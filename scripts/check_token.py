import json
import urllib.request
import sys

sys.path.insert(0, r"c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion")
from backend.app.core.config import settings

token = settings.HF_API_TOKEN

req = urllib.request.Request(
    "https://huggingface.co/api/whoami-v2",
    headers={"Authorization": f"Bearer {token}", "User-Agent": "VerdionLegal/1.0"}
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("Token Verified!")
        print(f"User: {data.get('name')}")
        print(f"Type: {data.get('type')}")
        print(f"Auth: {data.get('auth')}")
except Exception as e:
    print(f"Token error: {e}")

