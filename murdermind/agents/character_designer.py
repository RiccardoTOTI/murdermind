"""AGENT 4 — Character Designer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from murdermind.agents.base import BaseNarrativeAgent, ensure_str_list
from murdermind.prompts.system_prompts import CHARACTER_DESIGNER_PROMPT
from murdermind.schemas.mystery import (
    AgentCritique,
    CharacterProfile,
    CharacterRelationship,
    MysteryProject,
)


DEFAULT_ARCHETYPES = [
    ("Contessa Elena Morosini", "Socia d'affari ed erede contesa"),
    ("Dott. Valerio Santi", "Medico di fiducia e custode di segreti"),
    ("Marco Bellini", "Ex collaboratore ricattato dalla vittima"),
    ("Sofia De Luca", "Giornalista investigativa invitata in segreto"),
    ("Commissario Cesare Rinaldi", "Ospite d'onore dal passato ambiguo"),
    ("Camilla Ferri", "Nipote indebitata della vittima"),
    ("Arturo Bassi", "Maggiordomo / Direttore di sala"),
    ("Ginevra Conti", "Collezionista rivale"),
]


class CharacterDesignerAgent(BaseNarrativeAgent):
    """Creates rich, distinct characters with secrets, alibis, motives, and relationships."""

    name = "CharacterDesigner"
    role_title = "AGENT 4 – Character Designer"
    phase_name = "Fase 4 – Character Design"
    system_prompt = CHARACTER_DESIGNER_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        cfg = project.config
        concept = project.concept
        sol = project.plot.secret_solution
        total_chars = max(3, cfg.total_characters)
        revision_note = self.format_critique_feedback(critiques)

        # If revising specific characters only, only regenerate affected characters to save time and preserve state
        affected_ids = set()
        if critiques:
            for c in critiques:
                if c.target_agent == self.name and not c.resolved:
                    affected_ids.update(cid for cid in c.affected_ids if cid.startswith("char_"))

        existing_by_id = {c.character_id: c for c in project.characters}
        characters: List[CharacterProfile] = []

        for idx in range(1, total_chars + 1):
            char_id = f"char_{idx:02d}"
            is_playable = idx <= cfg.num_playable_characters
            is_culprit = char_id == sol.culprit_id

            if (
                critiques
                and affected_ids
                and char_id not in affected_ids
                and char_id in existing_by_id
            ):
                characters.append(existing_by_id[char_id])
                continue

            default_name, default_role = DEFAULT_ARCHETYPES[(idx - 1) % len(DEFAULT_ARCHETYPES)]
            if is_culprit and sol.culprit_name and sol.culprit_name != "Il Colpevole":
                default_name = sol.culprit_name

            other_idx = (idx % total_chars) + 1
            other_id = f"char_{other_idx:02d}"
            already_named = ", ".join(f"{c.character_id}: {c.name} ({c.role})" for c in characters)

            culprit_instructions = (
                f"ATTENZIONE: Questo personaggio ({char_id}) È IL COLPEVOLE DEL DELITTO.\n"
                f"- Movente canonico: {sol.motive}\n"
                f"- Arma usata: {sol.murder_weapon} in {sol.murder_location} ({sol.time_of_death})\n"
                f"- Falla nell'alibi da includere nel suo alibi: {sol.alibi_flaw}\n"
                if is_culprit
                else (
                    f"Questo personaggio ({char_id}) È INNOCENTE dell'omicidio, ma ha un forte segreto "
                    f"personale e un motivo di astio verso la vittima {concept.victim_name} che lo rende sospetto.\n"
                )
            )

            user_prompt = (
                f"Lingua: {cfg.language} | Ambientazione: {cfg.effective_setting} | Tono: {cfg.effective_tone}\n"
                f"Mistero: {concept.title} | Vittima: {concept.victim_name} ({concept.victim_role})\n"
                f"Genera il personaggio {char_id} ({'Giocante' if is_playable else 'PNG'}).\n"
                f"Suggerimento nome/ruolo (puoi migliorarlo): {default_name} — {default_role}\n"
                f"Altri personaggi già creati: {already_named or 'Nessuno ancora'}\n"
                f"Collega almeno una relazione a {other_id}.\n"
                f"{culprit_instructions}"
                f"{revision_note}\n"
                "Restituisci il profilo JSON del singolo personaggio."
            )

            def make_normalizer(
                c_id: str,
                playable: bool,
                culprit: bool,
                fallback_name: str,
                fallback_role: str,
                rel_target_id: str,
            ):
                def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
                    # Unwrap if nested under "character"
                    if "character" in raw and isinstance(raw["character"], dict):
                        raw = raw["character"]

                    name = str(raw.get("name") or fallback_name).strip()
                    role = str(raw.get("role") or fallback_role).strip()

                    rels_raw = raw.get("relationships")
                    rels: List[Dict[str, Any]] = []
                    if isinstance(rels_raw, list):
                        for r in rels_raw:
                            if isinstance(r, dict):
                                rels.append(
                                    {
                                        "target_character_id": str(
                                            r.get("target_character_id") or rel_target_id
                                        ),
                                        "target_name": str(r.get("target_name") or "Ospite"),
                                        "relation_type": str(
                                            r.get("relation_type") or "Conoscente sospetto"
                                        ),
                                        "public_view": str(
                                            r.get("public_view") or "Cordialità apparente"
                                        ),
                                        "hidden_tension": str(
                                            r.get("hidden_tension")
                                            or "Sospetto e rivalità latente"
                                        ),
                                    }
                                )
                    if not rels:
                        rels = [
                            {
                                "target_character_id": rel_target_id,
                                "target_name": "Altro Sospettato",
                                "relation_type": "Rivalità e segreti condivisi",
                                "public_view": "Si mostrano cortesi davanti agli altri invitati",
                                "hidden_tension": "Ciascuno teme che l'altro conosca la verità sul proprio passato.",
                            }
                        ]

                    secret_val = str(
                        raw.get("secret")
                        or (
                            f"È il vero responsabile della morte di {concept.victim_name} ({sol.motive})"
                            if culprit
                            else f"Nasconde un patto segreto e un debito compromettente con {concept.victim_name}."
                        )
                    ).strip()

                    alibi_val = str(
                        raw.get("alibi")
                        or (
                            f"Sostiene di essere stato in terrazza durante {sol.time_of_death}, ma {sol.alibi_flaw}"
                            if culprit
                            else f"Dichiara di essere stato vicino al corridoio tra le {sol.time_of_death} per una telefonata riservata."
                        )
                    ).strip()

                    motive_val = str(
                        raw.get("motive")
                        or (
                            sol.motive
                            if culprit
                            else f"{concept.victim_name} minacciava di rovinare la sua reputazione e la sua carriera."
                        )
                    ).strip()

                    return {
                        "character_id": c_id,
                        "name": name,
                        "role": role,
                        "is_playable": playable,
                        "is_culprit": culprit,
                        "background": str(
                            raw.get("background")
                            or f"{name} ({role}) conosceva {concept.victim_name} da anni ed era presente la sera del delitto."
                        ),
                        "personality": str(
                            raw.get("personality")
                            or "Carismatico, vigile, attento a misurare ogni parola."
                        ),
                        "goals": ensure_str_list(
                            raw.get("goals"),
                            [
                                "Smascherare l'assassino senza rivelare il proprio segreto"
                                if not culprit
                                else "Deviare i sospetti sugli altri ospiti e proteggere il proprio alibi",
                                "Scoprire cosa sapeva davvero la vittima",
                            ],
                        ),
                        "relationships": rels,
                        "secret": secret_val,
                        "alibi": alibi_val,
                        "motive": motive_val,
                        "known_facts": ensure_str_list(
                            raw.get("known_facts"),
                            [
                                f"Ha visto movimenti sospetti vicino a {sol.murder_location} intorno alle {sol.time_of_death}",
                                f"Sapeva che {concept.victim_name} aveva un conflitto acceso con uno dei presenti",
                            ],
                        ),
                        "hidden_facts": ensure_str_list(
                            raw.get("hidden_facts"),
                            [
                                secret_val,
                                f"Ha avuto un incontro riservato con {concept.victim_name} prima della cena",
                            ],
                        ),
                        "what_can_reveal": str(
                            raw.get("what_can_reveal")
                            or "Può confermare i propri spostamenti parziali solo se interrogato direttamente con un indizio in mano."
                        ),
                        "reaction_to_accusation": str(
                            raw.get("reaction_to_accusation")
                            or "Nega con fermezza e rilancia i sospetti puntando sulle contraddizioni altrui."
                        ),
                    }

                return normalize

            profile = self.llm.generate_structured(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                schema_cls=CharacterProfile,
                temperature=0.65,
                max_tokens=850,
                normalizer=make_normalizer(
                    char_id, is_playable, is_culprit, default_name, default_role, other_id
                ),
            )
            characters.append(profile)
            if is_culprit:
                sol.culprit_name = profile.name

        # Populate target_name across all relationships
        id_map = {c.character_id: c.name for c in characters}
        for c in characters:
            for rel in c.relationships:
                if rel.target_character_id in id_map:
                    rel.target_name = id_map[rel.target_character_id]

        project.characters = characters
        action = "revision" if critiques else "generate_characters"
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action=action,
            summary=(
                f"Creati {len(characters)} personaggi ({cfg.num_playable_characters} giocanti, "
                f"{cfg.num_npcs} PNG). Colpevole sincronizzato: {sol.culprit_id} ({sol.culprit_name})."
            ),
            status="revised" if critiques else "completed",
            details={"character_ids": [c.character_id for c in characters]},
        )
        return project
