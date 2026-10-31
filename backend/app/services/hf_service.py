import asyncio
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class InferenceProvider(str, Enum):
    HUGGINGFACE = "HUGGINGFACE"
    OLLAMA = "OLLAMA"
    OPENAI_COMPATIBLE = "OPENAI_COMPATIBLE"
    LOCAL_MOCK_SAFE = "LOCAL_MOCK_SAFE"


class ExecutionMode(str, Enum):
    LIVE_MODEL_INFERENCE = "LIVE_MODEL_INFERENCE"
    LOCAL_MODEL_INFERENCE = "LOCAL_MODEL_INFERENCE"
    DETERMINISTIC_FALLBACK = "DETERMINISTIC_FALLBACK"
    CACHED_RESPONSE = "CACHED_RESPONSE"
    MOCK_TEST_EXECUTION = "MOCK_TEST_EXECUTION"


class ModelInferenceRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    model_id: Optional[str] = None
    timeout_seconds: float = Field(default=15.0, ge=1.0, le=60.0)


class ModelInferenceResponse(BaseModel):
    content: str
    model_identifier: str
    model_version: str
    provider: str
    execution_mode: str
    latency_ms: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    status: str = "SUCCESS"
    retry_count: int = 0
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class HuggingFaceInferenceService:
    """
    Genuine Model-Provider Integration for Adversarial Researcher & Legal Intelligence.
    Supports:
    1. Remote Hugging Face Inference API / Endpoints
    2. Local Ollama or vLLM OpenAI-compatible endpoints
    3. Safe Mock Transport for isolated reproducible testing
    4. Deterministic Statutory Exception Fallback when providers are offline
    """

    MAX_RETRIES = 2
    RETRY_BACKOFF_BASE = 0.5

    @classmethod
    async def generate_completion(
        cls,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.2,
        mock_response: Optional[str] = None
    ) -> Optional[str]:
        """Convenience method preserving backward compatibility."""
        req = ModelInferenceRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        res = await cls.execute_inference(req, mock_response=mock_response)
        return res.content if res and res.content else None

    @classmethod
    def execute_inference_sync(
        cls,
        request: ModelInferenceRequest,
        mock_response: Optional[str] = None
    ) -> ModelInferenceResponse:
        start_time = time.time()
        if mock_response is not None:
            elapsed = round((time.time() - start_time) * 1000, 2)
            return ModelInferenceResponse(
                content=mock_response,
                model_identifier="mock-legal-evaluator-v1",
                model_version="1.0.0",
                provider=InferenceProvider.LOCAL_MOCK_SAFE.value,
                execution_mode=ExecutionMode.MOCK_TEST_EXECUTION.value,
                latency_ms=elapsed,
                prompt_tokens=len(request.prompt.split()),
                completion_tokens=len(mock_response.split()),
                total_tokens=len(request.prompt.split()) + len(mock_response.split()),
                status="SUCCESS"
            )
        elapsed = round((time.time() - start_time) * 1000, 2)
        fallback_content = cls._deterministic_statutory_fallback(request.prompt)
        return ModelInferenceResponse(
            content=fallback_content,
            model_identifier="deterministic_statutory_exception_rules_v1.0",
            model_version="1.0.0",
            provider="LOCAL_STATUTORY_RULE_ENGINE",
            execution_mode=ExecutionMode.DETERMINISTIC_FALLBACK.value,
            latency_ms=elapsed,
            status="FALLBACK_ACTIVE",
            error_message="Remote inference credentials unset; deterministic fallback invoked."
        )

    @classmethod
    async def execute_inference(
        cls,
        request: ModelInferenceRequest,
        mock_response: Optional[str] = None
    ) -> ModelInferenceResponse:
        start_time = time.time()

        # 0. Mock Test Mode
        if mock_response is not None:
            elapsed = round((time.time() - start_time) * 1000, 2)
            return ModelInferenceResponse(
                content=mock_response,
                model_identifier="mock-legal-evaluator-v1",
                model_version="1.0.0",
                provider=InferenceProvider.LOCAL_MOCK_SAFE.value,
                execution_mode=ExecutionMode.MOCK_TEST_EXECUTION.value,
                latency_ms=elapsed,
                prompt_tokens=len(request.prompt.split()),
                completion_tokens=len(mock_response.split()),
                total_tokens=len(request.prompt.split()) + len(mock_response.split()),
                status="SUCCESS"
            )

        endpoint_url = getattr(settings, "HF_ENDPOINT_URL", None)
        token = getattr(settings, "HF_API_TOKEN", None)
        model_id = request.model_id or getattr(settings, "HF_MODEL_ID", "veridion-legal-finetuned")

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        retries = 0
        last_error = None

        # 1. Check local/custom endpoint URL (Ollama, vLLM, or dedicated container)
        if endpoint_url:
            provider = InferenceProvider.OPENAI_COMPATIBLE.value if "/v1" in endpoint_url else InferenceProvider.HUGGINGFACE.value
            exec_mode = ExecutionMode.LOCAL_MODEL_INFERENCE.value if "localhost" in endpoint_url or "127.0.0.1" in endpoint_url else ExecutionMode.LIVE_MODEL_INFERENCE.value

            for attempt in range(cls.MAX_RETRIES + 1):
                try:
                    async with httpx.AsyncClient(timeout=request.timeout_seconds) as client:
                        if "/v1" in endpoint_url or "chat/completions" in endpoint_url:
                            payload = {
                                "model": model_id,
                                "messages": [
                                    {"role": "system", "content": request.system_prompt or "You are a specialized legal intelligence agent."},
                                    {"role": "user", "content": request.prompt}
                                ],
                                "max_tokens": request.max_tokens,
                                "temperature": request.temperature
                            }
                            res = await client.post(endpoint_url, json=payload, headers=headers)
                            if res.status_code == 200:
                                data = res.json()
                                elapsed = round((time.time() - start_time) * 1000, 2)
                                usage = data.get("usage", {})
                                return ModelInferenceResponse(
                                    content=data["choices"][0]["message"]["content"],
                                    model_identifier=model_id,
                                    model_version="api_v1",
                                    provider=provider,
                                    execution_mode=exec_mode,
                                    latency_ms=elapsed,
                                    prompt_tokens=usage.get("prompt_tokens"),
                                    completion_tokens=usage.get("completion_tokens"),
                                    total_tokens=usage.get("total_tokens"),
                                    status="SUCCESS",
                                    retry_count=attempt,
                                    raw_response={"status": 200}
                                )
                            elif res.status_code == 429:
                                last_error = "Rate limit encountered (HTTP 429)"
                                await asyncio.sleep(cls.RETRY_BACKOFF_BASE * (2 ** attempt))
                                retries += 1
                                continue
                            else:
                                last_error = f"HTTP {res.status_code}: {res.text[:100]}"
                        else:
                            # Raw HuggingFace endpoint
                            payload = {
                                "inputs": f"{request.system_prompt}\n\nUser: {request.prompt}\n\nAssistant:",
                                "parameters": {"max_new_tokens": request.max_tokens, "temperature": request.temperature}
                            }
                            res = await client.post(endpoint_url, json=payload, headers=headers)
                            if res.status_code == 200:
                                data = res.json()
                                content = data[0].get("generated_text", str(data[0])) if isinstance(data, list) and data else str(data)
                                elapsed = round((time.time() - start_time) * 1000, 2)
                                return ModelInferenceResponse(
                                    content=content,
                                    model_identifier=model_id,
                                    model_version="tgi_raw",
                                    provider=provider,
                                    execution_mode=exec_mode,
                                    latency_ms=elapsed,
                                    status="SUCCESS",
                                    retry_count=attempt
                                )
                except Exception as e:
                    last_error = str(e)
                    await asyncio.sleep(cls.RETRY_BACKOFF_BASE * (2 ** attempt))
                    retries += 1

        # 2. Check Hugging Face Hub hosted inference API if token is present
        if token and model_id and not endpoint_url:
            hub_url = f"https://api-inference.huggingface.co/models/{model_id}"
            for attempt in range(cls.MAX_RETRIES + 1):
                try:
                    async with httpx.AsyncClient(timeout=request.timeout_seconds) as client:
                        res = await client.post(
                            hub_url,
                            json={"inputs": request.prompt, "parameters": {"max_new_tokens": request.max_tokens}},
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        if res.status_code == 200:
                            data = res.json()
                            content = data[0].get("generated_text") if isinstance(data, list) and data else str(data)
                            elapsed = round((time.time() - start_time) * 1000, 2)
                            return ModelInferenceResponse(
                                content=content,
                                model_identifier=model_id,
                                model_version="hf_hub_v1",
                                provider=InferenceProvider.HUGGINGFACE.value,
                                execution_mode=ExecutionMode.LIVE_MODEL_INFERENCE.value,
                                latency_ms=elapsed,
                                status="SUCCESS",
                                retry_count=attempt
                            )
                except Exception as e:
                    last_error = str(e)
                    await asyncio.sleep(cls.RETRY_BACKOFF_BASE * (2 ** attempt))
                    retries += 1

        # 3. Graceful Deterministic Statutory Fallback
        elapsed = round((time.time() - start_time) * 1000, 2)
        fallback_content = cls._deterministic_statutory_fallback(request.prompt)
        return ModelInferenceResponse(
            content=fallback_content,
            model_identifier="deterministic_statutory_exception_rules_v1.0",
            model_version="1.0.0",
            provider="LOCAL_STATUTORY_RULE_ENGINE",
            execution_mode=ExecutionMode.DETERMINISTIC_FALLBACK.value,
            latency_ms=elapsed,
            status="FALLBACK_ACTIVE",
            retry_count=retries,
            error_message=last_error or "Remote inference credentials unset; deterministic fallback invoked."
        )

    @classmethod
    def _deterministic_statutory_fallback(cls, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "biometric" in prompt_lower or "special category" in prompt_lower:
            return "Contesting applicability: Controller may assert employment law exemption (Art 9(2)(b)) or substantial public interest (Art 9(2)(g)) subject to statutory safeguards."
        elif "training" in prompt_lower or "purpose" in prompt_lower:
            return "Contesting applicability: Controller may assert legitimate interest (Art 6(1)(f)) or scientific research exemption (Art 89(1)) if data is sanitized and technical safeguards apply."
        elif "retention" in prompt_lower or "storage" in prompt_lower:
            return "Contesting breach: Retention may be justified under legal obligation defense (Art 6(1)(c)) or archiving in the public interest (Art 89(1))."
        else:
            return "Adversarial Defense: Controller asserts procedural compliance and lack of demonstrated data subject harm under applicable statutory limitations."
