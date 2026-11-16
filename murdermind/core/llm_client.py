"""OpenAI-compatible LLM Client with local/remote provider resolution and JSON repair."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from murdermind.config import LLMConfig, ProviderMode

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Global optional callback registered by app.py on Hugging Face ZeroGPU Spaces
_ZEROGPU_GENERATE_FN: Optional[Callable[[List[Dict[str, str]], float, int], str]] = None


def register_zerogpu_generator(
    fn: Callable[[List[Dict[str, str]], float, int], str],
) -> None:
    """Register an in-process ZeroGPU transformers generation callable."""
    global _ZEROGPU_GENERATE_FN
    _ZEROGPU_GENERATE_FN = fn


def get_zerogpu_generator() -> Optional[Callable[[List[Dict[str, str]], float, int], str]]:
    """Return the registered ZeroGPU generation callable if available."""
    return _ZEROGPU_GENERATE_FN


class LLMClientError(Exception):
    """Raised when the LLM endpoint fails or returns an unrecoverable response."""


def _salvage_json_fields(text: str) -> Dict[str, Any]:
    """Fallback parser that extracts top-level JSON key/value pairs when a 2B model emits unescaped quotes or truncates."""
    result: Dict[str, Any] = {}
    # Extract string fields: "key": "value"
    for match in re.finditer(
        r'"([a-zA-Z0-9_]+)"\s*:\s*"((?:[^"\\]|\\.)*)"', text, flags=re.DOTALL
    ):
        key, val = match.group(1), match.group(2)
        if key not in result:
            result[key] = val.replace('\\"', '"').replace("\\n", "\n").strip()

    # Extract boolean/integer fields: "key": true/false/123
    for match in re.finditer(
        r'"([a-zA-Z0-9_]+)"\s*:\s*(true|false|\d+)', text, flags=re.IGNORECASE
    ):
        key, raw_val = match.group(1), match.group(2).lower()
        if key not in result:
            if raw_val == "true":
                result[key] = True
            elif raw_val == "false":
                result[key] = False
            else:
                result[key] = int(raw_val)

    # Extract simple string lists: "key": ["a", "b"]
    for match in re.finditer(
        r'"([a-zA-Z0-9_]+)"\s*:\s*\[([^\[\]]*)\]', text, flags=re.DOTALL
    ):
        key, body = match.group(1), match.group(2)
        items = [
            m.group(1).strip()
            for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', body)
            if m.group(1).strip()
        ]
        if items and key not in result:
            result[key] = items

    return result


def extract_json_object(raw_text: str, allow_salvage: bool = False) -> Dict[str, Any]:
    """Extract and parse a JSON object from model output, handling think tags, fences, and 2B formatting quirks."""
    if not raw_text or not raw_text.strip():
        raise LLMClientError("Model returned empty content.")

    cleaned = raw_text.strip()
    # Remove <think>...</think> blocks if present
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()

    # Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    else:
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace : last_brace + 1]
        elif first_brace != -1:
            cleaned = cleaned[first_brace:]

    # Attempt direct parse
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        raise LLMClientError(f"Expected JSON object (dict), got {type(parsed).__name__}")
    except json.JSONDecodeError:
        pass

    # Repair common small-model formatting glitches:
    # 1. Trailing commas before } or ]
    repaired = re.sub(r",\s*([}\]])", r"\1", cleaned)
    # 2. Missing comma between adjacent string/bool/number/object/array lines
    repaired = re.sub(r'(["\d\}\]])\s*\n(\s*"[a-zA-Z0-9_]+"s*:)', r"\1,\n\2", repaired)
    try:
        parsed = json.loads(repaired)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError as exc:
        if allow_salvage:
            salvaged = _salvage_json_fields(cleaned)
            if salvaged:
                return salvaged
        raise LLMClientError(
            f"Malformed JSON from LLM: {exc.msg} | Snippet: {cleaned[:300]}"
        ) from exc

    raise LLMClientError("Could not extract a JSON dictionary from LLM response.")


class OpenAICompatibleClient:
    """Single-instance client for local (127.0.0.1:8888) or remote OpenAI-compatible LLMs."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.config = config or LLMConfig.from_env()
        self._transport = transport
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.call_count: int = 0

    def resolve_endpoint(self) -> tuple[str, str, str]:
        """Return (base_url, api_key, model) based on configured provider mode."""
        if self.config.provider == ProviderMode.ZEROGPU:
            return ("zerogpu://in-process", "", self.config.zerogpu_model)
        if self.config.provider == ProviderMode.REMOTE:
            return (
                self.config.remote_base_url,
                self.config.remote_api_key,
                self.config.remote_model,
            )
        if self.config.provider == ProviderMode.AUTO:
            if self.ping_local():
                return (self.config.base_url, self.config.api_key, self.config.model)
            if _ZEROGPU_GENERATE_FN is not None:
                return ("zerogpu://in-process", "", self.config.zerogpu_model)
            if self.config.remote_api_key:
                return (
                    self.config.remote_base_url,
                    self.config.remote_api_key,
                    self.config.remote_model,
                )
        return (self.config.base_url, self.config.api_key, self.config.model)

    def ping_local(self, timeout: float = 3.0) -> bool:
        """Check whether the local LLM endpoint responds."""
        url = f"{self.config.base_url}/models"
        headers: Dict[str, str] = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        try:
            with httpx.Client(timeout=timeout, transport=self._transport) as client:
                resp = client.get(url, headers=headers)
                return resp.status_code in (200, 401)
        except httpx.HTTPError:
            return False

    def check_health(self) -> Dict[str, Any]:
        """Verify connectivity and authentication with the active LLM endpoint."""
        base_url, api_key, model = self.resolve_endpoint()
        if base_url == "zerogpu://in-process":
            if _ZEROGPU_GENERATE_FN is not None:
                return {
                    "ok": True,
                    "provider": "zerogpu",
                    "base_url": "ZeroGPU (NVIDIA RTX PRO 6000 48GB)",
                    "model": model,
                    "reply": "ZeroGPU Ready",
                }
            return {
                "ok": False,
                "provider": "zerogpu",
                "base_url": "zerogpu://in-process",
                "model": model,
                "error": "ZeroGPU non è attivo in questo processo locale (usa 'local' per 127.0.0.1:8888).",
            }

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            with httpx.Client(timeout=10.0, transport=self._transport) as client:
                resp = client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Reply with OK"}],
                        "max_tokens": 8,
                        "temperature": 0.0,
                        "stream": False,
                    },
                )
            if resp.status_code != 200:
                return {
                    "ok": False,
                    "provider": self.config.provider.value,
                    "base_url": base_url,
                    "model": model,
                    "status_code": resp.status_code,
                    "error": resp.text[:300],
                }
            data = resp.json()
            reply = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return {
                "ok": True,
                "provider": self.config.provider.value,
                "base_url": base_url,
                "model": data.get("model", model),
                "reply": reply,
            }
        except Exception as exc:
            return {
                "ok": False,
                "provider": self.config.provider.value,
                "base_url": base_url,
                "model": model,
                "error": str(exc),
            }

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """Send a synchronous chat completion request to the configured OpenAI-compatible server or ZeroGPU worker."""
        base_url, api_key, model = self.resolve_endpoint()
        eff_temp = self.config.temperature if temperature is None else temperature
        eff_tokens = self.config.max_tokens if max_tokens is None else max_tokens

        if base_url == "zerogpu://in-process":
            if _ZEROGPU_GENERATE_FN is None:
                raise LLMClientError(
                    "Modalità ZeroGPU selezionata ma nessun modello ZeroGPU è caricato in memoria. "
                    "In locale seleziona 'local' (http://127.0.0.1:8888/v1)."
                )
            self.call_count += 1
            return _ZEROGPU_GENERATE_FN(messages, eff_temp, eff_tokens)

        url = f"{base_url}/chat/completions"

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": eff_temp,
            "max_tokens": eff_tokens,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(
                timeout=self.config.timeout, transport=self._transport
            ) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise LLMClientError(
                f"LLM request timed out after {self.config.timeout}s ({url})"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMClientError(f"HTTP connection error calling {url}: {exc}") from exc

        if response.status_code != 200:
            raise LLMClientError(
                f"LLM endpoint returned HTTP {response.status_code}: {response.text[:400]}"
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise LLMClientError(
                f"Non-JSON HTTP body from LLM endpoint: {response.text[:300]}"
            ) from exc

        usage = body.get("usage") or {}
        self.total_prompt_tokens += int(usage.get("prompt_tokens", 0))
        self.total_completion_tokens += int(usage.get("completion_tokens", 0))
        self.call_count += 1

        choices = body.get("choices")
        if not choices or not isinstance(choices, list):
            raise LLMClientError(f"Missing 'choices' in LLM response: {body}")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise LLMClientError(f"Missing string 'content' in LLM choice: {choices[0]}")

        return content

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 2,
        normalizer: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate and parse a JSON dictionary, retrying with error feedback if malformed."""
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_error: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            raw = self.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=True,
            )
            try:
                data = extract_json_object(raw)
                if normalizer is not None:
                    data = normalizer(data)
                return data
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "JSON extraction failed on attempt %d/%d: %s",
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous output was not valid JSON ({exc}). "
                            "Reply ONLY with a valid JSON object matching the requested keys."
                        ),
                    }
                )

        raise LLMClientError(
            f"Failed to obtain valid JSON after {max_retries + 1} attempts: {last_error}"
        )

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_cls: Type[T],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 2,
        normalizer: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> T:
        """Generate a response validated against a Pydantic schema class."""
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_error: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            raw = self.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=True,
            )
            try:
                data = extract_json_object(
                    raw, allow_salvage=(attempt == max_retries and normalizer is not None)
                )
                if normalizer is not None:
                    data = normalizer(data)
                return schema_cls.model_validate(data)
            except (LLMClientError, ValidationError) as exc:
                last_error = exc
                logger.warning(
                    "Schema validation failed for %s on attempt %d/%d: %s",
                    schema_cls.__name__,
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Validation error: {exc}. "
                            "Fix the JSON fields and return ONLY the corrected JSON object."
                        ),
                    }
                )

        raise LLMClientError(
            f"Failed to validate {schema_cls.__name__} after {max_retries + 1} attempts: {last_error}"
        )
