from __future__ import annotations

import abc
import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set, Tuple

_PRINTED_LOCAL_NOTE = False
_QUANT_CACHE: Dict[Tuple[str, str], Optional[str]] = {}
_WARM_MODELS: Set[Tuple[str, str]] = set()


@dataclass
class LLMResult:
    """Stores the execution result of an LLM completion.

    Attributes:
        text: The model response content string.
        prompt_tokens: Prompt evaluation token count.
        completion_tokens: Completion generation token count.
        latency_ms: Request round-trip execution latency in milliseconds.
        model: Model identifier reported by the engine.
        quantization: Model quantization level reported in engine details, or None.
        cost_usd: Local execution cost (always 0.0 for Ollama local runs; local execution incurrs no API billing).
        warm_run: True if this is a subsequent/warm invocation for the model, False for initial cold load.
    """

    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    model: str
    quantization: Optional[str]
    cost_usd: float = 0.0
    warm_run: bool = False


class LLMClient(abc.ABC):
    @abc.abstractmethod
    def complete(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None) -> LLMResult:
        """Completes a prompt using the underlying LLM."""
        pass


def get_model_quantization(url: str, model: str, timeout: float = 10.0) -> Optional[str]:
    """Retrieves and caches the quantization level for a given model from Ollama /api/show."""
    clean_url = url.rstrip("/")
    cache_key = (clean_url, model)
    if cache_key in _QUANT_CACHE:
        return _QUANT_CACHE[cache_key]

    payload = json.dumps({"model": model}).encode("utf-8")
    req = urllib.request.Request(
        f"{clean_url}/api/show",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise RuntimeError(f"Ollama unreachable at {clean_url}. Start it with `ollama serve`.") from e
    except Exception as e:
        logging.warning("Failed to retrieve model info for '%s' from %s: %s", model, clean_url, e)
        _QUANT_CACHE[cache_key] = None
        return None

    details = data.get("details")
    if isinstance(details, dict) and details.get("quantization_level"):
        quant = str(details["quantization_level"])
        _QUANT_CACHE[cache_key] = quant
        return quant

    logging.warning("Quantization level missing in /api/show for model '%s'", model)
    _QUANT_CACHE[cache_key] = None
    return None


_DIGEST_CACHE: Dict[Tuple[str, str], str] = {}


def get_model_digest(url: str = "http://localhost:11434", model: str = "qwen2.5:7b-instruct", timeout: float = 10.0) -> str:
    """Retrieves and caches the SHA256 digest of the specified model from Ollama /api/tags."""
    clean_url = url.rstrip("/")
    cache_key = (clean_url, model)
    if cache_key in _DIGEST_CACHE:
        return _DIGEST_CACHE[cache_key]

    req = urllib.request.Request(f"{clean_url}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("models", [])
            target = model.strip()
            for m in models:
                if m.get("name") == target:
                    digest = m.get("digest", "")
                    _DIGEST_CACHE[cache_key] = digest
                    return digest
            target_base = target.split(":")[0]
            for m in models:
                m_name = m.get("name", "")
                if m_name.split(":")[0] == target_base:
                    digest = m.get("digest", "")
                    _DIGEST_CACHE[cache_key] = digest
                    return digest
            if models and "digest" in models[0]:
                digest = models[0]["digest"]
                _DIGEST_CACHE[cache_key] = digest
                return digest
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise RuntimeError(f"Ollama unreachable at {clean_url}. Start it with `ollama serve`.") from e
    except Exception as e:
        logging.warning("Failed to retrieve model digest for '%s' from %s: %s", model, clean_url, e)

    return ""


class OllamaClient(LLMClient):
    def __init__(
        self,
        url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
    ) -> None:
        self.url = (url or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
        self.timeout = timeout
        self._call_count: int = 0

        global _PRINTED_LOCAL_NOTE
        if not _PRINTED_LOCAL_NOTE:
            print("Local run via Ollama: cost_usd=0.0 (no API billing).")
            _PRINTED_LOCAL_NOTE = True

    def complete(self, system: str, user: str, schema: Optional[Dict[str, Any]] = None) -> LLMResult:
        is_warm = (self.url, self.model) in _WARM_MODELS or self._call_count > 0

        quantization = get_model_quantization(self.url, self.model, timeout=self.timeout)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0},
        }
        if schema is not None:
            payload["format"] = schema

        body_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.url}/api/chat",
            data=body_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_bytes = resp.read()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
            raise RuntimeError(f"Ollama HTTP error {e.code}: {err_body}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            raise RuntimeError(f"Ollama unreachable at {self.url}. Start it with `ollama serve`.") from e

        latency_ms = (time.perf_counter() - start) * 1000.0

        try:
            data = json.loads(resp_bytes.decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Failed to parse Ollama JSON response: {e}") from e

        if "prompt_eval_count" not in data or "eval_count" not in data:
            raise RuntimeError("Missing token count fields (prompt_eval_count / eval_count) in Ollama response")

        prompt_tokens = int(data["prompt_eval_count"])
        completion_tokens = int(data["eval_count"])

        model_name = data.get("model")
        if not model_name:
            raise RuntimeError("Missing 'model' in Ollama response")

        message = data.get("message")
        if not isinstance(message, dict) or not message.get("content"):
            raise RuntimeError("Empty or missing content in Ollama message response")

        text = message["content"]

        _WARM_MODELS.add((self.url, self.model))
        self._call_count += 1

        return LLMResult(
            text=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            model=model_name,
            quantization=quantization,
            cost_usd=0.0,
            warm_run=is_warm,
        )


def get_ollama_version(url: str = "http://localhost:11434", timeout: float = 10.0) -> str:
    clean_url = url.rstrip("/")
    endpoint = f"{clean_url}/api/version"
    req = urllib.request.Request(endpoint, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return str(data.get("version", ""))
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise RuntimeError(f"Ollama unreachable at {clean_url}. Start it with `ollama serve`.") from e
