"""Tests for M4/M6 Web UI construction and full 10-agent live Qwen3.5-2B generation."""

from __future__ import annotations

from pathlib import Path
import gradio as gr
import pytest

from murdermind.core.graph_validator import InformationGraphValidator
from murdermind.core.llm_client import OpenAICompatibleClient
from murdermind.core.orchestrator import MurderMysteryOrchestrator
from murdermind.schemas.mystery import StoryConfig
from murdermind.services.exporter import DossierExporter
from murdermind.ui.studio_app import build_studio_ui, render_agent_board_md


def test_gradio_studio_ui_builds_cleanly() -> None:
    app = build_studio_ui()
    assert isinstance(app, gr.Blocks)


def test_live_qwen_full_10_agents_and_export(tmp_path: Path) -> None:
    client = OpenAICompatibleClient()
    if not client.ping_local():
        pytest.skip("Local LLM endpoint at 127.0.0.1:8888 is not reachable")

    orchestrator = MurderMysteryOrchestrator(llm_client=client)
    config = StoryConfig(
        title_hint="Delitto al Grand Hotel Excelsior",
        setting_preset="Hotel",
        custom_setting="Grand Hotel sulle Dolomiti isolato da una tormenta",
        num_playable_characters=3,
        num_npcs=1,
        complexity="Intermedia",
        duration_minutes=90,
        subplots_amount="Poche",
        narrative_tone="Thriller",
        max_review_iterations=1,
    )
    project = orchestrator.create_project(config)
    project = orchestrator.run_full_pipeline(project)

    assert project.status == "completed"
    assert len(project.characters) == 4
    assert len(project.clues) >= 4
    assert len(project.subplots) >= 2
    assert len(project.gameplay.phases) == 3
    assert len(project.final_production.master_manual_md) > 100

    # Verify zero graph consistency errors
    issues = InformationGraphValidator.validate_full_graph(project)
    assert issues == []

    # Verify board rendering and exports
    board = render_agent_board_md(project)
    assert "AGENT 10" in board

    zip_path = DossierExporter.export_zip(project, tmp_path / "live_qwen_bundle.zip")
    assert zip_path.exists()

    # Also save into examples/qwen_generated_mystery so the repo showcases a real Qwen3.5-2B run
    example_out = Path("examples/qwen_generated_mystery")
    DossierExporter.write_dossier_directory(project, example_out)
    assert (example_out / "murder_mystery" / "project.json").exists()
