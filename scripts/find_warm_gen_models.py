import urllib.request
import json
import sys

sys.path.insert(0, r"c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion")
from backend.app.core.config import settings

token = settings.HF_API_TOKEN

url = "https://huggingface.co/api/models?pipeline_tag=text-generation&inference=warm&limit=10"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print("Warm Text-Generation Models on Hugging Face:")
    for d in data:
        print("  -", d.get("id"))
