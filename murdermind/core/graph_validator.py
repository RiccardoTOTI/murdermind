"""Information Graph Validator and Canonical Synchronizer for MurderMind."""

from __future__ import annotations

from typing import List, Set

from murdermind.schemas.mystery import (
    AgentCritique,
    CharacterRelationship,
    MysteryProject,
)


class InformationGraphValidator:
    """Validates and synchronizes the Single Source of Truth Information Graph."""

    @staticmethod
    def synchronize_canonical_graph(project: MysteryProject) -> None:
        """Normalize canonical IDs and synchronize cross-references across plot, characters, subplots, and clues."""
        # 1. Ensure sequential canonical character IDs char_01..char_NN
        for idx, char in enumerate(project.characters, start=1):
            if not char.character_id or not char.character_id.startswith("char_"):
                char.character_id = f"char_{idx:02d}"

        valid_char_ids: Set[str] = {c.character_id for c in project.characters}
        name_to_id = {c.name.strip().lower(): c.character_id for c in project.characters if c.name}
        id_to_name = {c.character_id: c.name for c in project.characters}

        # 2. Synchronize culprit between plot.secret_solution and characters
        if project.characters:
            sol = project.plot.secret_solution
            target_culprit_id = sol.culprit_id
            if target_culprit_id not in valid_char_ids:
                # Try matching by culprit_name
                matched_id = name_to_id.get(sol.culprit_name.strip().lower())
                if matched_id:
                    target_culprit_id = matched_id
                else:
                    # Check if any character is flagged is_culprit
                    flagged = [c.character_id for c in project.characters if c.is_culprit]
                    target_culprit_id = flagged[0] if flagged else project.characters[0].character_id
                sol.culprit_id = target_culprit_id

            for char in project.characters:
                char.is_culprit = char.character_id == sol.culprit_id
                if char.is_culprit and char.name:
                    sol.culprit_name = char.name
                    if not sol.motive and char.motive:
                        sol.motive = char.motive
                    elif sol.motive and not char.motive:
                        char.motive = sol.motive

        # 3. Ensure every character has valid relationship target IDs
        if len(project.characters) >= 2:
            char_list = project.characters
            for idx, char in enumerate(char_list):
                other_char = char_list[(idx + 1) % len(char_list)]
                if not char.relationships:
                    char.relationships.append(
                        CharacterRelationship(
                            target_character_id=other_char.character_id,
                            target_name=other_char.name,
                            relation_type="Sospetto reciproco",
                            public_view=f"Rapporto formale con {other_char.name}",
                            hidden_tension=f"Diffida delle mosse di {other_char.name} durante la serata.",
                        )
                    )
                else:
                    for rel in char.relationships:
                        if rel.target_character_id not in valid_char_ids or rel.target_character_id == char.character_id:
                            by_name = name_to_id.get(rel.target_name.strip().lower())
                            if by_name and by_name != char.character_id:
                                rel.target_character_id = by_name
                            else:
                                rel.target_character_id = other_char.character_id
                        rel.target_name = id_to_name.get(rel.target_character_id, rel.target_name)

        # 4. Normalize timeline event IDs and character refs
        for idx, evt in enumerate(project.plot.timeline, start=1):
            if not evt.event_id or not evt.event_id.startswith("evt_"):
                evt.event_id = f"evt_{idx:02d}"
            if valid_char_ids:
                normalized_involved: List[str] = []
                for ref in evt.involved_character_ids:
                    if ref in valid_char_ids:
                        normalized_involved.append(ref)
                    elif ref.strip().lower() in name_to_id:
                        normalized_involved.append(name_to_id[ref.strip().lower()])
                if not normalized_involved and evt.is_crime_event and project.plot.secret_solution.culprit_id in valid_char_ids:
                    normalized_involved.append(project.plot.secret_solution.culprit_id)
                evt.involved_character_ids = normalized_involved

        # 5. Normalize subplot IDs and character refs
        for idx, sub in enumerate(project.subplots, start=1):
            if not sub.subplot_id or not sub.subplot_id.startswith("sub_"):
                sub.subplot_id = f"sub_{idx:02d}"
            if valid_char_ids:
                cleaned_ids = [
                    cid if cid in valid_char_ids else name_to_id.get(cid.strip().lower(), "")
                    for cid in sub.involved_character_ids
                ]
                cleaned_ids = [c for c in cleaned_ids if c in valid_char_ids]
                if len(cleaned_ids) < 2 and len(project.characters) >= 2:
                    c1 = project.characters[(idx - 1) % len(project.characters)].character_id
                    c2 = project.characters[idx % len(project.characters)].character_id
                    cleaned_ids = [c1, c2]
                sub.involved_character_ids = list(dict.fromkeys(cleaned_ids))

        # 6. Normalize clue IDs and ensure culprit solvability link
        culprit_id = project.plot.secret_solution.culprit_id
        for idx, clue in enumerate(project.clues, start=1):
            if not clue.clue_id or not clue.clue_id.startswith("clue_"):
                clue.clue_id = f"clue_{idx:02d}"
            if clue.points_to_character_id and clue.points_to_character_id not in valid_char_ids:
                clue.points_to_character_id = name_to_id.get(
                    clue.points_to_character_id.strip().lower(), culprit_id
                )
            if clue.contradicts_alibi_of_id and clue.contradicts_alibi_of_id not in valid_char_ids:
                clue.contradicts_alibi_of_id = name_to_id.get(
                    clue.contradicts_alibi_of_id.strip().lower(), culprit_id
                )

        project.touch()

    @classmethod
    def validate_mvp_core(cls, project: MysteryProject) -> List[AgentCritique]:
        """Validate the 3-agent MVP core (Concept + Plot + Characters)."""
        critiques: List[AgentCritique] = []
        valid_char_ids = {c.character_id for c in project.characters}

        if not project.concept.title.strip() or not project.concept.victim_name.strip():
            critiques.append(
                AgentCritique(
                    target_agent="GameDirector",
                    issue_type="incomplete_concept",
                    severity="critical",
                    description="Manca il titolo o il nome della vittima nel concept iniziale.",
                    suggested_fix="Definire chiaramente titolo, vittima e premessa del delitto.",
                )
            )

        sol = project.plot.secret_solution
        if not sol.motive.strip() or not sol.murder_weapon.strip() or not sol.alibi_flaw.strip():
            critiques.append(
                AgentCritique(
                    target_agent="PlotArchitect",
                    issue_type="weak_solution",
                    severity="critical",
                    description="La soluzione segreta manca di movente, arma del delitto o punto debole dell'alibi.",
                    suggested_fix="Completare movente, arma, dinamica e falla nell'alibi del colpevole.",
                )
            )

        if len(project.plot.timeline) < 3:
            critiques.append(
                AgentCritique(
                    target_agent="PlotArchitect",
                    issue_type="short_timeline",
                    severity="major",
                    description="La cronologia canonica ha meno di 3 eventi.",
                    suggested_fix="Aggiungere almeno 4 eventi ordinati cronologicamente incluso il momento del delitto.",
                )
            )

        if not project.characters:
            critiques.append(
                AgentCritique(
                    target_agent="CharacterDesigner",
                    issue_type="missing_characters",
                    severity="critical",
                    description="Nessun personaggio generato.",
                    suggested_fix="Creare tutti i personaggi richiesti con segreti, alibi e moventi.",
                )
            )
            return critiques

        if sol.culprit_id not in valid_char_ids:
            critiques.append(
                AgentCritique(
                    target_agent="CharacterDesigner",
                    issue_type="culprit_id_mismatch",
                    severity="critical",
                    description=f"Il colpevole {sol.culprit_id} non corrisponde a nessun ID personaggio ({sorted(valid_char_ids)}).",
                    suggested_fix="Allineare l'ID del colpevole tra PlotArchitect e CharacterDesigner.",
                    affected_ids=[sol.culprit_id],
                )
            )

        for char in project.characters:
            if not char.secret.strip() or not char.alibi.strip() or not char.motive.strip():
                critiques.append(
                    AgentCritique(
                        target_agent="CharacterDesigner",
                        issue_type="incomplete_character_profile",
                        severity="major",
                        description=f"Il personaggio {char.character_id} ({char.name}) non ha segreto, alibi o movente completo.",
                        suggested_fix=f"Arricchire segreto, alibi e movente di {char.character_id}.",
                        affected_ids=[char.character_id],
                    )
                )

        return critiques

    @classmethod
    def validate_full_graph(cls, project: MysteryProject) -> List[AgentCritique]:
        """Validate the complete 10-agent Information Graph."""
        critiques = cls.validate_mvp_core(project)
        valid_char_ids = {c.character_id for c in project.characters}
        culprit_id = project.plot.secret_solution.culprit_id

        # Check clues solvability
        if len(project.clues) < 3:
            critiques.append(
                AgentCritique(
                    target_agent="ClueMaster",
                    issue_type="insufficient_clues",
                    severity="critical",
                    description="Il sistema investigativo ha meno di 3 indizi strutturati.",
                    suggested_fix="Generare almeno 4-6 indizi (fisici, documentali, testimoniali) + almeno 1 depistaggio.",
                )
            )
        else:
            culprit_clues = [
                c
                for c in project.clues
                if not c.is_red_herring
                and (
                    c.points_to_character_id == culprit_id
                    or c.contradicts_alibi_of_id == culprit_id
                )
            ]
            if len(culprit_clues) < 2:
                critiques.append(
                    AgentCritique(
                        target_agent="ClueMaster",
                        issue_type="unsolvable_mystery",
                        severity="critical",
                        description=(
                            f"Meno di 2 indizi veritieri puntano al colpevole ({culprit_id}) "
                            "o smontano il suo alibi."
                        ),
                        suggested_fix=(
                            f"Assicurare che almeno 2 indizi non-depistaggio colleghino {culprit_id} "
                            "all'arma/luogo del delitto e contraddicano il suo alibi."
                        ),
                        affected_ids=[culprit_id],
                    )
                )

        # Check subplots
        if project.config.subplots_amount != "Nessuna" and not project.subplots:
            critiques.append(
                AgentCritique(
                    target_agent="SubplotDesigner",
                    issue_type="missing_subplots",
                    severity="major",
                    description="Nessuna sottotrama generata nonostante la configurazione lo richieda.",
                    suggested_fix="Creare sottotrame intrecciate tra i personaggi con risoluzione chiara.",
                )
            )
        for sub in project.subplots:
            invalid_refs = [cid for cid in sub.involved_character_ids if cid not in valid_char_ids]
            if invalid_refs:
                critiques.append(
                    AgentCritique(
                        target_agent="SubplotDesigner",
                        issue_type="invalid_subplot_characters",
                        severity="major",
                        description=f"La sottotrama {sub.subplot_id} cita personaggi inesistenti: {invalid_refs}.",
                        suggested_fix="Collegare la sottotrama solo a ID personaggi canonici esistenti.",
                        affected_ids=[sub.subplot_id],
                    )
                )

        return critiques

    @staticmethod
    def check_player_sheet_firewall(
        project: MysteryProject, character_id: str, sheet_markdown: str
    ) -> List[str]:
        """Verify that a player's character sheet does not leak Master-only solution markers or other players' secrets."""
        violations: List[str] = []
        if "SOLUZIONE SEGRETA DEL MASTER" in sheet_markdown:
            violations.append("Contiene l'intestazione riservata al Master.")

        for other in project.characters:
            if other.character_id == character_id:
                continue
            if other.secret and len(other.secret) > 25 and other.secret in sheet_markdown:
                violations.append(
                    f"Espone il segreto privato di {other.character_id} ({other.name})."
                )
        return violations
