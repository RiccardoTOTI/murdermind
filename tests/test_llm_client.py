"""Tests for M1 OpenAI-compatible LLM Core (unit + live local Qwen3.5-2B checks)."""

from __future__ import annotations

import json
import httpx
import pytest
from pydantic import BaseModel

from murdermind.config import LLMConfig, ProviderMode
from murdermind.core.llm_client import (
    LLMClientError,
    OpenAICompatibleClient,
    extract_json_object,
)


class SampleConcept(BaseModel):
    title: str
    victim: str


def test_extract_json_object_handles_fences_and_think_tags() -> None:
    raw = """<think>Let me create the JSON object carefully.</think>
```json
{
  "title": "Murder on the Midnight Express",
  "victim": "Lord Ashworth",
}
```"""
    parsed = extract_json_object(raw)
    assert parsed["title"] == "Murder on the Midnight Express"
    assert parsed["victim"] == "Lord Ashworth"


def test_llm_client_retries_on_malformed_json() -> None:
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            content = "not a json object at all"
        else:
            content = json.dumps({"title": "Villa Segreta", "victim": "Conte Bardi"})
        return httpx.Response(
            200,
            json={
                "model": "unsloth/Qwen3.5-2B",
                "choices": [{"message": {"role": "assistant", "content": content}}],
                "usage": {"prompt_tokens": 15, "completion_tokens": 20},
            },
        )

    transport = httpx.MockTransport(handler)
    cfg = LLMConfig(
        provider=ProviderMode.LOCAL,
        base_url="http://127.0.0.1:8888/v1",
        api_key="test-key",
    )
    client = OpenAICompatibleClient(config=cfg, transport=transport)
    result = client.generate_structured(
        system_prompt="Return JSON.",
        user_prompt="Create a concept.",
        schema_cls=SampleConcept,
    )
    assert result.title == "Villa Segreta"
    assert result.victim == "Conte Bardi"
    assert attempts["count"] == 2
    assert client.call_count == 2


def test_provider_resolution_remote_vs_local() -> None:
    cfg = LLMConfig(
        provider=ProviderMode.REMOTE,
        base_url="http://127.0.0.1:8888/v1",
        api_key="local-key",
        model="unsloth/Qwen3.5-2B",
        remote_base_url="https://router.huggingface.co/v1",
        remote_api_key="remote-key",
        remote_model="Qwen/Qwen2.5-7B-Instruct",
    )
    client = OpenAICompatibleClient(config=cfg)
    base_url, api_key, model = client.resolve_endpoint()
    assert base_url == "https://router.huggingface.co/v1"
    assert api_key == "remote-key"
    assert model == "Qwen/Qwen2.5-7B-Instruct"


def test_live_local_qwen_connection_and_structured_json() -> None:
    client = OpenAICompatibleClient()
    if not client.ping_local():
        pytest.skip("Local LLM endpoint at 127.0.0.1:8888 is not reachable")

    health = client.check_health()
    assert health["ok"] is True
    assert "Qwen" in health["model"] or "unsloth" in health["model"]

    concept = client.generate_structured(
        system_prompt="You are a mystery writer. Reply ONLY with a JSON object containing 'title' and 'victim'.",
        user_prompt="Create a short title and victim name for an Italian villa murder mystery.",
        schema_cls=SampleConcept,
        temperature=0.3,
        max_tokens=128,
    )
    assert len(concept.title.strip()) > 0
    assert len(concept.victim.strip()) > 0
