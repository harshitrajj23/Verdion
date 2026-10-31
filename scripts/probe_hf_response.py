import urllib.request
import urllib.error
import json
import sys

sys.path.insert(0, r"c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion")
from backend.app.core.config import settings

token = settings.HF_API_TOKEN
model = "google/flan-t5-base"
url = f"https://router.huggingface.co/hf-inference/models/{model}"

req = urllib.request.Request(
    url,
    data=json.dumps({"inputs": "Is customer support audio processing without consent a compliance violation under GDPR? Answer yes or no."}).encode("utf-8"),
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print("Success:", resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode('utf-8')}")
