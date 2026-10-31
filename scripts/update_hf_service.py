path = r"c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion\backend\app\services\hf_service.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

old_block = '''        # 2. Check Hugging Face Hub hosted inference API if token is present
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
                    retries += 1'''

new_block = '''        # 2. Check Hugging Face Hub hosted inference API if token is present
        if token and model_id and not endpoint_url:
            hub_urls = [
                f"https://router.huggingface.co/hf-inference/models/{model_id}",
                f"https://api-inference.huggingface.co/models/{model_id}"
            ]
            for hub_url in hub_urls:
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
                                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                                    content = data[0].get("generated_text") or data[0].get("sequence") or str(data[0])
                                else:
                                    content = str(data)
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
                        retries += 1'''

if old_block.replace("\n", "\r\n") in text:
    text = text.replace(old_block.replace("\n", "\r\n"), new_block.replace("\n", "\r\n"))
elif old_block in text:
    text = text.replace(old_block, new_block)
else:
    print("Old block not found!")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Updated hf_service.py successfully!")
