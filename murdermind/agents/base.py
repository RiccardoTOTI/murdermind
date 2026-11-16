"""Base class and shared utilities for MurderMind narrative agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from murdermind.core.llm_client import OpenAICompatibleClient
from murdermind.schemas.mystery import AgentCritique, MysteryProject


def ensure_str_list(val: Any, default: Optional[List[str]] = None) -> List[str]:
    """Coerce a value into a list of non-empty strings."""
    if isinstance(val, list):
        result = [str(item).strip() for item in val if str(item).strip()]
        return result if result else (default or [])
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return default or []


class BaseNarrativeAgent(ABC):
    """Abstract base class for every specialized MurderMind agent."""

    name: str = "BaseAgent"
    role_title: str = "Narrative Agent"
    phase_name: str = "Base Phase"
    system_prompt: str = ""

    def __init__(self, llm_client: OpenAICompatibleClient) -> None:
        self.llm = llm_client

    @abstractmethod
    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        """Execute the agent's task or targeted revision on the shared MysteryProject."""

    def format_critique_feedback(
        self, critiques: Optional[List[AgentCritique]]
    ) -> str:
        """Format critiques addressed to this agent for revision prompts."""
        if not critiques:
            return ""
        relevant = [
            c
            for c in critiques
            if c.target_agent.lower() in (self.name.lower(), "all")
            and not c.resolved
        ]
        if not relevant:
            return ""
        lines = ["\nREVISIONE RICHIESTA DAL REVISORE CRITICO:"]
        for idx, c in enumerate(relevant, start=1):
            lines.append(
                f"{idx}. [{c.severity.upper()} - {c.issue_type}] {c.description} -> Correzione: {c.suggested_fix}"
            )
        return "\n".join(lines)
