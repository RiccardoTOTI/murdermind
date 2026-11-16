# MurderMind Technical Architecture

## 1. Overview

**MurderMind** is a multi-agent narrative design engine built to create playable, logically solvable **Murder Mystery Dinner Games** (*Cene con Delitto*) using compact local language models (`unsloth/Qwen3.5-2B`) as well as remote OpenAI-compatible providers for cloud/Hugging Face Spaces deployment.

```
+-------------------------------------------------------------------------+
|                        Web UI (Gradio Studio)                           |
|  [1. Studio Creativo]    [2. Control Room]    [3. Game Dossier & Export] |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                Game Director / Multi-Agent Orchestrator                 |
|  - Stepwise workflow execution (Phases 1..10)                           |
|  - Targeted inter-agent review & revision cycles (bounded iterations)   |
|  - Observable event & critique stream                                   |
+-----------------+------------------+------------------+-----------------+
                  |                  |                  |
                  v                  v                  v
     +--------------------+ +------------------+ +-------------------+
     | 10 Modular Agents  | | Single Source of | |  Graph Validator  |
     | (Independent       | | Truth (Pydantic  | | - Timeline order  |
     |  modules + prompts)| | InformationGraph)| | - Alibi/Clue link |
     +---------+----------+ +--------+---------+ | - Secret firewall |
               |                     |           +-------------------+
               v                     v
     +--------------------+ +------------------+
     | OpenAI-Compatible  | | Persistence &    |
     | LLM Client Core    | | Dossier Exporter |
     | - Local: :8888     | | - SQLite DB      |
     | - Remote: HF/API   | | - MD/JSON/PDF/ZIP|
     +--------------------+ +------------------+
```

## 2. Four Core Design Principles

1. **Compact-Model Multi-Agent Collaboration (`Qwen3.5-2B` Friendly)**
   Agents are not 10 unconstrained free-text calls. Each agent has a bounded responsibility, a focused system prompt, a compact slice of shared context, and a structured JSON contract validated by Pydantic.
2. **Story as an Information Graph (Single Source of Truth)**
   Characters (`char_01`...), clues (`clue_01`...), timeline events (`evt_01`...), secrets, and subplots (`sub_01`...) are linked by canonical IDs inside `MysteryProject`. Automated graph validation verifies that:
   - The secret solution is established before clues are distributed.
   - Every clue and subplot references valid character IDs.
   - At least one non-red-herring clue exposes the culprit's alibi contradiction or links them to the crime.
3. **Strict Information Firewall (Master vs. Player Views)**
   The exporter and view builders enforce a strict separation between Master material (`secret_solution.md`, `master_manual.md`, `master_report.md`) and Player character sheets (`characters/character_XX.md`). A player sheet never leaks `secret_solution`, `culprit_id`, or another character's hidden secrets.
4. **Observable Creative Process**
   Every agent execution, inter-agent critique, and targeted revision is recorded as an `AgentActivityEvent` and `ReviewCritique` inside the project state and surfaced in the Control Room UI.

## 3. LLM Provider Abstraction

`murdermind/core/llm_client.py` separates inference configuration by environment:
- **Local Development (`LLM_PROVIDER=local`)**: Connects to `http://127.0.0.1:8888/v1/chat/completions` running `unsloth/Qwen3.5-2B`.
- **Remote Deployment (`LLM_PROVIDER=remote` or `auto`)**: Connects to a remote OpenAI-compatible endpoint (such as Hugging Face Inference Router `https://router.huggingface.co/v1` or OpenRouter/OpenAI) when hosted on Hugging Face Spaces, since a cloud Space cannot access the developer's `127.0.0.1`.
