"""Explicit, observable Multi-Agent Orchestrator for MurderMind."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from murdermind.agents import (
    BaseNarrativeAgent,
    CharacterDesignerAgent,
    ClueMasterAgent,
    ContinuityEditorAgent,
    FinalGameProducerAgent,
    GameDirectorAgent,
    GameMechanicsAgent,
    NarrativeWriterAgent,
    PlotArchitectAgent,
    SubplotDesignerAgent,
    WorldBuilderAgent,
)
from murdermind.core.graph_validator import InformationGraphValidator
from murdermind.core.llm_client import OpenAICompatibleClient
from murdermind.schemas.mystery import AgentCritique, MysteryProject, StoryConfig


StepCallback = Optional[Callable[[MysteryProject, str], None]]


class MurderMysteryOrchestrator:
    """Coordinates the 10 specialized narrative agents, shared Information Graph, and iterative review loops."""

    def __init__(self, llm_client: Optional[OpenAICompatibleClient] = None) -> None:
        self.llm = llm_client or OpenAICompatibleClient()
        self.game_director = GameDirectorAgent(self.llm)
        self.world_builder = WorldBuilderAgent(self.llm)
        self.plot_architect = PlotArchitectAgent(self.llm)
        self.character_designer = CharacterDesignerAgent(self.llm)
        self.subplot_designer = SubplotDesignerAgent(self.llm)
        self.clue_master = ClueMasterAgent(self.llm)
        self.game_mechanics = GameMechanicsAgent(self.llm)
        self.narrative_writer = NarrativeWriterAgent(self.llm)
        self.continuity_editor = ContinuityEditorAgent(self.llm)
        self.final_producer = FinalGameProducerAgent(self.llm)

        self.agents_by_name: Dict[str, BaseNarrativeAgent] = {
            self.game_director.name: self.game_director,
            self.world_builder.name: self.world_builder,
            self.plot_architect.name: self.plot_architect,
            self.character_designer.name: self.character_designer,
            self.subplot_designer.name: self.subplot_designer,
            self.clue_master.name: self.clue_master,
            self.game_mechanics.name: self.game_mechanics,
            self.narrative_writer.name: self.narrative_writer,
            self.continuity_editor.name: self.continuity_editor,
            self.final_producer.name: self.final_producer,
        }

        self.phase_map: Dict[int, BaseNarrativeAgent] = {
            1: self.game_director,
            2: self.world_builder,
            3: self.plot_architect,
            4: self.character_designer,
            5: self.subplot_designer,
            6: self.clue_master,
            7: self.game_mechanics,
            8: self.narrative_writer,
            9: self.continuity_editor,
            10: self.final_producer,
        }

    def create_project(self, config: Optional[StoryConfig] = None) -> MysteryProject:
        """Initialize a new MysteryProject with canonical defaults."""
        project = MysteryProject(config=config or StoryConfig())
        project.log_activity(
            phase="Inizializzazione",
            agent_name="GameDirector",
            action="init_project",
            summary=(
                f"Progetto {project.project_id} creato: ambientazione '{project.config.effective_setting}', "
                f"{project.config.num_playable_characters} PG + {project.config.num_npcs} PNG, "
                f"tono '{project.config.effective_tone}'."
            ),
            status="completed",
        )
        return project

    def run_phase(
        self,
        project: MysteryProject,
        phase_number: int,
        critiques: Optional[List[AgentCritique]] = None,
        on_step: StepCallback = None,
    ) -> MysteryProject:
        """Execute a single phase (1..10) and synchronize the Information Graph."""
        if phase_number not in self.phase_map:
            raise ValueError(f"Invalid phase number: {phase_number} (expected 1..10)")

        agent = self.phase_map[phase_number]
        project.status = "generating"
        if phase_number == 9:
            self.continuity_editor.run(
                project,
                critiques=critiques,
                mvp_only=False,
                iteration=len(project.reviews) + 1,
            )
        else:
            agent.run(project, critiques=critiques)

        InformationGraphValidator.synchronize_canonical_graph(project)
        if on_step:
            on_step(project, agent.phase_name)
        return project

    def _apply_review_revisions(
        self,
        project: MysteryProject,
        critiques: List[AgentCritique],
        allowed_agents: Optional[List[str]] = None,
        on_step: StepCallback = None,
    ) -> bool:
        """Dispatch critiques to target agents in canonical dependency order and mark them resolved."""
        ordered_names = [
            "GameDirector",
            "WorldBuilder",
            "PlotArchitect",
            "CharacterDesigner",
            "SubplotDesigner",
            "ClueMaster",
            "GameMechanicsDesigner",
            "NarrativeWriter",
        ]
        if allowed_agents is not None:
            ordered_names = [n for n in ordered_names if n in allowed_agents]

        any_revised = False
        for agent_name in ordered_names:
            agent_critiques = [
                c
                for c in critiques
                if c.target_agent == agent_name
                and not c.resolved
                and c.severity in ("critical", "major")
            ]
            if not agent_critiques:
                continue

            agent = self.agents_by_name[agent_name]
            project.log_activity(
                phase="Fase 9 – Ciclo di Revisione",
                agent_name="GameDirector",
                action="dispatch_revision",
                summary=f"Invio richiesta di revisione mirata a {agent_name} ({len(agent_critiques)} rilievi).",
                status="critique",
                details={"critiques": [c.model_dump() for c in agent_critiques]},
            )
            agent.run(project, critiques=agent_critiques)
            for c in agent_critiques:
                c.resolved = True
            InformationGraphValidator.synchronize_canonical_graph(project)
            any_revised = True
            if on_step:
                on_step(project, f"Revisione {agent_name}")

        return any_revised

    def run_mvp_pipeline(
        self,
        project: MysteryProject,
        on_step: StepCallback = None,
    ) -> MysteryProject:
        """Execute the 3-agent collaborative MVP (GameDirector, PlotArchitect, CharacterDesigner) + review loop."""
        project.status = "generating"

        # Step 1: Game Director
        self.game_director.run(project)
        if on_step:
            on_step(project, self.game_director.phase_name)

        # Step 2: Plot Architect
        self.plot_architect.run(project)
        if on_step:
            on_step(project, self.plot_architect.phase_name)

        # Step 3: Character Designer
        self.character_designer.run(project)
        InformationGraphValidator.synchronize_canonical_graph(project)
        if on_step:
            on_step(project, self.character_designer.phase_name)

        # Step 4: Iterative Review Loop on MVP Core
        max_iters = max(1, project.config.max_review_iterations)
        for iteration in range(1, max_iters + 1):
            self.continuity_editor.run(project, mvp_only=True, iteration=iteration)
            latest_review = project.reviews[-1]
            if on_step:
                on_step(project, f"Revisione MVP #{iteration}")

            if latest_review.passed:
                break

            revised = self._apply_review_revisions(
                project,
                latest_review.critiques,
                allowed_agents=["GameDirector", "PlotArchitect", "CharacterDesigner"],
                on_step=on_step,
            )
            if not revised:
                break

        project.status = "completed"
        project.touch()
        return project

    def run_full_pipeline(
        self,
        project: MysteryProject,
        on_step: StepCallback = None,
    ) -> MysteryProject:
        """Execute all 10 phases including iterative ContinuityEditor review & targeted agent revisions."""
        project.status = "generating"

        # Phases 1..8
        for phase_num in range(1, 9):
            self.run_phase(project, phase_num, on_step=on_step)

        # Phase 9: Iterative Critical Review & Targeted Revisions
        max_iters = max(1, project.config.max_review_iterations)
        for iteration in range(1, max_iters + 1):
            self.continuity_editor.run(project, mvp_only=False, iteration=iteration)
            InformationGraphValidator.synchronize_canonical_graph(project)
            latest_review = project.reviews[-1]
            if on_step:
                on_step(project, f"Fase 9 – Critical Review #{iteration}")

            if latest_review.passed:
                break

            revised = self._apply_review_revisions(
                project,
                latest_review.critiques,
                on_step=on_step,
            )
            if not revised:
                break

        # Phase 10: Final Game Producer
        self.run_phase(project, 10, on_step=on_step)
        project.status = "completed"
        project.touch()
        return project
