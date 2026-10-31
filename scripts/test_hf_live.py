import asyncio
import os
import sys

sys.path.insert(0, r"c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion")

from backend.app.core.config import settings
from backend.app.services.hf_service import HuggingFaceInferenceService, ModelInferenceRequest

async def test_live_inference():
    print(f"HF_API_TOKEN configured: {bool(settings.HF_API_TOKEN)} ({settings.HF_API_TOKEN[:6]}...)")
    print(f"HF_MODEL_ID: {settings.HF_MODEL_ID}")
    
    req = ModelInferenceRequest(
        prompt="Processing of personal data is lawful under [MASK] 6 of the GDPR.",
        max_tokens=50
    )
    
    print("\nExecuting live Hugging Face inference via HuggingFaceInferenceService...")
    res = await HuggingFaceInferenceService.execute_inference(req)
    print("\n--- Live Inference Result ---")
    print(f"Provider: {res.provider}")
    print(f"Execution Mode: {res.execution_mode}")
    print(f"Model ID: {res.model_identifier}")
    print(f"Latency: {res.latency_ms} ms")
    print(f"Status: {res.status}")
    print(f"Content: {res.content}")

if __name__ == "__main__":
    asyncio.run(test_live_inference())
