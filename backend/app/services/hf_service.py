import logging
from typing import Any, Dict, List, Optional
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class HuggingFaceInferenceService:
    """
    Adapter for Hugging Face models (fine-tuned by ML teammate).
    Supports:
    1. Local inference server (e.g. vLLM / TGI / Ollama OpenAI-compatible endpoint at HF_ENDPOINT_URL)
    2. Hugging Face Hosted Inference API (via HF_API_TOKEN and HF_MODEL_ID)
    3. Seamless fallback to deterministic hybrid reasoning engine if offline.
    """

    @classmethod
    async def generate_completion(
        cls,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.2
    ) -> Optional[str]:
        # 1. Check if local endpoint URL is configured (e.g. teammate running vLLM or Ollama)
        endpoint_url = getattr(settings, "HF_ENDPOINT_URL", None)
        token = getattr(settings, "HF_API_TOKEN", None)
        model_id = getattr(settings, "HF_MODEL_ID", "veridion-legal-finetuned")

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        if endpoint_url:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Check if OpenAI-compatible /v1/chat/completions or raw TGI /generate
                    if "/v1" in endpoint_url or "chat/completions" in endpoint_url:
                        payload = {
                            "model": model_id,
                            "messages": [
                                {"role": "system", "content": system_prompt or "You are a specialized legal intelligence agent."},
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": max_tokens,
                            "temperature": temperature
                        }
                        res = await client.post(endpoint_url, json=payload, headers=headers)
                        if res.status_code == 200:
                            data = res.json()
                            return data["choices"][0]["message"]["content"]
                    else:
                        # Raw HuggingFace endpoint
                        payload = {
                            "inputs": f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:",
                            "parameters": {"max_new_tokens": max_tokens, "temperature": temperature}
                        }
                        res = await client.post(endpoint_url, json=payload, headers=headers)
                        if res.status_code == 200:
                            data = res.json()
                            if isinstance(data, list) and len(data) > 0:
                                return data[0].get("generated_text", str(data[0]))
                            return str(data)
            except Exception as e:
                logger.warning(f"Failed to query Hugging Face endpoint ({endpoint_url}): {e}. Falling back to internal engine.")

        # 2. Check Hugging Face Hub hosted inference API
        if token and model_id and not endpoint_url:
            hub_url = f"https://api-inference.huggingface.co/models/{model_id}"
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(
                        hub_url,
                        json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}},
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        if isinstance(data, list) and len(data) > 0:
                            return data[0].get("generated_text")
            except Exception as e:
                logger.warning(f"Failed to query HF Hub: {e}")

        return None
