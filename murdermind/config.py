"""Environment-aware configuration for MurderMind."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env from project root if present
load_dotenv(override=False)


class ProviderMode(str, Enum):
    LOCAL = "local"
    ZEROGPU = "zerogpu"
    REMOTE = "remote"
    AUTO = "auto"


class LLMConfig(BaseModel):
    """Configuration for an OpenAI-compatible or ZeroGPU LLM endpoint."""

    provider: ProviderMode = Field(default=ProviderMode.LOCAL)
    base_url: str = Field(default="http://127.0.0.1:8888/v1")
    api_key: str = Field(default="")
    model: str = Field(default="unsloth/Qwen3.5-2B")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=64, le=16384)
    timeout: float = Field(default=120.0, ge=5.0, le=600.0)

    # ZeroGPU in-process model id (used on Hugging Face Spaces with zero-a10g)
    zerogpu_model: str = Field(default="Qwen/Qwen2.5-3B-Instruct")

    # Remote provider settings (used when provider == REMOTE or AUTO fallback)
    remote_base_url: str = Field(default="https://router.huggingface.co/v1")
    remote_api_key: str = Field(default="")
    remote_model: str = Field(default="Qwen/Qwen2.5-7B-Instruct")

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider_raw = os.getenv("LLM_PROVIDER", "").strip().lower()
        # On Hugging Face Spaces, SPACE_ID or SPACES_ZERO_GPU is set automatically
        if not provider_raw:
            if os.getenv("SPACES_ZERO_GPU") == "1" or os.getenv("SPACE_ID"):
                provider_raw = "zerogpu"
            else:
                provider_raw = "local"

        try:
            provider = ProviderMode(provider_raw)
        except ValueError:
            provider = ProviderMode.LOCAL

        remote_key = (
            os.getenv("REMOTE_LLM_API_KEY")
            or os.getenv("HF_TOKEN")
            or os.getenv("OPENAI_API_KEY")
            or ""
        )

        return cls(
            provider=provider,
            base_url=os.getenv("LLM_BASE_URL", "http://127.0.0.1:8888/v1").rstrip("/"),
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", "unsloth/Qwen3.5-2B"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            timeout=float(os.getenv("LLM_TIMEOUT", "120")),
            zerogpu_model=os.getenv("ZEROGPU_MODEL", "Qwen/Qwen2.5-3B-Instruct"),
            remote_base_url=os.getenv(
                "REMOTE_LLM_BASE_URL", "https://router.huggingface.co/v1"
            ).rstrip("/"),
            remote_api_key=remote_key,
            remote_model=os.getenv("REMOTE_LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        )


class AppSettings(BaseModel):
    """Global application settings."""

    llm: LLMConfig = Field(default_factory=LLMConfig.from_env)
    db_path: Path = Field(
        default_factory=lambda: Path(os.getenv("MURDERMIND_DB_PATH", "data/murdermind.db"))
    )
    output_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("MURDERMIND_OUTPUT_DIR", "data/output"))
    )
    max_review_iterations: int = Field(
        default_factory=lambda: int(os.getenv("MURDERMIND_MAX_REVIEW_ITERATIONS", "2"))
    )
