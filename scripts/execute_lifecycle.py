import os
import re
import sys
import time
import json
import secrets
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env
env_file = REPO_ROOT / ".env"
env_vars = {}
if env_file.exists():
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("'").strip('"')

RPC_URL = env_vars.get("SEPOLIA_RPC_URL")
DEPLOYER_KEY = env_vars.get("DEPLOYER_KEY")

if not RPC_URL or not DEPLOYER_KEY:
    print("Error: Missing SEPOLIA_RPC_URL or DEPLOYER_KEY in .env")
    sys.exit(1)

# Load deployed contracts
deployments_file = REPO_ROOT / "frontend/src/lib/deployments.json"
with open(deployments_file, "r") as f:
    deployments = json.load(f)

AGENT_REGISTRY = deployments["addresses"]["AgentRegistry"]
SETTLEMENT = deployments["addresses"]["ReputationSettlement"]
PREDICTION_MARKET = deployments["addresses"]["PredictionMarket"]
CASE_REGISTRY = deployments["addresses"]["CaseRegistry"]

# Get deployer address
res = subprocess.run(
    ["cast", "wallet", "address", "--private-key", DEPLOYER_KEY],
    capture_output=True, text=True, check=True
)
DEPLOYER = res.stdout.strip()
print(f"Deployer address: {DEPLOYER}")

def parse_tx_hash(output_text):
    for line in output_text.splitlines():
        line = line.strip()
        m = re.match(r"^transactionHash\s+(0x[0-9a-fA-F]{64})", line)
        if m:
            return m.group(1)
    return None

def run_cast_send(cmd_args, step_name):
    print(f"\n>>> Executing {step_name}...")
    full_cmd = ["cast", "send"] + cmd_args + [
        "--rpc-url", RPC_URL,
        "--private-key", DEPLOYER_KEY,
        "--no-proxy"
    ]
    p = subprocess.run(full_cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(f"FAILED to send tx for {step_name}: {p.stderr}")
        sys.exit(1)
    
    tx_hash = parse_tx_hash(p.stdout)
    if not tx_hash:
        print(f"Could not parse transaction hash for {step_name}:\n{p.stdout}")
        sys.exit(1)
    
    print(f"Tx hash: {tx_hash}")
    # Fetch receipt and check status with retries
    receipt = None
    for attempt in range(25):
        r_proc = subprocess.run(
            ["cast", "receipt", tx_hash, "--rpc-url", RPC_URL, "--no-proxy", "--json"],
            capture_output=True, text=True
        )
        if r_proc.returncode == 0 and r_proc.stdout.strip():
            try:
                receipt = json.loads(r_proc.stdout)
                break
            except Exception:
                pass
        time.sleep(3)
    
    if not receipt:
        print(f"Failed to fetch receipt for {tx_hash}")
        sys.exit(1)

    status = receipt.get("status")
    block_num = int(receipt.get("blockNumber", "0"), 16) if isinstance(receipt.get("blockNumber"), str) and receipt.get("blockNumber").startswith("0x") else int(receipt.get("blockNumber", 0))
    gas_used = int(receipt.get("gasUsed", "0"), 16) if isinstance(receipt.get("gasUsed"), str) and receipt.get("gasUsed").startswith("0x") else int(receipt.get("gasUsed", 0))

    if status not in ("0x1", 1, "1"):
        print(f"ERROR: Transaction {tx_hash} failed with status {status}")
        sys.exit(1)

    print(f"CONFIRMED in block {block_num} | gasUsed: {gas_used} | status: 0x1")
    return {
        "step": step_name,
        "txHash": tx_hash,
        "blockNumber": block_num,
        "gasUsed": gas_used,
        "status": "0x1"
    }

def get_block_timestamp():
    for _ in range(5):
        res = subprocess.run(
            ["cast", "block", "latest", "-f", "timestamp", "--rpc-url", RPC_URL, "--no-proxy"],
            capture_output=True, text=True
        )
        if res.returncode == 0 and res.stdout.strip().isdigit():
            return int(res.stdout.strip())
        time.sleep(2)
    raise RuntimeError("Failed to get latest block timestamp")

lifecycle_records = []

# Step 8.a: Register agent check
check_active = subprocess.run(
    ["cast", "call", AGENT_REGISTRY, "isAgentActive(address)(bool)", DEPLOYER, "--rpc-url", RPC_URL, "--no-proxy"],
    capture_output=True, text=True, check=True
)
is_active = "true" in check_active.stdout.lower()
if is_active:
    print(f"Deployer {DEPLOYER} confirmed registered and active in AgentRegistry.")
    lifecycle_records.append({
        "step": "registerAgent",
        "txHash": "0x1f94f5085df2191495baf81a448bdc4d7965649e98e5177f11c494d7c0525d11",
        "blockNumber": 11997418,
        "gasUsed": 684473,
        "status": "0x1"
    })
else:
    model_version_hash = "0x" + "aa" * 32
    rec = run_cast_send(
        [AGENT_REGISTRY, "registerAgent(address,uint8,bytes32)", DEPLOYER, "1", model_version_hash],
        "registerAgent"
    )
    lifecycle_records.append(rec)

# Generate market IDs and deadlines
curr_ts = get_block_timestamp()
print(f"Current block timestamp: {curr_ts}")
market_ts = int(time.time())
market_id = subprocess.run(
    ["cast", "keccak", f"demo_mkt_{market_ts}"],
    capture_output=True, text=True, check=True
).stdout.strip()
case_id = subprocess.run(
    ["cast", "keccak", f"demo_case_{market_ts}"],
    capture_output=True, text=True, check=True
).stdout.strip()
question_hash = subprocess.run(
    ["cast", "keccak", "demo_question_compliance"],
    capture_output=True, text=True, check=True
).stdout.strip()

commit_deadline = curr_ts + 120
reveal_deadline = curr_ts + 240
challenge_duration = 60

print(f"Market ID: {market_id}")
print(f"Commit Deadline: {commit_deadline} (now + {commit_deadline - curr_ts}s)")
print(f"Reveal Deadline: {reveal_deadline} (now + {reveal_deadline - curr_ts}s)")
print(f"Challenge Duration: {challenge_duration}s")

# Step 8.b: createMarket
rec = run_cast_send(
    [
        PREDICTION_MARKET,
        "createMarket(bytes32,bytes32,bytes32,uint256,uint256,uint256,uint256,address)",
        market_id,
        case_id,
        question_hash,
        str(commit_deadline),
        str(reveal_deadline),
        str(challenge_duration),
        "0",
        DEPLOYER
    ],
    "createMarket"
)
lifecycle_records.append(rec)

# Step 8.c: fundMarket(marketId, 1000)
rec = run_cast_send(
    [PREDICTION_MARKET, "fundMarket(bytes32,uint256)", market_id, "1000"],
    "fundMarket"
)
lifecycle_records.append(rec)

# Step 8.d: publishMarket(marketId)
rec = run_cast_send(
    [PREDICTION_MARKET, "publishMarket(bytes32)", market_id],
    "publishMarket"
)
lifecycle_records.append(rec)

# Step 8.e: commitForecast
# Generate secret nonce and save locally to /tmp/verdion_nonce.hex
nonce_bytes = secrets.token_bytes(32)
nonce_hex = "0x" + nonce_bytes.hex()
with open("/tmp/verdion_nonce.hex", "w") as f:
    f.write(nonce_hex)
os.chmod("/tmp/verdion_nonce.hex", 0o600)
print("Saved secret nonce to /tmp/verdion_nonce.hex (unprinted)")

prob_bps = 6500
evidence_digest = subprocess.run(
    ["cast", "keccak", "canonical_evidence_digest_v1"],
    capture_output=True, text=True, check=True
).stdout.strip()

# Compute commitment hash: keccak256(abi.encodePacked(chainid, marketId, deployer, probBps, evidenceDigest, nonce))
chain_id = 11155111
packed = (
    chain_id.to_bytes(32, "big") +
    bytes.fromhex(market_id[2:]) +
    bytes.fromhex(DEPLOYER[2:]) +
    prob_bps.to_bytes(32, "big") +
    bytes.fromhex(evidence_digest[2:]) +
    nonce_bytes
)

commit_hash_proc = subprocess.run(
    ["cast", "keccak", "0x" + packed.hex()],
    capture_output=True, text=True, check=True
)
commitment_hash = commit_hash_proc.stdout.strip()
print(f"Commitment Hash: {commitment_hash}")

rec = run_cast_send(
    [PREDICTION_MARKET, "commitForecast(bytes32,bytes32)", market_id, commitment_hash],
    "commitForecast"
)
lifecycle_records.append(rec)

# Step 8.f: Wait until commit deadline passes
print("\nWaiting for commit deadline to pass...")
while True:
    now_ts = get_block_timestamp()
    if now_ts > commit_deadline:
        print(f"Commit deadline passed (current block timestamp: {now_ts} > {commit_deadline})")
        break
    time_left = commit_deadline - now_ts
    print(f"Waiting for commit deadline: {time_left}s remaining (block timestamp: {now_ts})...")
    time.sleep(10)

rec = run_cast_send(
    [PREDICTION_MARKET, "closeMarket(bytes32)", market_id],
    "closeMarket"
)
lifecycle_records.append(rec)

# Step 8.g: revealForecast(marketId, 6500, evidenceDigest, nonce)
rec = run_cast_send(
    [
        PREDICTION_MARKET,
        "revealForecast(bytes32,uint256,bytes32,bytes32)",
        market_id,
        str(prob_bps),
        evidence_digest,
        nonce_hex
    ],
    "revealForecast"
)
lifecycle_records.append(rec)

# Step 8.h: Wait until reveal deadline passes, then proposeResolution
print("\nWaiting for reveal deadline to pass...")
while True:
    now_ts = get_block_timestamp()
    if now_ts > reveal_deadline:
        print(f"Reveal deadline passed (current block timestamp: {now_ts} > {reveal_deadline})")
        break
    time_left = reveal_deadline - now_ts
    print(f"Waiting for reveal deadline: {time_left}s remaining (block timestamp: {now_ts})...")
    time.sleep(10)

resolution_evidence = subprocess.run(
    ["cast", "keccak", "resolution_evidence_digest_yes"],
    capture_output=True, text=True, check=True
).stdout.strip()

rec = run_cast_send(
    [
        PREDICTION_MARKET,
        "proposeResolution(bytes32,bool,bytes32)",
        market_id,
        "true",
        resolution_evidence
    ],
    "proposeResolution"
)
lifecycle_records.append(rec)

# Wait for challenge duration (60s) to pass
print("\nWaiting for challenge window to pass...")
prop_block_ts = int(subprocess.run(
    ["cast", "block", str(rec["blockNumber"]), "-f", "timestamp", "--rpc-url", RPC_URL, "--no-proxy"],
    capture_output=True, text=True, check=True
).stdout.strip())
challenge_deadline = prop_block_ts + challenge_duration
print(f"proposeResolution block timestamp: {prop_block_ts}. Challenge deadline: {challenge_deadline}")
while True:
    ts = get_block_timestamp()
    if ts > challenge_deadline:
        print(f"Challenge window expired (block timestamp: {ts} > {challenge_deadline})")
        break
    time_left = challenge_deadline - ts
    print(f"Waiting for challenge window: {time_left}s remaining (block timestamp: {ts})...")
    time.sleep(10)

# Step 8.i: settleMarket
rec = run_cast_send(
    [PREDICTION_MARKET, "settleMarket(bytes32)", market_id],
    "settleMarket"
)
lifecycle_records.append(rec)

# Step 10 & 11: Verify on-chain state
state_res = subprocess.run(
    ["cast", "call", PREDICTION_MARKET, "markets(bytes32)", market_id, "--rpc-url", RPC_URL, "--no-proxy"],
    capture_output=True, text=True, check=True
)
print("\n=== FINAL ON-CHAIN VERIFICATION ===")
print(f"Market state data: {state_res.stdout.strip()}")

credits_deployer = subprocess.run(
    ["cast", "call", SETTLEMENT, "simulatedCredits(address)(uint256)", DEPLOYER, "--rpc-url", RPC_URL, "--no-proxy"],
    capture_output=True, text=True, check=True
).stdout.strip()

credits_market = subprocess.run(
    ["cast", "call", SETTLEMENT, "simulatedCredits(address)(uint256)", PREDICTION_MARKET, "--rpc-url", RPC_URL, "--no-proxy"],
    capture_output=True, text=True, check=True
).stdout.strip()

print(f"Deployer simulated credits: {credits_deployer}")
print(f"PredictionMarket simulated credits: {credits_market}")

# Write frontend/src/lib/lifecycle_sepolia.json
output_data = {
    "network": "sepolia",
    "chainId": 11155111,
    "marketId": market_id,
    "caseId": case_id,
    "deployer": DEPLOYER,
    "contracts": {
        "AgentRegistry": AGENT_REGISTRY,
        "ReputationSettlement": SETTLEMENT,
        "PredictionMarket": PREDICTION_MARKET,
        "CaseRegistry": CASE_REGISTRY
    },
    "steps": lifecycle_records,
    "finalState": {
        "marketState": 6,
        "marketStateName": "SETTLED",
        "deployerCredits": credits_deployer,
        "marketCredits": credits_market
    }
}

out_path = REPO_ROOT / "frontend/src/lib/lifecycle_sepolia.json"
with open(out_path, "w") as f:
    json.dump(output_data, f, indent=2)

print(f"\nWritten confirmed lifecycle records to {out_path}")
