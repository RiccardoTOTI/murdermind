"""AGENT 1 — Game Director / Concept Architect."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from murdermind.agents.base import BaseNarrativeAgent, ensure_str_list
from murdermind.prompts.system_prompts import GAME_DIRECTOR_PROMPT
from murdermind.schemas.mystery import AgentCritique, MysteryProject, StoryConcept


class GameDirectorAgent(BaseNarrativeAgent):
    """Coordinates initial story concept and creative direction."""

    name = "GameDirector"
    role_title = "AGENT 1 – Game Director / Orchestrator"
    phase_name = "Fase 1 – Concept"
    system_prompt = GAME_DIRECTOR_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        cfg = project.config
        revision_note = self.format_critique_feedback(critiques)

        user_prompt = (
            f"Lingua richiesta: {cfg.language}\n"
            f"Ambientazione: {cfg.effective_setting}\n"
            f"Personaggi giocanti: {cfg.num_playable_characters} | PNG: {cfg.num_npcs}\n"
            f"Complessità: {cfg.complexity} | Durata: {cfg.duration_minutes} minuti\n"
            f"Tono narrativo: {cfg.effective_tone}\n"
            f"Modalità di gioco: {cfg.gameplay_mode} | Master: {cfg.master_mode}\n"
            f"Titolo/Idea iniziale: {cfg.title_hint or 'Genera un titolo originale'}\n"
            f"Vincoli personalizzati: {cfg.custom_constraints or 'Nessun vincolo extra'}\n"
            f"{revision_note}\n"
            "Genera il concept iniziale della cena con delitto in formato JSON."
        )

        def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "title": str(raw.get("title") or cfg.title_hint or f"Mistero a {cfg.effective_setting}"),
                "tagline": str(raw.get("tagline") or f"Un delitto irrisolto in {cfg.effective_setting}"),
                "hook": str(
                    raw.get("hook")
                    or f"Durante un incontro esclusivo in {cfg.effective_setting}, un ospite illustre viene trovato senza vita."
                ),
                "victim_name": str(raw.get("victim_name") or "Lorenzo Valenti"),
                "victim_role": str(raw.get("victim_role") or "Anfitrione e collezionista di segreti"),
                "crime_summary": str(
                    raw.get("crime_summary")
                    or "La vittima è stata assassinata a porte chiuse poco prima di fare una rivelazione clamorosa."
                ),
                "atmosphere_directive": str(
                    raw.get("atmosphere_directive")
                    or f"Tono {cfg.effective_tone}, ritmo incalzante e sospetto tra tutti i presenti."
                ),
                "design_pillars": ensure_str_list(
                    raw.get("design_pillars"),
                    [
                        "Ogni personaggio nasconde un segreto compromettente",
                        "Soluzione deducibile tramite incrocio di alibi e indizi fisici",
                        f"Atmosfera coerente con {cfg.effective_setting}",
                    ],
                ),
            }

        concept = self.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema_cls=StoryConcept,
            temperature=0.6,
            max_tokens=700,
            normalizer=normalize,
        )
        project.concept = concept
        action = "revision" if critiques else "generate_concept"
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action=action,
            summary=f"Concept creato: '{concept.title}' — Vittima: {concept.victim_name} ({concept.victim_role})",
            status="revised" if critiques else "completed",
            details=concept.model_dump(),
        )
        return project
