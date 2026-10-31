import urllib.request
import json
import sys

sys.path.insert(0, r"c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion")
from backend.app.core.config import settings

token = settings.HF_API_TOKEN

req = urllib.request.Request(
    "https://huggingface.co/api/models?inference=warm&limit=10",
    headers={"Authorization": f"Bearer {token}", "User-Agent": "Verdion/1.0"}
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        models = json.loads(resp.read().decode("utf-8"))
        print("Warm inference models on Hugging Face:")
        for m in models:
            print(f"  - {m.get('id')}")
except Exception as e:
    print("Error querying warm models:", e)
