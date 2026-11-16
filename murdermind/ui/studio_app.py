"""Gradio 3-Area Web Application for MurderMind — Murder Mystery Multi-Agent Studio."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import gradio as gr

from murdermind.config import AppSettings, LLMConfig, ProviderMode
from murdermind.core.graph_validator import InformationGraphValidator
from murdermind.core.llm_client import OpenAICompatibleClient
from murdermind.core.orchestrator import MurderMysteryOrchestrator
from murdermind.schemas.mystery import (
    COMPLEXITY_LEVELS,
    GAMEPLAY_MODES,
    MASTER_MODES,
    NARRATIVE_TONES,
    SETTING_PRESETS,
    SUBPLOT_COUNTS,
    AgentCritique,
    MysteryProject,
    StoryConfig,
)
from murdermind.services.demo_preset import build_demo_mystery_project
from murdermind.services.exporter import DossierExporter
from murdermind.services.storage import ProjectStorage


AGENT_ROSTER = [
    ("GameDirector", "AGENT 1 – Game Director", "Fase 1 – Concept"),
    ("WorldBuilder", "AGENT 2 – World Builder", "Fase 2 – World Building"),
    ("PlotArchitect", "AGENT 3 – Plot Architect", "Fase 3 – Plot Design"),
    ("CharacterDesigner", "AGENT 4 – Character Designer", "Fase 4 – Character Design"),
    ("SubplotDesigner", "AGENT 5 – Subplot Designer", "Fase 5 – Subplot Design"),
    ("ClueMaster", "AGENT 6 – Clue Master", "Fase 6 – Clue Design"),
    ("GameMechanicsDesigner", "AGENT 7 – Game Mechanics Designer", "Fase 7 – Game Design"),
    ("NarrativeWriter", "AGENT 8 – Narrative Writer", "Fase 8 – Narrative Production"),
    ("ContinuityEditor", "AGENT 9 – Continuity Editor", "Fase 9 – Critical Review"),
    ("FinalGameProducer", "AGENT 10 – Final Game Producer", "Fase 10 – Finalization"),
]


def render_agent_board_md(project: MysteryProject) -> str:
    """Render a Markdown table showing the real-time status of all 10 specialized agents."""
    latest_by_agent: Dict[str, Any] = {}
    for entry in project.agent_logs:
        latest_by_agent[entry.agent_name] = entry

    rows = [
        "### Stato Workflow dei 10 Agenti Collaborativi",
        "| Agente | Fase | Stato | Ultima Attività Registrata |",
        "| :--- | :--- | :---: | :--- |",
    ]
    badge_map = {
        "completed": "🟢 Completato",
        "revised": "🔵 Revisionato",
        "critique": "🟠 Revisione Richiesta",
        "running": "🟡 In Esecuzione",
        "error": "🔴 Errore",
    }
    for key, label, phase in AGENT_ROSTER:
        log = latest_by_agent.get(key)
        if log:
            badge = badge_map.get(log.status, "🟢 Attivo")
            summary = log.summary.replace("|", "/")
        else:
            badge = "⚪ In attesa"
            summary = "—"
        rows.append(f"| **{label}** | {phase} | {badge} | {summary} |")

    return "\n".join(rows)


def render_activity_log_md(project: MysteryProject) -> str:
    """Render the chronological log of agent actions, proposals, critiques, and revisions."""
    if not project.agent_logs:
        return "*Nessuna attività registrata.*"
    lines = ["### Cronologia Osservabile delle Attività Multi-Agente"]
    for log in reversed(project.agent_logs):
        icon = {
            "completed": "✅",
            "revised": "🔄",
            "critique": "🔍",
            "running": "⏳",
            "error": "❌",
        }.get(log.status, "📌")
        lines.append(
            f"- **{icon} Step #{log.step_index} [{log.phase}] — `{log.agent_name}`** "
            f"*({log.action})*: {log.summary}"
        )
    return "\n".join(lines)


def render_reviews_md(project: MysteryProject) -> str:
    """Render the Continuity Editor reports and Information Graph validation status."""
    graph_issues = InformationGraphValidator.validate_full_graph(project)
    lines = ["### Report Continuity Editor & Validazione Grafo Narrativo"]

    if project.reviews:
        for rev in project.reviews:
            status_badge = "✅ APPROVATO" if rev.passed else "⚠️ RICHIESTA REVISIONE"
            lines.append(
                f"#### Iterazione #{rev.iteration}: {status_badge} — Coerenza `{rev.coherence_score}/100`\n"
                f"{rev.summary}"
            )
            if rev.critiques:
                for c in rev.critiques:
                    res = "✔️ Risolto" if c.resolved else "❗ Aperto"
                    lines.append(
                        f"- **[{c.severity.upper()}] → `{c.target_agent}`** ({c.issue_type}) [{res}]: "
                        f"{c.description} *(Fix: {c.suggested_fix})*"
                    )
            else:
                lines.append("- *Nessuna contraddizione rilevata.*")
    else:
        lines.append("*Nessun ciclo di revisione ancora eseguito.*")

    lines.append("\n---")
    if not graph_issues:
        lines.append(
            "🟢 **Validatore Automatico del Grafo d'Informazione**: "
            "Tutte le verifiche di consistenza (ID canonici, alibi del colpevole, solvibilità degli indizi, sottotrame) sono superate."
        )
    else:
        lines.append(f"🟠 **Rilievi Strutturali Attuali ({len(graph_issues)})**:")
        for g in graph_issues:
            lines.append(f"- `{g.target_agent}` [{g.issue_type}]: {g.description}")

    return "\n".join(lines)


def render_clues_and_docs_md(project: MysteryProject) -> str:
    """Render player-facing printable clues and in-game documents (without Master spoilers)."""
    lines = [f"# Reperti e Documenti Investigativi — {project.concept.title}\n"]
    lines.append("## Cartellini Indizi (Per Fase di Gioco)")
    for clue in project.clues:
        lines.append(
            f"### `{clue.clue_id}` — {clue.title} *(Fase {clue.discovery_phase} | Tipo: {clue.clue_type})*\n"
            f"- **Luogo / Provenienza**: {clue.location_or_holder}\n"
            f"- **Testo Stampabile**:\n> {clue.printable_text}\n"
        )

    lines.append("\n---\n## Documenti In-Game (Lettere, Messaggi, Prove)")
    for doc in project.narrative.documents:
        lines.append(
            f"### `{doc.doc_id}` [{doc.doc_type.upper()}] — {doc.title}\n"
            f"- **Da**: {doc.sender} → **A**: {doc.recipient}\n\n"
            f"{doc.content}\n"
        )
    return "\n".join(lines)


def render_timeline_and_subplots_md(project: MysteryProject) -> str:
    """Render the canonical timeline and subplots for the Master view."""
    lines = [f"# Cronologia Canonica & Sottotrame — {project.concept.title}\n"]
    lines.append("## 1. Cronologia Canonica degli Eventi (`timeline.json`)")
    for evt in project.plot.timeline:
        crime_tag = " 🔴 **[EVENTO DEL DELITTO]**" if evt.is_crime_event else ""
        vis_tag = "Pubblico" if evt.is_public else "Segreto"
        lines.append(
            f"- **{evt.timestamp}** (`{evt.event_id}`) — **{evt.title}** [{evt.location}] ({vis_tag}){crime_tag}\n"
            f"  {evt.description} *(Personaggi: {', '.join(evt.involved_character_ids)})*"
        )

    lines.append("\n---\n## 2. Sottotrame (`subplots/`)")
    if not project.subplots:
        lines.append("*Nessuna sottotrama configurata.*")
    for sub in project.subplots:
        lines.append(
            f"### `{sub.subplot_id}` — {sub.title} ({sub.category})\n"
            f"- **Personaggi coinvolti**: {', '.join(sub.involved_character_ids)}\n"
            f"- **Intreccio**: {sub.description}\n"
            f"- **Innesco**: {sub.player_triggers}\n"
            f"- **Risoluzione**: {sub.resolution}\n"
            f"- **Legame con il delitto**: {sub.connects_to_main_plot}\n"
        )
    return "\n".join(lines)


def build_studio_ui(gpu_decorator: Any = None) -> gr.Blocks:
    """Construct the clean, streamlined 3-Area Gradio Blocks application for MurderMind Studio."""
    if gpu_decorator is None:
        def _identity_decorator(duration: Any = 60):
            def _wrap(fn: Any) -> Any:
                return fn
            return _wrap
        gpu_decorator = _identity_decorator

    settings = AppSettings()
    storage = ProjectStorage(db_path=settings.db_path)

    # Seed the database with the playable Demo Mystery so the Space/App is immediately rich on first open
    demo_project = build_demo_mystery_project()
    storage.save(demo_project)

    def get_project_choices() -> List[Tuple[str, str]]:
        records = storage.list_projects()
        return [
            (f"{r['title']} ({r['setting']})", r["project_id"])
            for r in records
        ]

    def get_char_choices(project: MysteryProject) -> List[Tuple[str, str]]:
        return [
            (
                f"{c.character_id} — {c.name} ({'Giocante' if c.is_playable else 'PNG'})",
                c.character_id,
            )
            for c in project.characters
        ]

    def pack_ui_outputs(
        project: MysteryProject, status_banner: str
    ) -> Tuple[Any, ...]:
        char_choices = get_char_choices(project)
        first_char_id = char_choices[0][1] if char_choices else None
        first_char_sheet = (
            DossierExporter.render_character_sheet_md(project, project.characters[0])
            if project.characters
            else "*Nessun personaggio ancora generato.*"
        )
        proj_choices = get_project_choices()

        return (
            project.model_dump(),
            status_banner,
            render_agent_board_md(project),
            render_activity_log_md(project),
            render_reviews_md(project),
            project.final_production.player_instructions_md or project.concept.hook,
            gr.update(choices=char_choices, value=first_char_id),
            first_char_sheet,
            render_clues_and_docs_md(project),
            project.final_production.master_manual_md,
            project.final_production.secret_resolution_md,
            render_timeline_and_subplots_md(project),
            project.final_production.master_report_md,
            project.concept.title,
            project.concept.hook,
            project.final_production.master_manual_md,
            gr.update(choices=proj_choices, value=project.project_id),
        )

    custom_css = """
    .gradio-container { max-width: 1180px !important; margin: 0 auto !important; }
    .studio-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 60%, #3b0764 100%);
        color: #f8fafc;
        padding: 18px 24px;
        border-radius: 14px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.18);
    }
    .studio-hero h1 { color: #ffffff !important; margin: 0 0 4px 0; font-size: 1.45rem; font-weight: 700; }
    .studio-hero p { color: #cbd5e1 !important; margin: 0; font-size: 0.92rem; }
    .studio-pill {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #e2e8f0;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 0.8rem;
        white-space: nowrap;
    }
    """

    with gr.Blocks(title="MurderMind — Murder Mystery Studio") as app:
        project_state = gr.State(value=demo_project.model_dump())

        gr.HTML(
            f"<style>{custom_css}</style>"
            """
            <div class="studio-hero">
                <div>
                    <h1>🕵️‍♀️ MurderMind Studio</h1>
                    <p>Motore Multi-Agente per Cene con Delitto coerenti, giocabili e pronte da stampare</p>
                </div>
                <div class="studio-pill">10 Agenti AI • Grafo Verificato</div>
            </div>
            """
        )

        status_md = gr.Markdown(
            value=f"🟢 **Caso attivo**: **{demo_project.concept.title}** — Esplora subito il **Dossier di Gioco** oppure configura e genera un nuovo mistero."
        )

        with gr.Tabs():
            # =========================================================================
            # TAB 1: STUDIO CREATIVO (CLEAN & STREAMLINED)
            # =========================================================================
            with gr.Tab("✨ 1. Crea la tua Cena con Delitto"):
                with gr.Row():
                    with gr.Column(scale=3):
                        title_hint_in = gr.Textbox(
                            label="Titolo o Idea di Partenza (opzionale)",
                            value="L'Ultimo Brindisi a Villa Morosini",
                            placeholder="Es. Delitto sull'Orient Express, Mistero a Corte...",
                        )
                        with gr.Row():
                            setting_in = gr.Dropdown(
                                label="Ambientazione",
                                choices=SETTING_PRESETS,
                                value="Villa nobiliare",
                            )
                            tone_in = gr.Dropdown(
                                label="Tono Narrativo",
                                choices=NARRATIVE_TONES,
                                value="Thriller",
                            )
                            num_pg_in = gr.Slider(
                                label="Giocatori ( Sospettati )",
                                minimum=3,
                                maximum=10,
                                step=1,
                                value=4,
                            )
                        constraints_in = gr.Textbox(
                            label="Richiesta Narrativa o Dettaglio Speciale (opzionale)",
                            lines=2,
                            value="Il colpevole usa un metodo ingegnoso e lascia una contraddizione oraria nel proprio alibi.",
                            placeholder="Es. La vittima è un famoso chef; l'arma è nascosta in cucina...",
                        )

                        with gr.Row():
                            btn_generate_full = gr.Button(
                                "🚀 Genera Cena con Delitto Completa (10 Agenti)",
                                variant="primary",
                                size="lg",
                            )
                            btn_generate_mvp = gr.Button(
                                "⚡ Bozza Veloce (3 Agenti MVP)",
                                variant="secondary",
                                size="lg",
                            )

                        with gr.Accordion("🎛️ Opzioni Avanzate di Gioco (Complessità, Durata, PNG, Sottotrame, Master)", open=False):
                            with gr.Row():
                                custom_setting_in = gr.Textbox(
                                    label="Dettaglio Luogo / Epoca Personalizzata",
                                    value="Villa storica sul Lago di Como durante un temporale",
                                )
                                num_npc_in = gr.Slider(
                                    label="Personaggi Non Giocanti (PNG)",
                                    minimum=0,
                                    maximum=4,
                                    step=1,
                                    value=1,
                                )
                            with gr.Row():
                                complexity_in = gr.Dropdown(
                                    label="Complessità",
                                    choices=COMPLEXITY_LEVELS,
                                    value="Intermedia",
                                )
                                duration_in = gr.Dropdown(
                                    label="Durata (minuti)",
                                    choices=[60, 90, 120, 180],
                                    value=90,
                                    allow_custom_value=True,
                                )
                                subplots_in = gr.Dropdown(
                                    label="Sottotrame",
                                    choices=SUBPLOT_COUNTS,
                                    value="Medie",
                                )
                            with gr.Row():
                                master_mode_in = gr.Dropdown(
                                    label="Presenza del Master",
                                    choices=MASTER_MODES,
                                    value="Con master",
                                )
                                gameplay_mode_in = gr.Dropdown(
                                    label="Modalità di Gioco",
                                    choices=GAMEPLAY_MODES,
                                    value="A fasi",
                                )
                                max_rev_in = gr.Slider(
                                    label="Cicli Revisione (Agent 9)",
                                    minimum=1,
                                    maximum=3,
                                    step=1,
                                    value=1,
                                )

                    with gr.Column(scale=1):
                        gr.Markdown("#### 📂 Archivio Casi Pronti")
                        saved_projects_dd = gr.Dropdown(
                            label="Casi Salvati",
                            choices=get_project_choices(),
                            value=demo_project.project_id,
                        )
                        btn_load_project = gr.Button("📂 Carica Caso Selezionato", size="sm")
                        btn_load_demo = gr.Button("🎭 Ricarica Demo 'Villa Morosini'", size="sm")

                        with gr.Accordion("⚙️ Motore AI (ZeroGPU / Locale :8888)", open=False):
                            provider_mode_in = gr.Dropdown(
                                label="Provider AI",
                                choices=["zerogpu", "local", "remote", "auto"],
                                value=settings.llm.provider.value,
                            )
                            llm_url_in = gr.Textbox(
                                label="Endpoint Locale/Remoto",
                                value=settings.llm.base_url,
                            )
                            llm_model_in = gr.Textbox(
                                label="Modello",
                                value=settings.llm.zerogpu_model
                                if settings.llm.provider == ProviderMode.ZEROGPU
                                else settings.llm.model,
                            )
                            llm_temp_in = gr.Slider(
                                label="Temperatura",
                                minimum=0.0,
                                maximum=1.2,
                                step=0.05,
                                value=settings.llm.temperature,
                            )
                            btn_check_llm = gr.Button("🔌 Test Connessione AI", size="sm")
                            llm_health_md = gr.Markdown(value="*Pronto.*")

                gr.Examples(
                    label="💡 Idee Pronte da Provare con un Click",
                    examples=[
                        [
                            "L'Ultimo Brindisi a Villa Morosini",
                            "Villa nobiliare",
                            "Thriller",
                            4,
                            "Delitto con veleno nel decanter dello studio privato durante un temporale.",
                        ],
                        [
                            "Ombre sull'Espresso di Mezzanotte",
                            "Treno",
                            "Noir",
                            4,
                            "Un passeggero viaggia sotto falsa identità; l'orologio spezzato segna l'ora del delitto.",
                        ],
                        [
                            "Congiura al Castello di Roccaforza",
                            "Castello medievale",
                            "Drammatico",
                            5,
                            "Un segreto dinastico e una pergamena sigillata con ceralacca.",
                        ],
                    ],
                    inputs=[
                        title_hint_in,
                        setting_in,
                        tone_in,
                        num_pg_in,
                        constraints_in,
                    ],
                )

            # =========================================================================
            # TAB 2: GAME DOSSIER (PLAYERS, MASTER & EXPORT)
            # =========================================================================
            with gr.Tab("📖 2. Dossier di Gioco & Download"):
                with gr.Tabs():
                    with gr.Tab("🎭 Schede Giocatori & Indizi (No Spoiler)"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                char_selector_dd = gr.Dropdown(
                                    label="👤 Seleziona il Personaggio da Visualizzare",
                                    choices=get_char_choices(demo_project),
                                    value="char_01",
                                )
                                char_sheet_md = gr.Markdown(
                                    value=DossierExporter.render_character_sheet_md(
                                        demo_project, demo_project.characters[0]
                                    )
                                )
                            with gr.Column(scale=1):
                                with gr.Accordion("📜 Regole Pubbliche e Introduzione per tutti i Giocatori", open=True):
                                    player_rules_md = gr.Markdown(
                                        value=demo_project.final_production.player_instructions_md
                                    )
                                with gr.Accordion("🔎 Cartellini Indizi & Documenti Stampabili", open=True):
                                    clues_docs_md = gr.Markdown(
                                        value=render_clues_and_docs_md(demo_project)
                                    )

                    with gr.Tab("🔐 Area Riservata al Master (Soluzione & Regia)"):
                        gr.Markdown(
                            "> ⚠️ **SOLO PER IL MASTER**: Contiene l'identità dell'assassino, la catena deduttiva e la cronologia segreta."
                        )
                        with gr.Row():
                            with gr.Column(scale=1):
                                secret_solution_view_md = gr.Markdown(
                                    value=demo_project.final_production.secret_resolution_md
                                )
                            with gr.Column(scale=1):
                                master_manual_view_md = gr.Markdown(
                                    value=demo_project.final_production.master_manual_md
                                )
                        with gr.Accordion("🕒 Cronologia Canonica, Sottotrame & Matrice Alibi", open=False):
                            timeline_subplots_md = gr.Markdown(
                                value=render_timeline_and_subplots_md(demo_project)
                            )
                            master_report_view_md = gr.Markdown(
                                value=demo_project.final_production.master_report_md
                            )

                    with gr.Tab("📥 Scarica Pacchetto Stampabile (PDF / ZIP) & Modifica"):
                        with gr.Row():
                            with gr.Column(scale=1):
                                gr.Markdown("#### 📦 Esporta il Dossier Completo")
                                btn_export_all = gr.Button(
                                    "📥 Genera File Scaricabili (ZIP + PDF + JSON + MD)",
                                    variant="primary",
                                )
                                export_zip_file = gr.File(label="Archivio Completo (murder_mystery.zip)")
                                export_pdf_file = gr.File(label="Dossier Stampabile (PDF)")
                                with gr.Row():
                                    export_json_file = gr.File(label="Grafo (project.json)")
                                    export_md_file = gr.File(label="Storia (complete_story.md)")
                            with gr.Column(scale=1):
                                gr.Markdown("#### ✏️ Ritocco Rapido dei Testi")
                                edit_title_in = gr.Textbox(
                                    label="Titolo",
                                    value=demo_project.concept.title,
                                )
                                edit_hook_in = gr.Textbox(
                                    label="Premessa Narrativa (Hook)",
                                    lines=3,
                                    value=demo_project.concept.hook,
                                )
                                edit_master_manual_in = gr.Textbox(
                                    label="Manuale del Master (Markdown)",
                                    lines=8,
                                    value=demo_project.final_production.master_manual_md,
                                )
                                btn_save_edits = gr.Button("💾 Salva Modifiche", variant="secondary")

            # =========================================================================
            # TAB 3: CONTROL ROOM (OBSERVABLE MULTI-AGENT WORKFLOW)
            # =========================================================================
            with gr.Tab("🛰️ 3. Control Room (I 10 Agenti & Revisioni)"):
                agent_board_md = gr.Markdown(value=render_agent_board_md(demo_project))
                with gr.Row():
                    with gr.Column(scale=1):
                        reviews_md = gr.Markdown(value=render_reviews_md(demo_project))
                    with gr.Column(scale=1):
                        activity_log_md = gr.Markdown(value=render_activity_log_md(demo_project))

                with gr.Accordion("🔄 Rigenera un Singolo Agente con Direttive Specifiche", open=False):
                    with gr.Row():
                        phase_select_dd = gr.Dropdown(
                            label="Agente / Fase",
                            choices=[
                                ("Fase 1 – Concept (Game Director)", 1),
                                ("Fase 2 – World Building (World Builder)", 2),
                                ("Fase 3 – Plot Design (Plot Architect)", 3),
                                ("Fase 4 – Character Design (Character Designer)", 4),
                                ("Fase 5 – Subplot Design (Subplot Designer)", 5),
                                ("Fase 6 – Clue Design (Clue Master)", 6),
                                ("Fase 7 – Game Design (Game Mechanics Designer)", 7),
                                ("Fase 8 – Narrative Production (Narrative Writer)", 8),
                                ("Fase 9 – Critical Review (Continuity Editor)", 9),
                                ("Fase 10 – Finalization (Final Game Producer)", 10),
                            ],
                            value=6,
                        )
                        phase_critique_in = gr.Textbox(
                            label="Istruzione di Revisione per l'Agente",
                            placeholder="Es. Aggiungi un indizio legato a una chiave trovata in giardino...",
                        )
                        btn_rerun_phase = gr.Button("♻️ Rigenera Fase", variant="secondary")

        # =========================================================================
        # EVENT HANDLERS
        # =========================================================================
        all_main_outputs = [
            project_state,
            status_md,
            agent_board_md,
            activity_log_md,
            reviews_md,
            player_rules_md,
            char_selector_dd,
            char_sheet_md,
            clues_docs_md,
            master_manual_view_md,
            secret_solution_view_md,
            timeline_subplots_md,
            master_report_view_md,
            edit_title_in,
            edit_hook_in,
            edit_master_manual_in,
            saved_projects_dd,
        ]

        def _make_client(
            provider_str: str, base_url: str, model_name: str, temp: float
        ) -> OpenAICompatibleClient:
            cfg = LLMConfig.from_env()
            try:
                cfg.provider = ProviderMode(provider_str)
            except ValueError:
                cfg.provider = ProviderMode.LOCAL
            if base_url.strip():
                cfg.base_url = base_url.strip().rstrip("/")
            if model_name.strip():
                if cfg.provider == ProviderMode.ZEROGPU:
                    cfg.zerogpu_model = model_name.strip()
                else:
                    cfg.model = model_name.strip()
            cfg.temperature = float(temp)
            return OpenAICompatibleClient(config=cfg)

        def on_check_llm(
            provider_str: str, base_url: str, model_name: str, temp: float
        ) -> str:
            """Check connectivity and authentication with the configured LLM endpoint."""
            client = _make_client(provider_str, base_url, model_name, temp)
            info = client.check_health()
            if info.get("ok"):
                return (
                    f"🟢 **Connessione riuscita!** Provider: `{info['provider']}` | "
                    f"Endpoint: `{info['base_url']}` | Modello: `{info['model']}` | "
                    f"Risposta test: `{info.get('reply', 'OK')}`"
                )
            return (
                f"🔴 **Connessione non riuscita** ({info.get('base_url')}): `{info.get('error')}`\n\n"
                "*Nota per Hugging Face Spaces*: `127.0.0.1:8888` è l'endpoint locale di sviluppo. "
                "Su HF Spaces imposta `REMOTE_LLM_API_KEY` / `HF_TOKEN` e seleziona `remote` o usa il Caso Demo precaricato."
            )

        btn_check_llm.click(
            fn=on_check_llm,
            inputs=[provider_mode_in, llm_url_in, llm_model_in, llm_temp_in],
            outputs=[llm_health_md],
        )

        def on_select_character(state_dict: Dict[str, Any], char_id: str) -> str:
            """Render the player-safe character sheet for the selected character ID."""
            project = MysteryProject.model_validate(state_dict)
            char = project.get_character(char_id)
            if not char and project.characters:
                char = project.characters[0]
            if not char:
                return "*Nessun personaggio disponibile.*"
            return DossierExporter.render_character_sheet_md(project, char)

        char_selector_dd.change(
            fn=on_select_character,
            inputs=[project_state, char_selector_dd],
            outputs=[char_sheet_md],
        )

        def on_load_project(selected_id: str) -> Tuple[Any, ...]:
            """Load a saved MysteryProject from SQLite storage."""
            loaded = storage.load(selected_id) if selected_id else None
            if not loaded:
                loaded = build_demo_mystery_project()
            return pack_ui_outputs(
                loaded,
                f"📂 **Progetto caricato**: *{loaded.concept.title}* (`{loaded.project_id}`)",
            )

        btn_load_project.click(
            fn=on_load_project,
            inputs=[saved_projects_dd],
            outputs=all_main_outputs,
        )

        def on_load_demo() -> Tuple[Any, ...]:
            """Restore and display the full playable Demo Murder Mystery case."""
            demo = build_demo_mystery_project()
            storage.save(demo)
            return pack_ui_outputs(
                demo,
                f"🎭 **Caso Dimostrativo Caricato**: *{demo.concept.title}* (`{demo.project_id}`)",
            )

        btn_load_demo.click(
            fn=on_load_demo,
            inputs=[],
            outputs=all_main_outputs,
        )

        @gpu_decorator(duration=120)
        def on_generate_full(
            title_hint: str,
            setting_preset: str,
            custom_setting: str,
            num_pg: int,
            num_npc: int,
            complexity: str,
            duration: int,
            master_mode: str,
            subplots_amount: str,
            tone: str,
            gameplay_mode: str,
            constraints: str,
            max_rev: int,
            provider_str: str,
            base_url: str,
            model_name: str,
            temp: float,
        ) -> Generator[Tuple[Any, ...], None, None]:
            """Run the complete 10-agent collaborative workflow with live streaming updates."""
            cfg = StoryConfig(
                title_hint=title_hint,
                setting_preset=setting_preset,
                custom_setting=custom_setting,
                num_playable_characters=int(num_pg),
                num_npcs=int(num_npc),
                complexity=complexity,
                duration_minutes=int(duration),
                master_mode=master_mode,
                subplots_amount=subplots_amount,
                narrative_tone=tone,
                gameplay_mode=gameplay_mode,
                custom_constraints=constraints,
                max_review_iterations=int(max_rev),
            )
            client = _make_client(provider_str, base_url, model_name, temp)
            orchestrator = MurderMysteryOrchestrator(llm_client=client)
            project = orchestrator.create_project(cfg)
            yield pack_ui_outputs(
                project,
                "⏳ **Avvio Workflow Multi-Agente (10 Agenti)**... Inizializzazione progetto.",
            )

            try:
                for phase_num in range(1, 9):
                    agent = orchestrator.phase_map[phase_num]
                    yield pack_ui_outputs(
                        project,
                        f"🟡 **In esecuzione**: `{agent.role_title}` ({agent.phase_name})...",
                    )
                    orchestrator.run_phase(project, phase_num)
                    storage.save(project)
                    yield pack_ui_outputs(
                        project,
                        f"✅ **Completata {agent.phase_name}** da `{agent.name}`.",
                    )

                # Phase 9 Iterative Review Loop
                for iteration in range(1, cfg.max_review_iterations + 1):
                    yield pack_ui_outputs(
                        project,
                        f"🔍 **Fase 9 – Critical Review (Iterazione #{iteration})**: Analisi di `ContinuityEditor`...",
                    )
                    orchestrator.continuity_editor.run(
                        project, mvp_only=False, iteration=iteration
                    )
                    InformationGraphValidator.synchronize_canonical_graph(project)
                    latest_review = project.reviews[-1]
                    storage.save(project)
                    yield pack_ui_outputs(
                        project,
                        f"📋 **Esito Revisione #{iteration}**: Coerenza `{latest_review.coherence_score}/100`.",
                    )
                    if latest_review.passed:
                        break
                    revised = orchestrator._apply_review_revisions(
                        project, latest_review.critiques
                    )
                    storage.save(project)
                    if not revised:
                        break

                # Phase 10 Finalization
                yield pack_ui_outputs(
                    project,
                    "🟡 **Fase 10 – Finalization**: `FinalGameProducer` sta assemblando il dossier completo...",
                )
                orchestrator.run_phase(project, 10)
                project.status = "completed"
                storage.save(project)
                yield pack_ui_outputs(
                    project,
                    f"🎉 **Cena con Delitto Completata!** *{project.concept.title}* (`{project.project_id}`) salvata e pronta all'esportazione.",
                )
            except Exception as exc:
                project.log_activity(
                    phase=project.current_phase,
                    agent_name="Orchestrator",
                    action="error",
                    summary=f"Errore durante la generazione: {exc}",
                    status="error",
                )
                yield pack_ui_outputs(
                    project,
                    f"🔴 **Errore durante la chiamata al modello LLM**: `{exc}` — Verifica che `127.0.0.1:8888` sia attivo o usa la Demo.",
                )

        btn_generate_full.click(
            fn=on_generate_full,
            inputs=[
                title_hint_in,
                setting_in,
                custom_setting_in,
                num_pg_in,
                num_npc_in,
                complexity_in,
                duration_in,
                master_mode_in,
                subplots_in,
                tone_in,
                gameplay_mode_in,
                constraints_in,
                max_rev_in,
                provider_mode_in,
                llm_url_in,
                llm_model_in,
                llm_temp_in,
            ],
            outputs=all_main_outputs,
        )

        @gpu_decorator(duration=45)
        def on_generate_mvp(
            title_hint: str,
            setting_preset: str,
            custom_setting: str,
            num_pg: int,
            num_npc: int,
            complexity: str,
            duration: int,
            master_mode: str,
            subplots_amount: str,
            tone: str,
            gameplay_mode: str,
            constraints: str,
            max_rev: int,
            provider_str: str,
            base_url: str,
            model_name: str,
            temp: float,
        ) -> Tuple[Any, ...]:
            """Run the fast 3-agent MVP workflow (GameDirector, PlotArchitect, CharacterDesigner) + Review."""
            cfg = StoryConfig(
                title_hint=title_hint,
                setting_preset=setting_preset,
                custom_setting=custom_setting,
                num_playable_characters=int(num_pg),
                num_npcs=int(num_npc),
                complexity=complexity,
                duration_minutes=int(duration),
                master_mode=master_mode,
                subplots_amount=subplots_amount,
                narrative_tone=tone,
                gameplay_mode=gameplay_mode,
                custom_constraints=constraints,
                max_review_iterations=int(max_rev),
            )
            client = _make_client(provider_str, base_url, model_name, temp)
            orchestrator = MurderMysteryOrchestrator(llm_client=client)
            project = orchestrator.create_project(cfg)
            try:
                orchestrator.run_mvp_pipeline(project)
                orchestrator.final_producer.run(project)
                storage.save(project)
                return pack_ui_outputs(
                    project,
                    f"⚡ **Nucleo MVP Generato e Revisionato!** *{project.concept.title}* (`{project.project_id}`).",
                )
            except Exception as exc:
                return pack_ui_outputs(
                    project,
                    f"🔴 **Errore durante la generazione MVP**: `{exc}`",
                )

        btn_generate_mvp.click(
            fn=on_generate_mvp,
            inputs=[
                title_hint_in,
                setting_in,
                custom_setting_in,
                num_pg_in,
                num_npc_in,
                complexity_in,
                duration_in,
                master_mode_in,
                subplots_in,
                tone_in,
                gameplay_mode_in,
                constraints_in,
                max_rev_in,
                provider_mode_in,
                llm_url_in,
                llm_model_in,
                llm_temp_in,
            ],
            outputs=all_main_outputs,
        )

        @gpu_decorator(duration=35)
        def on_rerun_single_phase(
            state_dict: Dict[str, Any],
            phase_num: int,
            custom_critique: str,
            provider_str: str,
            base_url: str,
            model_name: str,
            temp: float,
        ) -> Tuple[Any, ...]:
            """Regenerate a single selected phase with optional user critique notes."""
            project = MysteryProject.model_validate(state_dict)
            client = _make_client(provider_str, base_url, model_name, temp)
            orchestrator = MurderMysteryOrchestrator(llm_client=client)
            agent = orchestrator.phase_map[int(phase_num)]

            critiques = None
            if custom_critique and custom_critique.strip():
                critiques = [
                    AgentCritique(
                        target_agent=agent.name,
                        issue_type="user_revision_request",
                        severity="major",
                        description=custom_critique.strip(),
                        suggested_fix=custom_critique.strip(),
                    )
                ]

            try:
                orchestrator.run_phase(project, int(phase_num), critiques=critiques)
                if int(phase_num) != 10:
                    orchestrator.final_producer.run(project)
                storage.save(project)
                return pack_ui_outputs(
                    project,
                    f"♻️ **Fase {phase_num} ({agent.name}) rigenerata con successo!**",
                )
            except Exception as exc:
                return pack_ui_outputs(
                    project,
                    f"🔴 **Errore durante la rigenerazione della Fase {phase_num}**: `{exc}`",
                )

        btn_rerun_phase.click(
            fn=on_rerun_single_phase,
            inputs=[
                project_state,
                phase_select_dd,
                phase_critique_in,
                provider_mode_in,
                llm_url_in,
                llm_model_in,
                llm_temp_in,
            ],
            outputs=all_main_outputs,
        )

        def on_save_manual_edits(
            state_dict: Dict[str, Any],
            new_title: str,
            new_hook: str,
            new_master_manual: str,
        ) -> Tuple[Any, ...]:
            """Persist manual edits made in the Dossier Editor tab to SQLite."""
            project = MysteryProject.model_validate(state_dict)
            if new_title.strip():
                project.concept.title = new_title.strip()
            if new_hook.strip():
                project.concept.hook = new_hook.strip()
            if new_master_manual.strip():
                project.final_production.master_manual_md = new_master_manual.strip()
            project.log_activity(
                phase="Editing Manuale",
                agent_name="UserEditor",
                action="manual_edit",
                summary="Contenuti aggiornati manualmente dall'utente e salvati nel database.",
                status="revised",
            )
            storage.save(project)
            return pack_ui_outputs(
                project,
                f"💾 **Modifiche manuali salvate** per *{project.concept.title}* (`{project.project_id}`).",
            )

        btn_save_edits.click(
            fn=on_save_manual_edits,
            inputs=[project_state, edit_title_in, edit_hook_in, edit_master_manual_in],
            outputs=all_main_outputs,
        )

        def on_export_all(state_dict: Dict[str, Any]) -> Tuple[str, str, str, str]:
            """Export the active project into ZIP, PDF, JSON, and Markdown files for download."""
            project = MysteryProject.model_validate(state_dict)
            export_dir = Path(tempfile.mkdtemp(prefix=f"murdermind_{project.project_id}_"))

            zip_path = DossierExporter.export_zip(
                project, export_dir / f"{project.project_id}_murder_mystery.zip"
            )
            pdf_path = DossierExporter.export_pdf(
                project, export_dir / f"{project.project_id}_printable_dossier.pdf"
            )
            json_path = export_dir / f"{project.project_id}_project.json"
            json_path.write_text(project.model_dump_json(indent=2), encoding="utf-8")

            md_path = export_dir / f"{project.project_id}_complete_story.md"
            md_path.write_text(
                project.final_production.complete_story_md or project.concept.hook,
                encoding="utf-8",
            )
            return str(zip_path), str(pdf_path), str(json_path), str(md_path)

        btn_export_all.click(
            fn=on_export_all,
            inputs=[project_state],
            outputs=[export_zip_file, export_pdf_file, export_json_file, export_md_file],
        )

    return app
