# Contributing to MurderMind

Thank you for your interest in contributing to **MurderMind — Murder Mystery Multi-Agent Studio**!

## Why MIT License?
MurderMind is released under the **MIT License** to maximize adoption, remixing, and educational use across narrative designers, tabletop RPG communities, and AI engineering researchers working with compact local models (such as `unsloth/Qwen3.5-2B`).

## Development Setup

1. Clone the repository and configure a Python 3.10+ environment.
2. Copy `.env.example` to `.env` and set your `LLM_API_KEY`:
   ```bash
   cp .env.example .env
   ```
   **Never commit `.env` or real API keys to Git.**
3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Ensure your local OpenAI-compatible server is running on `http://127.0.0.1:8888/v1` with `unsloth/Qwen3.5-2B` (or configure `REMOTE_LLM_*` variables).
5. Run the test suite:
   ```bash
   pytest -v
   ```

## Adding or Modifying an Agent

- Each agent lives in its own module under `murdermind/agents/`.
- System prompts are separated under `murdermind/prompts/`.
- Keep prompts concise and outputs strictly typed via Pydantic models in `murdermind/schemas/` so small 2B-parameter models produce reliable JSON.
- All canonical story mutations must flow through the Single Source of Truth (`MysteryProject`) and pass `InformationGraphValidator`.
