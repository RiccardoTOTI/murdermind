"""AGENT 6 — Clue Master."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from murdermind.agents.base import BaseNarrativeAgent
from murdermind.prompts.system_prompts import CLUE_MASTER_PROMPT
from murdermind.schemas.mystery import AgentCritique, ClueItem, MysteryProject


class ClueListEnvelope(BaseModel):
    clues: List[ClueItem] = Field(default_factory=list)


class ClueMasterAgent(BaseNarrativeAgent):
    """Designs physical, testimonial, documentary, and red-herring clues guaranteeing logical solvability."""

    name = "ClueMaster"
    role_title = "AGENT 6 – Clue Master"
    phase_name = "Fase 6 – Clue Design"
    system_prompt = CLUE_MASTER_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        cfg = project.config
        sol = project.plot.secret_solution
        valid_ids = [c.character_id for c in project.characters] or ["char_01", "char_02", "char_03"]
        culprit_id = sol.culprit_id if sol.culprit_id in valid_ids else valid_ids[0]
        innocent_ids = [cid for cid in valid_ids if cid != culprit_id] or [valid_ids[0]]
        revision_note = self.format_critique_feedback(critiques)

        char_brief = "\n".join(
            f"- {c.character_id} ({c.name}, {'COLPEVOLE' if c.is_culprit else 'Innocente'}): alibi='{c.alibi}' | segreto='{c.secret}'"
            for c in project.characters
        )

        user_prompt = (
            f"Lingua: {cfg.language}\n"
            f"Mistero: {project.concept.title} | Vittima: {sol.victim_name}\n"
            f"SOLUZIONE CANONICA DA DIMOSTRARE:\n"
            f"- Colpevole: {culprit_id} ({sol.culprit_name})\n"
            f"- Arma: {sol.murder_weapon}\n"
            f"- Luogo: {sol.murder_location} | Orario: {sol.time_of_death}\n"
            f"- Movente: {sol.motive}\n"
            f"- Falla nell'alibi del colpevole: {sol.alibi_flaw}\n"
            f"Personaggi:\n{char_brief}\n"
            "Progetta almeno 5 indizi (clue_01..clue_05): almeno 3 devono puntare logicamente al colpevole "
            f"({culprit_id}) e smontare il suo alibi, e almeno 1-2 devono essere depistaggi (is_red_herring=true) "
            "legati alle sottotrame degli innocenti.\n"
            f"{revision_note}\n"
            "Restituisci un oggetto JSON con la chiave 'clues'."
        )

        def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
            raw_list = raw.get("clues")
            if not isinstance(raw_list, list):
                raw_list = [raw] if "title" in raw else []

            clues: List[Dict[str, Any]] = []
            for idx, item in enumerate(raw_list, start=1):
                if not isinstance(item, dict):
                    continue
                pts = str(item.get("points_to_character_id") or "").strip()
                if pts not in valid_ids:
                    pts = culprit_id if not item.get("is_red_herring") else innocent_ids[0]

                contra = item.get("contradicts_alibi_of_id")
                if isinstance(contra, str):
                    contra = contra.strip()
                    if contra not in valid_ids:
                        contra = culprit_id if not item.get("is_red_herring") else None
                else:
                    contra = culprit_id if idx in (1, 2) else None

                phase = item.get("discovery_phase", ((idx - 1) % 3) + 1)
                try:
                    phase_int = max(1, min(3, int(phase)))
                except (ValueError, TypeError):
                    phase_int = ((idx - 1) % 3) + 1

                clues.append(
                    {
                        "clue_id": f"clue_{idx:02d}",
                        "title": str(item.get("title") or f"Reperto Investigativo {idx}"),
                        "clue_type": str(item.get("clue_type") or "fisico"),
                        "description": str(
                            item.get("description")
                            or f"Elemento probatorio rinvenuto vicino a {sol.murder_location}."
                        ),
                        "printable_text": str(
                            item.get("printable_text")
                            or item.get("description")
                            or f"REPERTO #{idx}: Traccia rilevata in {sol.murder_location}."
                        ),
                        "discovery_phase": phase_int,
                        "location_or_holder": str(
                            item.get("location_or_holder") or sol.murder_location
                        ),
                        "points_to_character_id": pts,
                        "contradicts_alibi_of_id": contra,
                        "is_red_herring": bool(item.get("is_red_herring", False)),
                        "logical_inference": str(
                            item.get("logical_inference")
                            or f"Collega {pts} alla dinamica degli eventi intorno alle {sol.time_of_death}."
                        ),
                    }
                )

            # Guarantee solvability: ensure at least 3 canonical clues point to culprit_id & contradict their alibi, plus 1 red herring
            canonical_baseline = [
                {
                    "title": f"Prova Fisica: {sol.murder_weapon}",
                    "clue_type": "fisico",
                    "description": (
                        f"Tracce compatibili con '{sol.murder_weapon}' rinvenute in {sol.murder_location}, "
                        f"accompagnate da un dettaglio accessibile solo a {sol.culprit_name} ({culprit_id})."
                    ),
                    "printable_text": (
                        f"[SCHEDA REPERTO] In {sol.murder_location} sono state isolate tracce di {sol.murder_weapon}. "
                        f"Chi ha agito conosceva le abitudini private di {sol.victim_name}."
                    ),
                    "discovery_phase": 1,
                    "location_or_holder": sol.murder_location,
                    "points_to_character_id": culprit_id,
                    "contradicts_alibi_of_id": culprit_id,
                    "is_red_herring": False,
                    "logical_inference": f"Dimostra il metodo del delitto e restringe il campo a {culprit_id}.",
                },
                {
                    "title": "Contraddizione Oraria dell'Alibi",
                    "clue_type": "contraddizione",
                    "description": f"Un riscontro oggettivo smentisce l'alibi di {sol.culprit_name}: {sol.alibi_flaw}",
                    "printable_text": (
                        f"[ ANNOTAZIONE ORARIA - {sol.time_of_death} ] "
                        f"Contrariamente a quanto dichiarato, {sol.alibi_flaw}"
                    ),
                    "discovery_phase": 2,
                    "location_or_holder": "Corridoio d'accesso / Registro",
                    "points_to_character_id": culprit_id,
                    "contradicts_alibi_of_id": culprit_id,
                    "is_red_herring": False,
                    "logical_inference": f"Smonta definitivamente l'alibi di {culprit_id} nella fascia {sol.time_of_death}.",
                },
                {
                    "title": "Documento Riservato sul Movente",
                    "clue_type": "documento",
                    "description": (
                        f"Appunto privato di {sol.victim_name} che documenta il conflitto decisivo con {sol.culprit_name}: {sol.motive}"
                    ),
                    "printable_text": (
                        f"[DOCUMENTO CONFIDENZIALE DELLA VITTIMA] 'Non posso più tacere: questa sera affronterò "
                        f"la questione riguardante {sol.motive}.'"
                    ),
                    "discovery_phase": 3,
                    "location_or_holder": "Scrivania della vittima",
                    "points_to_character_id": culprit_id,
                    "contradicts_alibi_of_id": culprit_id,
                    "is_red_herring": False,
                    "logical_inference": f"Conferma il movente diretto di {culprit_id}.",
                },
                {
                    "title": "Biglietto Compromettente (Falsa Pista)",
                    "clue_type": "messaggio",
                    "description": (
                        f"Un messaggio minaccioso associato a {innocent_ids[0]}, che in realtà riguarda un affare secondario e non l'omicidio."
                    ),
                    "printable_text": (
                        "[BIGLIETTO STRAPPATO] 'Se parlerai stasera, perderai tutto ciò che hai costruito. Ci vediamo alle 20:45.'"
                    ),
                    "discovery_phase": 1,
                    "location_or_holder": "Salone principale",
                    "points_to_character_id": innocent_ids[0],
                    "contradicts_alibi_of_id": None,
                    "is_red_herring": True,
                    "logical_inference": (
                        f"Depistaggio: riguarda il litigio delle 20:45 con {innocent_ids[0]}, quando la vittima era ancora viva."
                    ),
                },
            ]

            for base_item in canonical_baseline:
                culprit_true_count = sum(
                    1
                    for c in clues
                    if not c["is_red_herring"]
                    and (
                        c["points_to_character_id"] == culprit_id
                        or c["contradicts_alibi_of_id"] == culprit_id
                    )
                )
                has_red_herring = any(c["is_red_herring"] for c in clues)
                if len(clues) < 4 or culprit_true_count < 2 or (base_item["is_red_herring"] and not has_red_herring):
                    new_item = dict(base_item)
                    new_item["clue_id"] = f"clue_{len(clues) + 1:02d}"
                    clues.append(new_item)

            return {"clues": clues}

        envelope = self.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema_cls=ClueListEnvelope,
            temperature=0.5,
            max_tokens=1100,
            normalizer=normalize,
        )
        project.clues = envelope.clues
        action = "revision" if critiques else "generate_clues"
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action=action,
            summary=(
                f"Progettati {len(project.clues)} indizi "
                f"({sum(1 for c in project.clues if not c.is_red_herring)} prove canoniche, "
                f"{sum(1 for c in project.clues if c.is_red_herring)} depistaggi)."
            ),
            status="revised" if critiques else "completed",
            details={"clue_ids": [c.clue_id for c in project.clues]},
        )
        return project
