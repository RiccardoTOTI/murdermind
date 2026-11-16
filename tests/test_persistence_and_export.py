"""Tests for M5 SQLite persistence, canonical dossier structure, secret separation firewall, and PDF/ZIP exports."""

from __future__ import annotations

import zipfile
from pathlib import Path

from murdermind.core.graph_validator import InformationGraphValidator
from murdermind.services.demo_preset import build_demo_mystery_project
from murdermind.services.exporter import DossierExporter
from murdermind.services.storage import ProjectStorage


def test_sqlite_persistence_roundtrip(tmp_path: Path) -> None:
    db_file = tmp_path / "test_murdermind.db"
    storage = ProjectStorage(db_path=db_file)
    demo = build_demo_mystery_project()

    storage.save(demo)
    listed = storage.list_projects()
    assert len(listed) == 1
    assert listed[0]["project_id"] == demo.project_id
    assert listed[0]["title"] == demo.concept.title

    loaded = storage.load(demo.project_id)
    assert loaded is not None
    assert loaded.concept.title == demo.concept.title
    assert len(loaded.characters) == 5
    assert loaded.plot.secret_solution.culprit_id == "char_02"


def test_strict_information_firewall_on_player_sheets() -> None:
    demo = build_demo_mystery_project()
    for char in demo.characters:
        sheet_md = DossierExporter.render_character_sheet_md(demo, char)
        violations = InformationGraphValidator.check_player_sheet_firewall(
            demo, char.character_id, sheet_md
        )
        assert violations == [], f"Firewall violation for {char.character_id}: {violations}"

        # Innocent player sheets must never state who the culprit is
        if not char.is_culprit:
            assert "SEI TU L'AUTORE DEL DELITTO" not in sheet_md
            assert "SOLUZIONE SEGRETA DEL MASTER" not in sheet_md


def test_dossier_directory_pdf_and_zip_exports(tmp_path: Path) -> None:
    demo = build_demo_mystery_project()

    # 1. Verify virtual dossier files match required directory tree
    files = DossierExporter.build_dossier_files(demo)
    expected_paths = [
        "murder_mystery/project.json",
        "murder_mystery/concept.md",
        "murder_mystery/world/setting.md",
        "murder_mystery/world/background.md",
        "murder_mystery/plot/main_plot.md",
        "murder_mystery/plot/timeline.json",
        "murder_mystery/plot/secret_solution.md",
        "murder_mystery/characters/character_01.md",
        "murder_mystery/characters/character_02.md",
        "murder_mystery/subplots/subplot_01.md",
        "murder_mystery/clues/clues.json",
        "murder_mystery/clues/printable_clues/clue_01.md",
        "murder_mystery/gameplay/master_manual.md",
        "murder_mystery/gameplay/player_instructions.md",
        "murder_mystery/gameplay/game_phases.md",
        "murder_mystery/documents/letters/doc_01.md",
        "murder_mystery/documents/messages/doc_02.md",
        "murder_mystery/documents/evidence/doc_03.md",
        "murder_mystery/final/complete_story.md",
        "murder_mystery/final/master_report.md",
        "murder_mystery/final/resolution.md",
    ]
    for path in expected_paths:
        assert path in files, f"Missing expected dossier file: {path}"
        assert len(files[path].strip()) > 20

    # 2. Write directory tree
    dossier_dir = DossierExporter.write_dossier_directory(demo, tmp_path / "export_dir")
    assert (dossier_dir / "project.json").exists()
    assert (dossier_dir / "characters" / "character_01.md").exists()

    # 3. Export printable PDF
    pdf_path = DossierExporter.export_pdf(demo, tmp_path / "dossier.pdf")
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000
    assert pdf_path.read_bytes()[:4] == b"%PDF"

    # 4. Export complete ZIP archive
    zip_path = DossierExporter.export_zip(demo, tmp_path / "murder_mystery_bundle.zip")
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
        assert "murder_mystery/project.json" in names
        assert "murder_mystery/final/printable_dossier.pdf" in names
        assert "murder_mystery/characters/character_01.md" in names
