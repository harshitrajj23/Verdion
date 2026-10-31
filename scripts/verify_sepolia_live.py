import json
import urllib.request
import os

def check_sepolia():
    rpc_url = "https://eth-sepolia.g.alchemy.com/v2/3iY4UXhtAVBnPmW9e0962"
    
    contracts = {
        "CaseRegistry": "0x9dEEFCa6b93d9812Cf67Dc7b3daCc51b62C6455E",
        "AgentRegistry": "0x32d5D291e287fF173F803f5ee53Aef75BADb2006",
        "PredictionMarket": "0xFF5e85547E443e3d50b393E09885c6Eb9671EE27",
        "EvidenceBounty": "0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46",
        "ReputationSettlement": "0xb002cd06fC2ce01B38C08787E6C4EaeAf547748c"
    }

    deployer_address = "0xF733bB7fe878B3830c2B1a1E13837494D28c50E2"

    results = {
        "rpc_url": rpc_url,
        "is_connected": False,
        "chain_id": None,
        "chain_id_matches_sepolia": False,
        "latest_block_number": None,
        "deployer_balance_wei": None,
        "contracts": {}
    }

    def rpc_call(method, params=[]):
        payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode('utf-8')
        req = urllib.request.Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "VerdionAudit/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if "error" in data:
                raise RuntimeError(f"RPC Error: {data['error']}")
            return data["result"]

    try:
        chain_id_hex = rpc_call("eth_chainId")
        chain_id = int(chain_id_hex, 16)
        results["chain_id"] = chain_id
        results["chain_id_matches_sepolia"] = (chain_id == 11155111)
        results["is_connected"] = True

        block_hex = rpc_call("eth_blockNumber")
        results["latest_block_number"] = int(block_hex, 16)

        bal_hex = rpc_call("eth_getBalance", [deployer_address, "latest"])
        results["deployer_balance_wei"] = int(bal_hex, 16)

        for name, addr in contracts.items():
            code = rpc_call("eth_getCode", [addr, "latest"])
            code_len = len(code) - 2 # strip 0x
            is_deployed = len(code) > 2 and code != "0x"
            results["contracts"][name] = {
                "address": addr,
                "is_deployed": is_deployed,
                "bytecode_bytes": code_len // 2,
                "code_sample": code[:30] + "..." if is_deployed else "0x"
            }

    except Exception as e:
        results["error"] = str(e)

    output_path = os.path.join(os.path.dirname(__file__), "..", "audit", "sepolia_verification_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Sepolia live verification completed:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    check_sepolia()

