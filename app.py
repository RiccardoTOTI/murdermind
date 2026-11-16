"""Main entrypoint for MurderMind Studio (Local & Hugging Face Spaces Gradio App)."""

from __future__ import annotations

import os
from murdermind.ui.studio_app import build_studio_ui

demo = build_studio_ui()

if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("GRADIO_SERVER_PORT", "7860")))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        mcp_server=True,
    )
