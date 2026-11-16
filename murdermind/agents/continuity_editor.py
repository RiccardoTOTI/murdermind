"""AGENT 9 — Continuity Editor / Critical Reviewer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from murdermind.agents.base import BaseNarrativeAgent, ensure_str_list
from murdermind.core.graph_validator import InformationGraphValidator
from murdermind.prompts.system_prompts import CONTINUITY_EDITOR_PROMPT
from murdermind.schemas.mystery import AgentCritique, MysteryProject, ReviewReport


VALID_TARGET_AGENTS = {
    "GameDirector",
    "WorldBuilder",
    "PlotArchitect",
    "CharacterDesigner",
    "SubplotDesigner",
    "ClueMaster",
    "GameMechanicsDesigner",
    "NarrativeWriter",
}


class ContinuityEditorAgent(BaseNarrativeAgent):
    """Independent critical reviewer combining deterministic graph checks with LLM narrative critique."""

    name = "ContinuityEditor"
    role_title = "AGENT 9 – Continuity Editor / Critical Reviewer"
    phase_name = "Fase 9 – Critical Review"
    system_prompt = CONTINUITY_EDITOR_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
        mvp_only: bool = False,
        iteration: int = 1,
    ) -> MysteryProject:
        # 1. Run deterministic Information Graph Validator first
        graph_critiques = (
            InformationGraphValidator.validate_mvp_core(project)
            if mvp_only
            else InformationGraphValidator.validate_full_graph(project)
        )

        sol = project.plot.secret_solution
        char_summary = "; ".join(
            f"{c.character_id}({c.name}, culprit={c.is_culprit}, alibi='{c.alibi[:60]}')"
            for c in project.characters
        )
        clue_summary = "; ".join(
            f"{cl.clue_id}({cl.title}, points_to={cl.points_to_character_id}, red_herring={cl.is_red_herring})"
            for cl in project.clues
        )

        user_prompt = (
            f"Revisione iterazione #{iteration}\n"
            f"Titolo: {project.concept.title} | Vittima: {sol.victim_name}\n"
            f"Soluzione: colpevole={sol.culprit_id} ({sol.culprit_name}), arma={sol.murder_weapon}, "
            f"orario={sol.time_of_death}, falla alibi={sol.alibi_flaw}\n"
            f"Personaggi: {char_summary}\n"
            f"Indizi: {clue_summary or 'Modalità MVP 3-agenti'}\n"
            f"Problemi strutturali rilevati dal grafo: {len(graph_critiques)}\n"
            "Valuta la coerenza complessiva e restituisci il report di revisione JSON."
        )

        def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
            raw_critiques = raw.get("critiques")
            merged: List[Dict[str, Any]] = [c.model_dump() for c in graph_critiques]

            if isinstance(raw_critiques, list):
                for item in raw_critiques:
                    if not isinstance(item, dict):
                        continue
                    target = str(item.get("target_agent") or "PlotArchitect").strip()
                    if target not in VALID_TARGET_AGENTS:
                        target = "PlotArchitect"
                    desc = str(item.get("description") or "").strip()
                    if not desc:
                        continue
                    merged.append(
                        {
                            "target_agent": target,
                            "issue_type": str(item.get("issue_type") or "narrative_consistency"),
                            "severity": str(item.get("severity") or "minor").lower()
                            if str(item.get("severity") or "minor").lower() in ("minor", "major", "critical")
                            else "minor",
                            "description": desc,
                            "suggested_fix": str(
                                item.get("suggested_fix")
                                or "Rendere più esplicito il legame tra indizio, orario e alibi."
                            ),
                            "affected_ids": ensure_str_list(item.get("affected_ids")),
                            "resolved": False,
                        }
                    )

            has_blocking = any(c["severity"] in ("critical", "major") for c in merged) and len(graph_critiques) > 0
            passed = bool(raw.get("passed", True)) and not has_blocking
            score_raw = raw.get("coherence_score", 90 if passed else 68)
            try:
                score = max(0, min(100, int(score_raw)))
            except (ValueError, TypeError):
                score = 88 if passed else 68

            return {
                "iteration": iteration,
                "passed": passed,
                "coherence_score": score,
                "critiques": merged,
                "summary": str(
                    raw.get("summary")
                    or (
                        f"Iterazione {iteration}: verifica superata con punteggio {score}/100."
                        if passed
                        else f"Iterazione {iteration}: rilevate {len(merged)} criticità da correggere."
                    )
                ),
            }

        report = self.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema_cls=ReviewReport,
            temperature=0.3,
            max_tokens=700,
            normalizer=normalize,
        )
        project.reviews.append(report)
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action=f"review_iteration_{iteration}",
            summary=(
                f"Revisione #{iteration}: {'APPROVATA' if report.passed else 'RICHIESTA REVISIONE'} "
                f"(Punteggio coerenza: {report.coherence_score}/100, Osservazioni: {len(report.critiques)})"
            ),
            status="completed" if report.passed else "critique",
            details=report.model_dump(),
        )
        return project
