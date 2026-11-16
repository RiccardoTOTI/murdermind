"""SQLite persistence service for saving, loading, and listing MysteryProjects."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from murdermind.schemas.mystery import MysteryProject


class ProjectStorage:
    """SQLite-backed store for MysteryProject instances."""

    def __init__(self, db_path: str | Path = "data/murdermind.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mystery_projects (
                    project_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    setting TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save(self, project: MysteryProject) -> None:
        """Insert or update a MysteryProject in SQLite."""
        project.touch()
        payload = project.model_dump_json(indent=2)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO mystery_projects (
                    project_id, title, setting, status, created_at, updated_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    title = excluded.title,
                    setting = excluded.setting,
                    status = excluded.status,
                    updated_at = excluded.updated_at,
                    payload_json = excluded.payload_json
                """,
                (
                    project.project_id,
                    project.concept.title,
                    project.config.effective_setting,
                    project.status,
                    project.created_at,
                    project.updated_at,
                    payload,
                ),
            )
            conn.commit()

    def load(self, project_id: str) -> Optional[MysteryProject]:
        """Load a MysteryProject by its project_id."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM mystery_projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        if not row:
            return None
        return MysteryProject.model_validate_json(row["payload_json"])

    def list_projects(self) -> List[Dict[str, str]]:
        """Return compact metadata for all saved projects ordered by updated_at DESC."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT project_id, title, setting, status, created_at, updated_at
                FROM mystery_projects
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def delete(self, project_id: str) -> bool:
        """Delete a project by ID."""
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM mystery_projects WHERE project_id = ?",
                (project_id,),
            )
            conn.commit()
            return cur.rowcount > 0
