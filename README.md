---
title: MurderMind Multi-Agent Mystery Studio
emoji: 🕵️‍♀️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.32.0
app_file: app.py
short_description: Multi-Agent Studio for Murder Mystery Dinner Games
python_version: "3.12"
startup_duration_timeout: 30m
---

# 🕵️‍♀️ MurderMind — Murder Mystery Multi-Agent Studio

**MurderMind** is an open-source **Multi-Agent Narrative Design Platform** for creating, validating, and exporting playable **Murder Mystery Dinner Games** (*Cene con Delitto*).

Instead of generating a single monolithic story, MurderMind coordinates **10 specialized AI agents** over a shared **Information Graph (Single Source of Truth)**—complete with iterative peer/critical review cycles, alibi-contradiction checks, strict Master/Player secret separation, and multi-format export (`Markdown`, `JSON`, printable `PDF`, and full `ZIP` dossier).

---

## ✨ Key Architectural Principles

1. **Compact-Model Multi-Agent Collaboration (`unsloth/Qwen3.5-2B` Ready)**
   Each agent has a bounded role, a concise system prompt (`murdermind/prompts/`), and a Pydantic-validated JSON output schema (`murdermind/schemas/`). An explicit orchestrator (`MurderMysteryOrchestrator`) routes context and targeted revisions without bloated framework overhead.
2. **Story as an Information Graph (`Single Source of Truth`)**
   Characters (`char_01`..), timeline events (`evt_01`..), subplots (`sub_01`..), and clues (`clue_01`..) are linked by canonical IDs and verified by `InformationGraphValidator` so every mystery has a provably deducible solution.
3. **Strict Information Firewall (Master vs. Players)**
   Individual player sheets (`characters/character_XX.md`) never expose the Master's secret solution or other characters' private secrets.
4. **Observable Creative Process**
   The Web UI's **Control Room** displays the status of all 10 agents, chronological activity logs, `ContinuityEditor` critiques, and lets you regenerate any individual phase.

---

## 🤖 The 10 Collaborative Agents

| Agent | Module | Phase & Responsibility |
| :--- | :--- | :--- |
| **AGENT 1 – Game Director** | `murdermind/agents/game_director.py` | **Phase 1 – Concept**: Translates user parameters into title, hook, victim, and creative pillars. |
| **AGENT 2 – World Builder** | `murdermind/agents/world_builder.py` | **Phase 2 – World Building**: Designs historical/contemporary setting, locations, atmosphere, and world secrets. |
| **AGENT 3 – Plot Architect** | `murdermind/agents/plot_architect.py` | **Phase 3 – Plot Design**: Defines the canonical culprit, motive, murder weapon, alibi flaw, timeline, and red herrings. |
| **AGENT 4 – Character Designer** | `murdermind/agents/character_designer.py` | **Phase 4 – Character Design**: Creates playable characters and NPCs with goals, relationships, alibis, and secrets. |
| **AGENT 5 – Subplot Designer** | `murdermind/agents/subplot_designer.py` | **Phase 5 – Subplot Design**: Weaves blackmail, rivalries, romances, and financial secrets across the cast. |
| **AGENT 6 – Clue Master** | `murdermind/agents/clue_master.py` | **Phase 6 – Clue Design**: Builds physical, documentary, testimonial, and red-herring clues guaranteeing logical solvability. |
| **AGENT 7 – Game Mechanics Designer** | `murdermind/agents/game_mechanics.py` | **Phase 7 – Game Design**: Structures playable phases, interrogation rules, accusation mechanics, and victory conditions. |
| **AGENT 8 – Narrative Writer** | `murdermind/agents/narrative_writer.py` | **Phase 8 – Narrative Production**: Writes public introductions, prologue speech, suggested dialogues, and in-game documents. |
| **AGENT 9 – Continuity Editor** | `murdermind/agents/continuity_editor.py` | **Phase 9 – Critical Review**: Combines deterministic graph checks with LLM critique and triggers targeted revisions. |
| **AGENT 10 – Final Game Producer** | `murdermind/agents/final_producer.py` | **Phase 10 – Finalization**: Produces the Master Manual, Player Instructions, Secret Resolution, and Master Report. |

---

## 🚀 Quick Start (Local Development with `unsloth/Qwen3.5-2B`)

1. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   Set your `LLM_API_KEY` in `.env` (pointing to `http://127.0.0.1:8888/v1` and model `unsloth/Qwen3.5-2B`).
2. **Install Dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
3. **Run Automated Tests**:
   ```bash
   pytest -v
   ```
4. **Launch the Web Studio**:
   ```bash
   python app.py
   ```

---

## ☁️ Hugging Face Spaces Deployment

Because a remote Hugging Face Space cannot reach `127.0.0.1:8888` on a developer's machine, `murdermind/config.py` and `OpenAICompatibleClient` support three provider modes:
- `local`: Uses `http://127.0.0.1:8888/v1` (`unsloth/Qwen3.5-2B`) for local development.
- `remote`: Uses a remote OpenAI-compatible endpoint (`REMOTE_LLM_BASE_URL`, `REMOTE_LLM_API_KEY` / `HF_TOKEN`, `REMOTE_LLM_MODEL`).
- `auto`: Automatically uses `local` if reachable, or falls back to `remote` on Hugging Face Spaces while pre-loading the full playable Demo Mystery (*"L'Ultimo Brindisi a Villa Morosini"*).

---

## 📂 Output Dossier Structure

Every generated mystery exports into the canonical structure:

```text
murder_mystery/
    project.json
    concept.md
    world/
        setting.md
        background.md
    plot/
        main_plot.md
        timeline.json
        secret_solution.md
    characters/
        character_01.md
        character_02.md
        ...
    subplots/
        subplot_01.md
        ...
    clues/
        clues.json
        printable_clues/
    gameplay/
        master_manual.md
        player_instructions.md
        game_phases.md
    documents/
        letters/
        messages/
        evidence/
    final/
        complete_story.md
        master_report.md
        resolution.md
        printable_dossier.pdf
```

A complete pre-generated dossier is available in [`examples/demo_villa_morosini/murder_mystery/`](./examples/demo_villa_morosini/murder_mystery/).

---

## 🗺️ Development Roadmap Status

- [x] **M0 – Environment**: HF Spaces conventions, local `:8888` verification, repository structure, `.env.example`, MIT license.
- [x] **M1 – LLM Core**: OpenAI-compatible client, `unsloth/Qwen3.5-2B` verification, JSON repair & salvage, local/remote provider switching.
- [x] **M2 – Multi-Agent Engine (MVP)**: Single Source of Truth, Orchestrator, 3-agent collaborative MVP + iterative review cycle.
- [x] **M3 – Narrative Engine (Full 10 Agents)**: All 10 specialized agents + `InformationGraphValidator`.
- [x] **M4 – User Interface**: 3-Area Gradio Web Studio (Creative Studio, Control Room, Game Dossier & Editor).
- [x] **M5 – Game Production**: SQLite persistence, strict Master/Player secret separation, Markdown/JSON/PDF/ZIP exporters, complete Demo Mystery.
- [x] **M6 – Hugging Face Space**: Ready-to-deploy `app.py`, `requirements.txt`, and `README.md` frontmatter.

## 📄 License

Released under the [MIT License](./LICENSE). See [CONTRIBUTING.md](./CONTRIBUTING.md) and [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).
