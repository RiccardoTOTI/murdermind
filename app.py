"""Main entrypoint for MurderMind Studio (Local & Hugging Face ZeroGPU Spaces App)."""

from __future__ import annotations

import os
from typing import Dict, List

# Rule 1 for ZeroGPU: import spaces BEFORE torch / transformers
try:
    import spaces  # type: ignore
    GPU_DECORATOR = spaces.GPU
except ImportError:
    def _fallback_gpu(duration: int = 60):
        def _wrap(fn):
            return fn
        return _wrap
    GPU_DECORATOR = _fallback_gpu

from murdermind.core.llm_client import register_zerogpu_generator
from murdermind.ui.studio_app import build_studio_ui

# Rule 2 for ZeroGPU: Load the model at module scope and move `.to("cuda")` eagerly when on HF Spaces
ZEROGPU_MODEL_ID = os.getenv("ZEROGPU_MODEL", "Qwen/Qwen2.5-3B-Instruct")

if os.getenv("SPACES_ZERO_GPU") == "1" or os.getenv("SPACE_ID"):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"[MurderMind ZeroGPU] Loading {ZEROGPU_MODEL_ID} at module scope...")
    _tokenizer = AutoTokenizer.from_pretrained(ZEROGPU_MODEL_ID)
    _model = AutoModelForCausalLM.from_pretrained(
        ZEROGPU_MODEL_ID,
        torch_dtype=torch.bfloat16,
    ).to("cuda")
    _model.eval()

    def _zerogpu_generate(
        messages: List[Dict[str, str]], temperature: float, max_tokens: int
    ) -> str:
        prompt_text = _tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = _tokenizer([prompt_text], return_tensors="pt").to("cuda")
        do_sample = temperature > 0.05
        gen_kwargs = {
            "max_new_tokens": min(int(max_tokens), 1024),
            "do_sample": do_sample,
            "pad_token_id": _tokenizer.eos_token_id,
        }
        if do_sample:
            gen_kwargs["temperature"] = max(0.1, float(temperature))
            gen_kwargs["top_p"] = 0.9

        with torch.no_grad():
            generated_ids = _model.generate(**inputs, **gen_kwargs)
        new_tokens = generated_ids[0][inputs.input_ids.shape[1] :]
        return _tokenizer.decode(new_tokens.cpu(), skip_special_tokens=True)

    register_zerogpu_generator(_zerogpu_generate)

demo = build_studio_ui(gpu_decorator=GPU_DECORATOR)

if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("GRADIO_SERVER_PORT", "7860")))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        mcp_server=True,
    )
