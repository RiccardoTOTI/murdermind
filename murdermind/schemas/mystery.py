"""Single Source of Truth schemas for the Murder Mystery Information Graph."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SETTING_PRESETS: List[str] = [
    "Castello medievale",
    "Villa nobiliare",
    "Hotel",
    "Nave",
    "Treno",
    "Anni '20",
    "Anni '70",
    "Contemporanea",
    "Fantasy",
    "Horror",
    "Fantascienza",
    "Personalizzata",
]

COMPLEXITY_LEVELS: List[str] = [
    "Semplice",
    "Intermedia",
    "Complessa",
    "Molto complessa",
]

DURATION_OPTIONS: List[int] = [60, 90, 120, 180]

MASTER_MODES: List[str] = [
    "Con master",
    "Senza master",
    "Master interpretato da un personaggio",
]

SUBPLOT_COUNTS: List[str] = [
    "Nessuna",
    "Poche",
    "Medie",
    "Molte",
    "Generazione automatica",
]

NARRATIVE_TONES: List[str] = [
    "Comico",
    "Drammatico",
    "Thriller",
    "Noir",
    "Horror",
    "Grottesco",
    "Elegante",
    "Personalizzato",
]

GAMEPLAY_MODES: List[str] = [
    "Investigazione libera",
    "A fasi",
    "Narrativa guidata",
    "Combinazione di modalità",
]


class StoryConfig(BaseModel):
    """User configuration parameters for generating a Murder Mystery Dinner Game."""

    title_hint: str = Field(default="", description="Optional title or initial theme idea")
    setting_preset: str = Field(default="Villa nobiliare")
    custom_setting: str = Field(default="")
    num_playable_characters: int = Field(default=4, ge=3, le=12)
    num_npcs: int = Field(default=1, ge=0, le=6)
    complexity: str = Field(default="Intermedia")
    duration_minutes: int = Field(default=90, ge=30, le=360)
    master_mode: str = Field(default="Con master")
    subplots_amount: str = Field(default="Medie")
    narrative_tone: str = Field(default="Thriller")
    custom_tone: str = Field(default="")
    gameplay_mode: str = Field(default="A fasi")
    custom_constraints: str = Field(default="")
    language: str = Field(default="Italiano")
    max_review_iterations: int = Field(default=2, ge=1, le=5)

    @property
    def effective_setting(self) -> str:
        if self.setting_preset == "Personalizzata" and self.custom_setting.strip():
            return self.custom_setting.strip()
        if self.custom_setting.strip():
            return f"{self.setting_preset} ({self.custom_setting.strip()})"
        return self.setting_preset

    @property
    def effective_tone(self) -> str:
        if self.narrative_tone == "Personalizzato" and self.custom_tone.strip():
            return self.custom_tone.strip()
        if self.custom_tone.strip():
            return f"{self.narrative_tone} ({self.custom_tone.strip()})"
        return self.narrative_tone

    @property
    def total_characters(self) -> int:
        return self.num_playable_characters + self.num_npcs


class StoryConcept(BaseModel):
    """Output of Agent 1 — Game Director (Phase 1 Concept)."""

    title: str = Field(default="Delitto a Porte Chiuse")
    tagline: str = Field(default="")
    hook: str = Field(default="")
    victim_name: str = Field(default="")
    victim_role: str = Field(default="")
    crime_summary: str = Field(default="")
    atmosphere_directive: str = Field(default="")
    design_pillars: List[str] = Field(default_factory=list)


class LocationItem(BaseModel):
    """Canonical location inside the narrative world."""

    location_id: str = Field(default="loc_01")
    name: str = Field(default="")
    description: str = Field(default="")
    hidden_detail: str = Field(default="")


class WorldState(BaseModel):
    """Output of Agent 2 — World Builder (Phase 2 World Building)."""

    era_and_place: str = Field(default="")
    social_cultural_context: str = Field(default="")
    atmosphere: str = Field(default="")
    backstory: str = Field(default="")
    characteristic_elements: List[str] = Field(default_factory=list)
    locations: List[LocationItem] = Field(default_factory=list)
    world_secrets: List[str] = Field(default_factory=list)
    public_facts: List[str] = Field(default_factory=list)


class SecretSolution(BaseModel):
    """Canonical secret solution defined before clue distribution."""

    victim_name: str = Field(default="")
    culprit_id: str = Field(default="char_01")
    culprit_name: str = Field(default="")
    motive: str = Field(default="")
    murder_weapon: str = Field(default="")
    murder_location: str = Field(default="")
    time_of_death: str = Field(default="")
    opportunity_and_dynamics: str = Field(default="")
    alibi_flaw: str = Field(default="")
    deduction_chain: List[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    """Canonical event in the timeline."""

    event_id: str = Field(default="evt_01")
    timestamp: str = Field(default="20:00")
    title: str = Field(default="")
    description: str = Field(default="")
    involved_character_ids: List[str] = Field(default_factory=list)
    location: str = Field(default="")
    is_public: bool = Field(default=False)
    is_crime_event: bool = Field(default=False)


class MainPlot(BaseModel):
    """Output of Agent 3 — Plot Architect (Phase 3 Plot Design)."""

    crime_overview: str = Field(default="")
    secret_solution: SecretSolution = Field(default_factory=SecretSolution)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    red_herrings: List[str] = Field(default_factory=list)
    alternative_developments: List[str] = Field(default_factory=list)


class CharacterRelationship(BaseModel):
    """Directed relationship between two canonical characters."""

    target_character_id: str = Field(default="char_02")
    target_name: str = Field(default="")
    relation_type: str = Field(default="Conoscente")
    public_view: str = Field(default="")
    hidden_tension: str = Field(default="")


class CharacterProfile(BaseModel):
    """Output item of Agent 4 — Character Designer (Phase 4 Character Design)."""

    character_id: str = Field(default="char_01")
    name: str = Field(default="")
    role: str = Field(default="")
    is_playable: bool = Field(default=True)
    is_culprit: bool = Field(default=False)
    background: str = Field(default="")
    personality: str = Field(default="")
    goals: List[str] = Field(default_factory=list)
    relationships: List[CharacterRelationship] = Field(default_factory=list)
    secret: str = Field(default="")
    alibi: str = Field(default="")
    motive: str = Field(default="")
    known_facts: List[str] = Field(default_factory=list)
    hidden_facts: List[str] = Field(default_factory=list)
    what_can_reveal: str = Field(default="")
    reaction_to_accusation: str = Field(default="")


class SubplotItem(BaseModel):
    """Output item of Agent 5 — Subplot Designer (Phase 5 Subplot Design)."""

    subplot_id: str = Field(default="sub_01")
    title: str = Field(default="")
    category: str = Field(default="Segreto")
    involved_character_ids: List[str] = Field(default_factory=list)
    description: str = Field(default="")
    player_triggers: str = Field(default="")
    resolution: str = Field(default="")
    connects_to_main_plot: str = Field(default="")


class ClueItem(BaseModel):
    """Output item of Agent 6 — Clue Master (Phase 6 Clue Design)."""

    clue_id: str = Field(default="clue_01")
    title: str = Field(default="")
    clue_type: str = Field(default="fisico")
    description: str = Field(default="")
    printable_text: str = Field(default="")
    discovery_phase: int = Field(default=1, ge=1, le=4)
    location_or_holder: str = Field(default="")
    points_to_character_id: Optional[str] = Field(default=None)
    contradicts_alibi_of_id: Optional[str] = Field(default=None)
    is_red_herring: bool = Field(default=False)
    logical_inference: str = Field(default="")


class GamePhase(BaseModel):
    """Single playable phase of the murder mystery dinner."""

    phase_number: int = Field(default=1)
    title: str = Field(default="")
    duration_minutes: int = Field(default=30)
    objectives: List[str] = Field(default_factory=list)
    revealed_clue_ids: List[str] = Field(default_factory=list)
    scheduled_events: List[str] = Field(default_factory=list)
    interrogation_mechanics: str = Field(default="")


class GameplayStructure(BaseModel):
    """Output of Agent 7 — Game Mechanics Designer (Phase 7 Game Design)."""

    phases: List[GamePhase] = Field(default_factory=list)
    information_distribution_rules: str = Field(default="")
    accusation_mechanics: str = Field(default="")
    victory_conditions: str = Field(default="")
    master_notes: str = Field(default="")


class InGameDocument(BaseModel):
    """Printable letter, message, or evidence document produced by Agent 8."""

    doc_id: str = Field(default="doc_01")
    doc_type: str = Field(default="letter")  # letter | message | evidence
    title: str = Field(default="")
    sender: str = Field(default="")
    recipient: str = Field(default="")
    content: str = Field(default="")
    related_clue_id: Optional[str] = Field(default=None)


class NarrativeMaterials(BaseModel):
    """Output of Agent 8 — Narrative Writer (Phase 8 Narrative Production)."""

    introduction_md: str = Field(default="")
    prologue_speech_md: str = Field(default="")
    character_dialogues: Dict[str, List[str]] = Field(default_factory=dict)
    confidential_communications: Dict[str, str] = Field(default_factory=dict)
    documents: List[InGameDocument] = Field(default_factory=list)


class AgentCritique(BaseModel):
    """Single critique item generated by Agent 9 or peer agent review."""

    target_agent: str = Field(default="PlotArchitect")
    issue_type: str = Field(default="timeline_contradiction")
    severity: str = Field(default="major")  # minor | major | critical
    description: str = Field(default="")
    suggested_fix: str = Field(default="")
    affected_ids: List[str] = Field(default_factory=list)
    resolved: bool = Field(default=False)


class ReviewReport(BaseModel):
    """Output of Agent 9 — Continuity Editor / Critical Reviewer (Phase 9)."""

    iteration: int = Field(default=1)
    passed: bool = Field(default=True)
    coherence_score: int = Field(default=85, ge=0, le=100)
    critiques: List[AgentCritique] = Field(default_factory=list)
    summary: str = Field(default="")


class FinalProductionSuite(BaseModel):
    """Output of Agent 10 — Final Game Producer (Phase 10 Finalization)."""

    master_manual_md: str = Field(default="")
    player_instructions_md: str = Field(default="")
    secret_resolution_md: str = Field(default="")
    master_report_md: str = Field(default="")
    complete_story_md: str = Field(default="")


class AgentActivityLog(BaseModel):
    """Observable activity log entry for the Control Room UI."""

    step_index: int = Field(default=1)
    timestamp: str = Field(default_factory=utc_now_iso)
    phase: str = Field(default="")
    agent_name: str = Field(default="")
    action: str = Field(default="")
    status: str = Field(default="completed")  # running | completed | critique | revised | error
    summary: str = Field(default="")
    details: Dict[str, Any] = Field(default_factory=dict)


class MysteryProject(BaseModel):
    """Single Source of Truth representing an entire Murder Mystery project and its Information Graph."""

    project_id: str = Field(default_factory=lambda: f"mm_{uuid.uuid4().hex[:8]}")
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    status: str = Field(default="draft")  # draft | generating | review | completed
    current_phase: str = Field(default="Configurazione")

    config: StoryConfig = Field(default_factory=StoryConfig)
    concept: StoryConcept = Field(default_factory=StoryConcept)
    world: WorldState = Field(default_factory=WorldState)
    plot: MainPlot = Field(default_factory=MainPlot)
    characters: List[CharacterProfile] = Field(default_factory=list)
    subplots: List[SubplotItem] = Field(default_factory=list)
    clues: List[ClueItem] = Field(default_factory=list)
    gameplay: GameplayStructure = Field(default_factory=GameplayStructure)
    narrative: NarrativeMaterials = Field(default_factory=NarrativeMaterials)
    reviews: List[ReviewReport] = Field(default_factory=list)
    final_production: FinalProductionSuite = Field(default_factory=FinalProductionSuite)
    agent_logs: List[AgentActivityLog] = Field(default_factory=list)

    def touch(self) -> None:
        self.updated_at = utc_now_iso()

    def log_activity(
        self,
        phase: str,
        agent_name: str,
        action: str,
        summary: str,
        status: str = "completed",
        details: Optional[Dict[str, Any]] = None,
    ) -> AgentActivityLog:
        entry = AgentActivityLog(
            step_index=len(self.agent_logs) + 1,
            phase=phase,
            agent_name=agent_name,
            action=action,
            status=status,
            summary=summary,
            details=details or {},
        )
        self.agent_logs.append(entry)
        self.current_phase = phase
        self.touch()
        return entry

    def get_character(self, character_id: str) -> Optional[CharacterProfile]:
        for char in self.characters:
            if char.character_id == character_id:
                return char
        return None

    def get_culprit(self) -> Optional[CharacterProfile]:
        culprit_id = self.plot.secret_solution.culprit_id
        for char in self.characters:
            if char.character_id == culprit_id or char.is_culprit:
                return char
        return None
