"""AGENT 5 — Subplot Designer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from murdermind.agents.base import BaseNarrativeAgent, ensure_str_list
from murdermind.prompts.system_prompts import SUBPLOT_DESIGNER_PROMPT
from murdermind.schemas.mystery import AgentCritique, MysteryProject, SubplotItem


class SubplotListEnvelope(BaseModel):
    subplots: List[SubplotItem] = Field(default_factory=list)


class SubplotDesignerAgent(BaseNarrativeAgent):
    """Generates secondary subplots (blackmail, romance, rivalry, financial secrets) woven into the cast."""

    name = "SubplotDesigner"
    role_title = "AGENT 5 – Subplot Designer"
    phase_name = "Fase 5 – Subplot Design"
    system_prompt = SUBPLOT_DESIGNER_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        cfg = project.config
        if cfg.subplots_amount == "Nessuna":
            project.subplots = []
            project.log_activity(
                phase=self.phase_name,
                agent_name=self.name,
                action="skip_subplots",
                summary="Sottotrame disattivate dalla configurazione utente ('Nessuna').",
                status="completed",
            )
            return project

        count_map = {
            "Poche": 2,
            "Medie": 3,
            "Molte": 4,
            "Generazione automatica": 3,
        }
        target_count = count_map.get(cfg.subplots_amount, 3)
        char_summaries = [
            f"- {c.character_id} ({c.name}, {c.role}): segreto='{c.secret}'"
            for c in project.characters
        ]
        valid_ids = [c.character_id for c in project.characters] or ["char_01", "char_02", "char_03"]
        revision_note = self.format_critique_feedback(critiques)

        user_prompt = (
            f"Lingua: {cfg.language}\n"
            f"Mistero: {project.concept.title} | Vittima: {project.concept.victim_name}\n"
            f"Colpevole principale (NON cambiarlo): {project.plot.secret_solution.culprit_id}\n"
            f"Personaggi disponibili:\n" + "\n".join(char_summaries) + "\n"
            f"Genera {target_count} sottotrame secondarie intrecciate tra questi personaggi.\n"
            f"{revision_note}\n"
            "Restituisci un oggetto JSON con la chiave 'subplots'."
        )

        def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
            raw_list = raw.get("subplots")
            if not isinstance(raw_list, list):
                raw_list = [raw] if "title" in raw else []

            subplots: List[Dict[str, Any]] = []
            for idx, item in enumerate(raw_list, start=1):
                if not isinstance(item, dict):
                    continue
                involved = ensure_str_list(item.get("involved_character_ids"))
                involved_valid = [cid for cid in involved if cid in valid_ids]
                if len(involved_valid) < 2 and len(valid_ids) >= 2:
                    c1 = valid_ids[(idx - 1) % len(valid_ids)]
                    c2 = valid_ids[idx % len(valid_ids)]
                    involved_valid = [c1, c2]

                subplots.append(
                    {
                        "subplot_id": f"sub_{idx:02d}",
                        "title": str(item.get("title") or f"Intreccio Segreto {idx}"),
                        "category": str(item.get("category") or "Ricatto e Rivalità"),
                        "involved_character_ids": involved_valid,
                        "description": str(
                            item.get("description")
                            or f"Un patto segreto tra {', '.join(involved_valid)} rischia di emergere durante le indagini."
                        ),
                        "player_triggers": str(
                            item.get("player_triggers")
                            or "Emerge quando i due personaggi vengono interrogati sui loro movimenti prima della cena."
                        ),
                        "resolution": str(
                            item.get("resolution")
                            or "I personaggi coinvolti devono scegliere se coprirsi a vicenda o tradirsi per scagionarsi dall'accusa di omicidio."
                        ),
                        "connects_to_main_plot": str(
                            item.get("connects_to_main_plot")
                            or "Spiega il comportamento sospetto di due innocenti vicino al luogo del delitto."
                        ),
                    }
                )

            while len(subplots) < target_count and len(valid_ids) >= 2:
                idx = len(subplots) + 1
                c1 = valid_ids[(idx - 1) % len(valid_ids)]
                c2 = valid_ids[idx % len(valid_ids)]
                subplots.append(
                    {
                        "subplot_id": f"sub_{idx:02d}",
                        "title": f"Il Patto Nascosto ({c1} & {c2})",
                        "category": "Interesse economico / Ricatto",
                        "involved_character_ids": [c1, c2],
                        "description": (
                            f"{c1} e {c2} stavano negoziando alle spalle di {project.concept.victim_name} "
                            "per sottrarre un documento compromettente."
                        ),
                        "player_triggers": "Un messaggio cifrato trovato tra gli indizi fa emergere il loro incontro segreto.",
                        "resolution": "Confessare l'accordo economico permette a entrambi di dimostrare che non avevano interesse a uccidere la vittima in quel momento.",
                        "connects_to_main_plot": "Fornisce un alibi incrociato parziale ma alimenta i sospetti iniziali.",
                    }
                )

            return {"subplots": subplots}

        envelope = self.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema_cls=SubplotListEnvelope,
            temperature=0.65,
            max_tokens=1000,
            normalizer=normalize,
        )
        project.subplots = envelope.subplots
        action = "revision" if critiques else "generate_subplots"
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action=action,
            summary=f"Create {len(project.subplots)} sottotrame intrecciate tra i personaggi.",
            status="revised" if critiques else "completed",
            details={"subplot_ids": [s.subplot_id for s in project.subplots]},
        )
        return project
