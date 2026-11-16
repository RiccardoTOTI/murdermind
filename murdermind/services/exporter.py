"""Dossier builder and multi-format exporter (Markdown, JSON, PDF, ZIP) with strict Master/Player separation."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Dict

from fpdf import FPDF

from murdermind.schemas.mystery import CharacterProfile, MysteryProject


def _pdf_safe_text(text: str) -> str:
    """Normalize Unicode typography into Latin-1-compatible characters for core PDF fonts."""
    replacements = {
        "«": '"',
        "»": '"',
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "—": " - ",
        "–": "-",
        "…": "...",
        "•": "*",
        "→": "->",
    }
    out = text
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out.encode("latin-1", errors="replace").decode("latin-1")


class DossierExporter:
    """Produces the canonical `murder_mystery/` dossier structure and exports MD, JSON, PDF, and ZIP."""

    @staticmethod
    def render_character_sheet_md(
        project: MysteryProject, char: CharacterProfile
    ) -> str:
        """Render an individual player character sheet WITHOUT leaking Master-only secrets or other players' secrets."""
        role_badge = "Personaggio Giocante" if char.is_playable else "Personaggio Non Giocante (PNG)"
        private_role_note = (
            "🔴 **NOTA SEGRETA PERSONALE: SEI TU L'AUTORE DEL DELITTO.** "
            "Il tuo obiettivo principale è non farti smascherare, difendere il tuo alibi e deviare i sospetti sugli altri invitati."
            if char.is_culprit
            else "🟢 **NOTA SEGRETA PERSONALE: SEI INNOCENTE DELL'OMICIDIO.** "
            "Tuttavia nascondi un segreto compromettente: proteggi la tua reputazione mentre cerchi di scoprire il vero assassino."
        )

        rels_md = "\n".join(
            f"- **{r.target_name}** (`{r.target_character_id}`) — *{r.relation_type}*\n"
            f"  - *Come vi mostrate in pubblico*: {r.public_view}\n"
            f"  - *La tua tensione privata verso di lui/lei*: {r.hidden_tension}"
            for r in char.relationships
        ) or "- Nessun legame diretto registrato."

        goals_md = "\n".join(f"- {g}" for g in char.goals)
        known_md = "\n".join(f"- {k}" for k in char.known_facts)
        hidden_md = "\n".join(f"- {h}" for h in char.hidden_facts)
        dialogues = project.narrative.character_dialogues.get(char.character_id, [])
        dialogues_md = "\n".join(f"- {d}" for d in dialogues) or "- Improvvisa seguendo la tua personalità."
        conf_msg = project.narrative.confidential_communications.get(char.character_id, "")

        return (
            f"# Scheda Personaggio: {char.name} (`{char.character_id}`)\n\n"
            f"**Mistero**: {project.concept.title}  \n"
            f"**Ruolo**: {char.role} ({role_badge})\n\n"
            f"> **SCHEDA INDIVIDUALE RISERVATA AL GIOCATORE — NON MOSTRARE AGLI ALTRI PARTECIPANTI**\n\n"
            f"{private_role_note}\n\n"
            f"## 1. Identità, Passato e Personalità\n"
            f"- **Background**: {char.background}\n"
            f"- **Personalità e stile**: {char.personality}\n\n"
            f"## 2. Obiettivi Individuali della Serata\n{goals_md}\n\n"
            f"## 3. Il Tuo Alibi, Movente e Segreto Personale\n"
            f"- **Il tuo Alibi dichiarato**: {char.alibi}\n"
            f"- **Il tuo Segreto da proteggere**: {char.secret}\n"
            f"- **Perché avevi un contrasto con {project.concept.victim_name}**: {char.motive}\n\n"
            f"## 4. Relazioni con gli Altri Presenti\n{rels_md}\n\n"
            f"## 5. Cosa Sai fin dall'Inizio (Informazioni Conosciute)\n{known_md}\n\n"
            f"## 6. Informazioni Nascoste (Da rivelare solo se messo alle strette)\n{hidden_md}\n"
            f"- **Criterio di rivelazione**: {char.what_can_reveal}\n"
            f"- **Come reagire se vieni accusato**: {char.reaction_to_accusation}\n\n"
            f"## 7. Battute Suggerite e Comunicazione di Metà Serata\n"
            f"### Frasi consigliate\n{dialogues_md}\n\n"
            f"### Busta Riservata di Metà Partita\n{conf_msg}\n"
        )

    @classmethod
    def build_dossier_files(cls, project: MysteryProject) -> Dict[str, str]:
        """Generate the complete `murder_mystery/` virtual filesystem dictionary."""
        files: Dict[str, str] = {}
        root = "murder_mystery"

        # 1. project.json & concept.md
        files[f"{root}/project.json"] = project.model_dump_json(indent=2)
        pillars_md = "\n".join(f"- {p}" for p in project.concept.design_pillars)
        files[f"{root}/concept.md"] = (
            f"# {project.concept.title}\n\n"
            f"**Tagline**: *{project.concept.tagline}*\n\n"
            f"## Premessa (Hook)\n{project.concept.hook}\n\n"
            f"## Vittima\n**{project.concept.victim_name}** — {project.concept.victim_role}\n\n"
            f"## Sintesi del Delitto\n{project.concept.crime_summary}\n\n"
            f"## Direttiva Atmosferica\n{project.concept.atmosphere_directive}\n\n"
            f"## Pilastri Progettuali\n{pillars_md}\n"
        )

        # 2. world/
        locs_md = "\n\n".join(
            f"### {loc.location_id} — {loc.name}\n- **Descrizione**: {loc.description}\n- **Dettaglio Nascosto**: {loc.hidden_detail}"
            for loc in project.world.locations
        )
        elems_md = "\n".join(f"- {e}" for e in project.world.characteristic_elements)
        files[f"{root}/world/setting.md"] = (
            f"# Ambientazione — {project.world.era_and_place}\n\n"
            f"## Contesto Sociale e Culturale\n{project.world.social_cultural_context}\n\n"
            f"## Atmosfera\n{project.world.atmosphere}\n\n"
            f"## Elementi Caratterizzanti\n{elems_md}\n\n"
            f"## Mappa dei Luoghi\n{locs_md}\n"
        )
        w_secrets_md = "\n".join(f"- {s}" for s in project.world.world_secrets)
        p_facts_md = "\n".join(f"- {f}" for f in project.world.public_facts)
        files[f"{root}/world/background.md"] = (
            f"# Antefatti e Segreti del Mondo\n\n"
            f"## Antefatto della Serata\n{project.world.backstory}\n\n"
            f"## Fatti di Dominio Pubblico\n{p_facts_md}\n\n"
            f"## Segreti del Luogo (Riservato al Master)\n{w_secrets_md}\n"
        )

        # 3. plot/
        sol = project.plot.secret_solution
        herrings_md = "\n".join(f"- {r}" for r in project.plot.red_herrings)
        alt_md = "\n".join(f"- {a}" for a in project.plot.alternative_developments)
        files[f"{root}/plot/main_plot.md"] = (
            f"# Trama Principale — {project.concept.title}\n\n"
            f"## Panoramica del Delitto\n{project.plot.crime_overview}\n\n"
            f"## Depistaggi (Red Herrings)\n{herrings_md}\n\n"
            f"## Sviluppi Alternativi\n{alt_md}\n"
        )
        files[f"{root}/plot/timeline.json"] = json.dumps(
            [e.model_dump() for e in project.plot.timeline],
            indent=2,
            ensure_ascii=False,
        )
        files[f"{root}/plot/secret_solution.md"] = (
            project.final_production.secret_resolution_md
            or (
                f"# SOLUZIONE SEGRETA DEL MASTER\n\n"
                f"- **Vittima**: {sol.victim_name}\n"
                f"- **Colpevole**: {sol.culprit_name} (`{sol.culprit_id}`)\n"
                f"- **Movente**: {sol.motive}\n"
                f"- **Arma**: {sol.murder_weapon}\n"
                f"- **Luogo**: {sol.murder_location} ({sol.time_of_death})\n"
                f"- **Falla nell'alibi**: {sol.alibi_flaw}\n"
            )
        )

        # 4. characters/ (strictly player-safe sheets!)
        for idx, char in enumerate(project.characters, start=1):
            files[f"{root}/characters/character_{idx:02d}.md"] = cls.render_character_sheet_md(
                project, char
            )

        # 5. subplots/
        for idx, sub in enumerate(project.subplots, start=1):
            files[f"{root}/subplots/subplot_{idx:02d}.md"] = (
                f"# Sottotrama {sub.subplot_id}: {sub.title}\n\n"
                f"- **Categoria**: {sub.category}\n"
                f"- **Personaggi coinvolti**: {', '.join(sub.involved_character_ids)}\n\n"
                f"## Descrizione\n{sub.description}\n\n"
                f"## Innesco in Gioco\n{sub.player_triggers}\n\n"
                f"## Risoluzione\n{sub.resolution}\n\n"
                f"## Legame con la Trama Principale\n{sub.connects_to_main_plot}\n"
            )

        # 6. clues/
        files[f"{root}/clues/clues.json"] = json.dumps(
            [c.model_dump() for c in project.clues],
            indent=2,
            ensure_ascii=False,
        )
        for clue in project.clues:
            # Player-facing printable clue card (no Master spoiler of is_red_herring or logical_inference!)
            files[f"{root}/clues/printable_clues/{clue.clue_id}.md"] = (
                f"# Cartellino Indizio `{clue.clue_id}` — {clue.title}\n\n"
                f"- **Tipologia**: {clue.clue_type.upper()}\n"
                f"- **Fase di Rivelazione**: Fase {clue.discovery_phase}\n"
                f"- **Luogo / Provenienza**: {clue.location_or_holder}\n\n"
                f"---\n\n"
                f"{clue.printable_text}\n\n"
                f"---\n"
                f"*{clue.description}*\n"
            )

        # 7. gameplay/
        files[f"{root}/gameplay/master_manual.md"] = project.final_production.master_manual_md
        files[f"{root}/gameplay/player_instructions.md"] = (
            project.final_production.player_instructions_md
        )
        phases_detail_md = "\n\n".join(
            f"## Fase {p.phase_number}: {p.title} ({p.duration_minutes} min)\n"
            f"- **Obiettivi**: {', '.join(p.objectives)}\n"
            f"- **Indizi Rivelati**: {', '.join(p.revealed_clue_ids)}\n"
            f"- **Eventi**: {', '.join(p.scheduled_events)}\n"
            f"- **Meccanica di Interrogatorio**: {p.interrogation_mechanics}"
            for p in project.gameplay.phases
        )
        files[f"{root}/gameplay/game_phases.md"] = (
            f"# Struttura delle Fasi di Gioco — {project.concept.title}\n\n"
            f"{phases_detail_md}\n\n"
            f"## Gestione delle Accuse\n{project.gameplay.accusation_mechanics}\n\n"
            f"## Condizioni di Vittoria\n{project.gameplay.victory_conditions}\n"
        )

        # 8. documents/ (letters, messages, evidence)
        folder_map = {
            "letter": "letters",
            "message": "messages",
            "evidence": "evidence",
        }
        for doc in project.narrative.documents:
            subfolder = folder_map.get(doc.doc_type, "evidence")
            files[f"{root}/documents/{subfolder}/{doc.doc_id}.md"] = (
                f"# {doc.title} (`{doc.doc_id}`)\n\n"
                f"- **Da**: {doc.sender}\n"
                f"- **A**: {doc.recipient}\n"
                f"- **Indizio collegato**: {doc.related_clue_id or 'N/A'}\n\n"
                f"---\n\n"
                f"{doc.content}\n"
            )

        # 9. final/
        files[f"{root}/final/complete_story.md"] = project.final_production.complete_story_md
        files[f"{root}/final/master_report.md"] = project.final_production.master_report_md
        files[f"{root}/final/resolution.md"] = project.final_production.secret_resolution_md

        return files

    @classmethod
    def write_dossier_directory(cls, project: MysteryProject, base_dir: str | Path) -> Path:
        """Write the complete `murder_mystery/` folder tree to disk under `base_dir`."""
        target_root = Path(base_dir)
        files = cls.build_dossier_files(project)
        for rel_path, content in files.items():
            full_path = target_root / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
        return target_root / "murder_mystery"

    @classmethod
    def export_pdf(cls, project: MysteryProject, output_path: str | Path) -> Path:
        """Generate a printable PDF containing Player Instructions, Character Sheets, Printable Clues, and Master Manual."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        def add_section(heading: str, body: str) -> None:
            pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 15)
            pdf.multi_cell(0, 9, _pdf_safe_text(heading), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
            pdf.set_font("Helvetica", "", 10)
            for line in body.splitlines():
                clean = _pdf_safe_text(line)
                pdf.set_x(pdf.l_margin)
                if clean.startswith("#"):
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.multi_cell(
                        0, 7, clean.lstrip("# ").strip() or " ", new_x="LMARGIN", new_y="NEXT"
                    )
                    pdf.set_font("Helvetica", "", 10)
                else:
                    pdf.multi_cell(
                        0, 5.5, clean if clean.strip() else " ", new_x="LMARGIN", new_y="NEXT"
                    )

        # Section 1: Cover & Player Rules
        add_section(
            f"DOSSIER GIOCATORI - {project.concept.title}",
            project.final_production.player_instructions_md or project.concept.hook,
        )

        # Section 2: Individual Character Sheets (each on its own page so it can be printed and handed out!)
        for char in project.characters:
            sheet_md = cls.render_character_sheet_md(project, char)
            add_section(f"SCHEDA PERSONAGGIO: {char.name} ({char.character_id})", sheet_md)

        # Section 3: Printable Clues & In-Game Documents
        clues_text = "\n\n".join(
            f"### {c.clue_id} - {c.title} (Fase {c.discovery_phase})\n"
            f"Luogo: {c.location_or_holder}\n"
            f"{c.printable_text}"
            for c in project.clues
        )
        add_section("CARTELLINI INDIZI STAMPABILI", clues_text)

        # Section 4: Master Manual & Secret Resolution (clearly marked at end of PDF)
        add_section(
            "MANUALE RISERVATO AL MASTER",
            (project.final_production.master_manual_md or "")
            + "\n\n"
            + (project.final_production.secret_resolution_md or ""),
        )

        pdf.output(str(out))
        return out

    @classmethod
    def export_zip(cls, project: MysteryProject, output_path: str | Path) -> Path:
        """Create a complete ZIP archive containing the `murder_mystery/` folder tree and the printable PDF."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        files = cls.build_dossier_files(project)

        pdf_temp = out.with_suffix(".printable.pdf")
        cls.export_pdf(project, pdf_temp)

        with zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for rel_path, content in files.items():
                zf.writestr(rel_path, content.encode("utf-8"))
            zf.write(pdf_temp, arcname="murder_mystery/final/printable_dossier.pdf")

        if pdf_temp.exists():
            pdf_temp.unlink()

        return out
