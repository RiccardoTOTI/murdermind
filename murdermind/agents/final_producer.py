"""AGENT 10 — Final Game Producer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from murdermind.agents.base import BaseNarrativeAgent, ensure_str_list
from murdermind.prompts.system_prompts import FINAL_PRODUCER_PROMPT
from murdermind.schemas.mystery import AgentCritique, FinalProductionSuite, MysteryProject


class ProducerLLMOutput(BaseModel):
    executive_summary: str = Field(default="")
    dramatic_reveal_speech: str = Field(default="")
    master_hosting_checklist: List[str] = Field(default_factory=list)
    post_game_debrief: str = Field(default="")


class FinalGameProducerAgent(BaseNarrativeAgent):
    """Compiles the complete, ready-to-play Master Manual, Player Instructions, Secret Resolution, and Master Report."""

    name = "FinalGameProducer"
    role_title = "AGENT 10 – Final Game Producer"
    phase_name = "Fase 10 – Finalization"
    system_prompt = FINAL_PRODUCER_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        cfg = project.config
        concept = project.concept
        sol = project.plot.secret_solution
        world = project.world

        user_prompt = (
            f"Lingua: {cfg.language}\n"
            f"Mistero: {concept.title} — {concept.tagline}\n"
            f"Vittima: {sol.victim_name} ({concept.victim_role})\n"
            f"Colpevole: {sol.culprit_id} ({sol.culprit_name})\n"
            f"Arma: {sol.murder_weapon} | Luogo: {sol.murder_location} | Orario: {sol.time_of_death}\n"
            f"Movente: {sol.motive}\n"
            f"Falla nell'alibi: {sol.alibi_flaw}\n"
            "Genera executive_summary, dramatic_reveal_speech, master_hosting_checklist e post_game_debrief in JSON."
        )

        def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "executive_summary": str(
                    raw.get("executive_summary")
                    or (
                        f"'{concept.title}' è una cena con delitto di complessità {cfg.complexity.lower()} "
                        f"della durata di {cfg.duration_minutes} minuti ambientata in {world.era_and_place or cfg.effective_setting}."
                    )
                ),
                "dramatic_reveal_speech": str(
                    raw.get("dramatic_reveal_speech")
                    or (
                        f"«È giunto il momento della verità. Molti di voi avevano un motivo per temere {sol.victim_name}, "
                        f"ma solo una persona è entrata in {sol.murder_location} tra le {sol.time_of_death} usando {sol.murder_weapon}. "
                        f"La contraddizione decisiva nell'alibi ({sol.alibi_flaw}) smaschera senza appello **{sol.culprit_name}** ({sol.culprit_id}), "
                        f"spinto da un movente inconfessabile: {sol.motive}!»"
                    )
                ),
                "master_hosting_checklist": ensure_str_list(
                    raw.get("master_hosting_checklist"),
                    [
                        "Stampare e imbustare separatamente le schede personaggio individuali (senza la soluzione segreta).",
                        "Preparare le 3 buste degli indizi divise per Fase 1, Fase 2 e Fase 3.",
                        "Consegnare i documenti stampabili e i messaggi riservati nei momenti previsti dal manuale.",
                        "Distribuire le schede di accusa finale 10 minuti prima della conclusione.",
                    ],
                ),
                "post_game_debrief": str(
                    raw.get("post_game_debrief")
                    or (
                        "Anche gli innocenti custodivano segreti scottanti che hanno alimentato i depistaggi della serata, "
                        "ma la catena logica degli indizi converge univocamente sul vero colpevole."
                    )
                ),
            }

        prod_out = self.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema_cls=ProducerLLMOutput,
            temperature=0.5,
            max_tokens=900,
            normalizer=normalize,
        )

        # Assemble canonical Master Manual, Player Instructions, Secret Resolution, Master Report, and Complete Story
        timeline_md = "\n".join(
            f"- **{e.timestamp}** (`{e.event_id}`) — **{e.title}** [{e.location}]: {e.description} "
            f"*(Coinvolti: {', '.join(e.involved_character_ids)})*"
            for e in project.plot.timeline
        )
        phases_md = "\n\n".join(
            f"### Fase {p.phase_number}: {p.title} ({p.duration_minutes} min)\n"
            f"- **Obiettivi**: {'; '.join(p.objectives)}\n"
            f"- **Indizi da rivelare**: {', '.join(p.revealed_clue_ids)}\n"
            f"- **Eventi programmati**: {'; '.join(p.scheduled_events)}\n"
            f"- **Meccanica di interrogatorio**: {p.interrogation_mechanics}"
            for p in project.gameplay.phases
        )
        checklist_md = "\n".join(f"- [ ] {item}" for item in prod_out.master_hosting_checklist)

        master_manual_md = (
            f"# Manuale del Master — {concept.title}\n\n"
            f"> **DOCUMENTO RISERVATO AL MASTER — NON MOSTRARE AI GIOCATORI**\n\n"
            f"## 1. Sintesi Esecutiva\n{prod_out.executive_summary}\n\n"
            f"- **Ambientazione**: {world.era_and_place or cfg.effective_setting}\n"
            f"- **Durata**: {cfg.duration_minutes} minuti | **Complessità**: {cfg.complexity}\n"
            f"- **Modalità Master**: {cfg.master_mode} | **Modalità di Gioco**: {cfg.gameplay_mode}\n\n"
            f"## 2. Checklist di Preparazione\n{checklist_md}\n\n"
            f"## 3. Regia delle Fasi di Gioco\n{phases_md}\n\n"
            f"## 4. Note di Facilitazione del Master\n{project.gameplay.master_notes}\n\n"
            f"## 5. Cronologia Canonica degli Eventi\n{timeline_md}\n"
        )

        public_roster_md = "\n".join(
            f"- **{c.name}** (`{c.character_id}`) — *{c.role}* ({'Personaggio Giocante' if c.is_playable else 'PNG'})"
            for c in project.characters
        )

        player_instructions_md = (
            f"# Regole e Istruzioni per i Giocatori — {concept.title}\n\n"
            f"*{concept.tagline}*\n\n"
            f"## 1. Benvenuti alla Cena con Delitto\n{project.narrative.introduction_md or concept.hook}\n\n"
            f"## 2. I Sospettati Presenti\n{public_roster_md}\n\n"
            f"## 3. Come Giocare\n"
            f"1. **Interpreta il tuo ruolo**: leggi attentamente la tua scheda personaggio individuale. Non mostrare mai la tua scheda agli altri giocatori.\n"
            f"2. **Proteggi il tuo segreto**: anche se sei innocente dell'omicidio, hai qualcosa da nascondere! Svela informazioni solo quando strategicamente utile o se messo alle strette.\n"
            f"3. **Se sei il Colpevole**: puoi mentire sull'omicidio, ma devi attenerti ai fatti pubblici e difendere il tuo alibi.\n"
            f"4. **Se sei Innocente**: non mentire sui fatti oggettivi che hai osservato, ma puoi omettere i tuoi segreti personali finché non vieni incalzato.\n\n"
            f"## 4. Distribuzione delle Informazioni e Accusa Finale\n"
            f"{project.gameplay.information_distribution_rules}\n\n"
            f"### Come formulare l'Accusa\n{project.gameplay.accusation_mechanics}\n\n"
            f"### Condizioni di Vittoria\n{project.gameplay.victory_conditions}\n"
        )

        deduction_md = "\n".join(
            f"{idx}. {step}" for idx, step in enumerate(sol.deduction_chain, start=1)
        )
        clues_solution_md = "\n".join(
            f"- **{cl.clue_id} — {cl.title}** ({'DEPISTAGGIO' if cl.is_red_herring else 'PROVA REALE'}): "
            f"{cl.logical_inference} *(Punta a: {cl.points_to_character_id or 'N/A'})*"
            for cl in project.clues
        )

        secret_resolution_md = (
            f"# SOLUZIONE SEGRETA DEL MASTER — {concept.title}\n\n"
            f"> **SPOILER TOTALE — RISERVATO ESCLUSIVAMENTE AL MASTER E ALLA RIVELAZIONE FINALE**\n\n"
            f"## Identità dell'Assassino\n"
            f"- **Vittima**: {sol.victim_name} ({concept.victim_role})\n"
            f"- **Colpevole Canonico**: **{sol.culprit_name}** (`{sol.culprit_id}`)\n"
            f"- **Arma / Metodo**: {sol.murder_weapon}\n"
            f"- **Luogo del Delitto**: {sol.murder_location}\n"
            f"- **Fascia Oraria della Morte**: {sol.time_of_death}\n"
            f"- **Movente**: {sol.motive}\n"
            f"- **Dinamica e Opportunità**: {sol.opportunity_and_dynamics}\n"
            f"- **La Falla nell'Alibi**: {sol.alibi_flaw}\n\n"
            f"## Catena Deduttiva Canonica\n{deduction_md}\n\n"
            f"## Mappa Logica degli Indizi\n{clues_solution_md}\n\n"
            f"## Discorso Finale di Rivelazione (Da leggere a fine serata)\n"
            f"{prod_out.dramatic_reveal_speech}\n\n"
            f"## Debriefing delle Sottotrame\n{prod_out.post_game_debrief}\n"
        )

        subplots_md = "\n\n".join(
            f"### {s.subplot_id}: {s.title} ({s.category})\n"
            f"- **Personaggi coinvolti**: {', '.join(s.involved_character_ids)}\n"
            f"- **Descrizione**: {s.description}\n"
            f"- **Attivazione in gioco**: {s.player_triggers}\n"
            f"- **Risoluzione**: {s.resolution}"
            for s in project.subplots
        ) or "Nessuna sottotrama secondaria configurata."

        reviews_md = "\n".join(
            f"- **Iterazione #{r.iteration}**: Punteggio `{r.coherence_score}/100` — {r.summary}"
            for r in project.reviews
        )

        master_report_md = (
            f"# Resoconto Architetturale e Grafo Narrativo (Master Report) — {concept.title}\n\n"
            f"## 1. Stato di Coerenza e Revisione Multi-Agente\n{reviews_md}\n\n"
            f"## 2. Matrice Segreti & Alibi dei Personaggi\n"
            + "\n".join(
                f"- **{c.character_id} — {c.name}** ({'COLPEVOLE' if c.is_culprit else 'Innocente'}):\n"
                f"  - *Movente*: {c.motive}\n"
                f"  - *Alibi*: {c.alibi}\n"
                f"  - *Segreto*: {c.secret}"
                for c in project.characters
            )
            + f"\n\n## 3. Sottotrame e Risoluzioni\n{subplots_md}\n"
        )

        complete_story_md = (
            f"# Dossier Narrativo Completo — {concept.title}\n\n"
            f"*{concept.tagline}*\n\n"
            f"## 1. Concept e Premessa\n{concept.hook}\n\n"
            f"## 2. Il Mondo e l'Ambientazione\n"
            f"**Luogo ed Epoca**: {world.era_and_place}\n\n"
            f"**Contesto**: {world.social_cultural_context}\n\n"
            f"**Atmosfera**: {world.atmosphere}\n\n"
            f"**Antefatti**: {world.backstory}\n\n"
            f"## 3. Prologo Drammatico\n{project.narrative.prologue_speech_md}\n\n"
            f"## 4. Cronologia Completa\n{timeline_md}\n\n"
            f"## 5. Epilogo e Rivelazione\n{prod_out.dramatic_reveal_speech}\n"
        )

        project.final_production = FinalProductionSuite(
            master_manual_md=master_manual_md,
            player_instructions_md=player_instructions_md,
            secret_resolution_md=secret_resolution_md,
            master_report_md=master_report_md,
            complete_story_md=complete_story_md,
        )
        project.status = "completed"
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action="finalize_production_suite",
            summary="Suite finale prodotta: Manuale Master, Regole Giocatori, Soluzione Riservata, Master Report e Storia Completa.",
            status="completed",
        )
        return project
