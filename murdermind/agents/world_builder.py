"""AGENT 2 — World Builder."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from murdermind.agents.base import BaseNarrativeAgent, ensure_str_list
from murdermind.prompts.system_prompts import WORLD_BUILDER_PROMPT
from murdermind.schemas.mystery import AgentCritique, MysteryProject, WorldState


class WorldBuilderAgent(BaseNarrativeAgent):
    """Builds the historical/contemporary setting, locations, atmosphere, and world secrets."""

    name = "WorldBuilder"
    role_title = "AGENT 2 – World Builder"
    phase_name = "Fase 2 – World Building"
    system_prompt = WORLD_BUILDER_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        cfg = project.config
        concept = project.concept
        revision_note = self.format_critique_feedback(critiques)

        user_prompt = (
            f"Lingua: {cfg.language}\n"
            f"Titolo: {concept.title} | Tagline: {concept.tagline}\n"
            f"Ambientazione: {cfg.effective_setting} | Tono: {cfg.effective_tone}\n"
            f"Vittima: {concept.victim_name} ({concept.victim_role})\n"
            f"Premessa: {concept.hook}\n"
            f"{revision_note}\n"
            "Costruisci il mondo narrativo con almeno 3 luoghi chiave (loc_01, loc_02, loc_03), segreti del luogo e fatti pubblici in JSON."
        )

        def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
            raw_locs = raw.get("locations")
            locations: List[Dict[str, Any]] = []
            if isinstance(raw_locs, list):
                for idx, loc in enumerate(raw_locs, start=1):
                    if isinstance(loc, dict):
                        locations.append(
                            {
                                "location_id": f"loc_{idx:02d}",
                                "name": str(loc.get("name") or f"Ambiente {idx}"),
                                "description": str(
                                    loc.get("description")
                                    or f"Area riservata di {cfg.effective_setting}."
                                ),
                                "hidden_detail": str(
                                    loc.get("hidden_detail")
                                    or "Presenta un accesso secondario noto a pochi."
                                ),
                            }
                        )
            if len(locations) < 3:
                locations = [
                    {
                        "location_id": "loc_01",
                        "name": "Studio Privato",
                        "description": f"La stanza più riservata di {cfg.effective_setting}, dove {concept.victim_name} custodiva documenti sensibili.",
                        "hidden_detail": "Una cassaforte a muro dietro la libreria e una finestra che dà sul giardino interno.",
                    },
                    {
                        "location_id": "loc_02",
                        "name": "Salone delle Feste",
                        "description": "Il grande salone dove gli ospiti si sono riuniti per la cena e l'aperitivo.",
                        "hidden_detail": "L'orologio a pendolo segna cinque minuti in anticipo rispetto all'ora reale.",
                    },
                    {
                        "location_id": "loc_03",
                        "name": "Galleria / Corridoio d'Onore",
                        "description": "Passaggio scarsamente illuminato che collega il salone allo studio privato.",
                        "hidden_detail": "Il pavimento vicino alla porta di servizio trattiene tracce di passaggio.",
                    },
                ]

            return {
                "era_and_place": str(
                    raw.get("era_and_place") or f"{cfg.effective_setting} — Serata esclusiva a porte chiuse"
                ),
                "social_cultural_context": str(
                    raw.get("social_cultural_context")
                    or "Un microcosmo elitario attraversato da rivalità economiche, segreti inconfessabili e alleanze fragili."
                ),
                "atmosphere": str(
                    raw.get("atmosphere")
                    or f"Atmosfera {cfg.effective_tone}: luci soffuse, sguardi furtivi e tensione crescente."
                ),
                "backstory": str(
                    raw.get("backstory")
                    or f"{concept.victim_name} ha convocato tutti i presenti con il pretesto di una serata speciale, ma in realtà intendeva regolare vecchi conti."
                ),
                "characteristic_elements": ensure_str_list(
                    raw.get("characteristic_elements"),
                    [
                        "Isolamento temporaneo dall'esterno",
                        "Documenti riservati scomparsi dallo studio",
                        "Vecchi rancori mai sopiti tra gli invitati",
                    ],
                ),
                "locations": locations,
                "world_secrets": ensure_str_list(
                    raw.get("world_secrets"),
                    [
                        "Esiste un passaggio di servizio che collega la galleria allo studio senza attraversare il salone.",
                        f"{concept.victim_name} aveva modificato le sue disposizioni segrete poche ore prima della cena.",
                    ],
                ),
                "public_facts": ensure_str_list(
                    raw.get("public_facts"),
                    [
                        f"Tutti gli ospiti sono stati invitati personalmente da {concept.victim_name}.",
                        "Nessuno estraneo è entrato o uscito dalla proprietà dopo le 20:00.",
                    ],
                ),
            }

        world = self.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema_cls=WorldState,
            temperature=0.65,
            max_tokens=900,
            normalizer=normalize,
        )
        project.world = world
        action = "revision" if critiques else "generate_world"
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action=action,
            summary=f"Mondo narrativo costruito: {world.era_and_place} ({len(world.locations)} luoghi chiave).",
            status="revised" if critiques else "completed",
            details=world.model_dump(),
        )
        return project
