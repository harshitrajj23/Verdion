// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/CaseRegistry.sol";
import "../src/AgentRegistry.sol";
import "../src/ReputationSettlement.sol";
import "../src/PredictionMarket.sol";
import "../src/EvidenceBounty.sol";

contract DeployVerdion is Script {
    function parseHexUint(string memory s) internal pure returns (uint256 result) {
        bytes memory b = bytes(s);
        uint256 start = 0;
        if (b.length >= 2 && b[0] == "0" && (b[1] == "x" || b[1] == "X")) {
            start = 2;
        }
        for (uint256 i = start; i < b.length; i++) {
            uint8 c = uint8(b[i]);
            uint8 val;
            if (c >= 48 && c <= 57) {
                val = c - 48;
            } else if (c >= 65 && c <= 70) {
                val = c - 55;
            } else if (c >= 97 && c <= 102) {
                val = c - 87;
            } else {
                continue;
            }
            result = result * 16 + val;
        }
    }

    function readDeployerKey() internal view returns (uint256) {
        try vm.envUint("DEPLOYER_KEY") returns (uint256 key) {
            return key;
        } catch {
            string memory keyStr = vm.envString("DEPLOYER_KEY");
            uint256 key = parseHexUint(keyStr);
            require(key != 0, "DEPLOYER_KEY unset or invalid");
            return key;
        }
    }

    function run() external {
        uint256 deployerPrivateKey = readDeployerKey();
        require(deployerPrivateKey != 0, "DEPLOYER_KEY must be set");

        address deployer = vm.addr(deployerPrivateKey);

        console.log("=== Verdion Protocol Deployment ===");
        console.log("Deployer:", deployer);

        vm.startBroadcast(deployerPrivateKey);

        CaseRegistry caseRegistry = new CaseRegistry();
        AgentRegistry agentRegistry = new AgentRegistry();
        ReputationSettlement settlement = new ReputationSettlement();
        PredictionMarket market = new PredictionMarket(address(agentRegistry), address(settlement));
        EvidenceBounty bounty = new EvidenceBounty(address(settlement));

        settlement.setContracts(address(market), address(bounty));
        settlement.setAuthorizedEvaluator(deployer);
        settlement.mintSimulatedCredits(deployer, 1_000_000);

        console.log("CaseRegistry:        ", address(caseRegistry));
        console.log("AgentRegistry:       ", address(agentRegistry));
        console.log("ReputationSettlement:", address(settlement));
        console.log("PredictionMarket:    ", address(market));
        console.log("EvidenceBounty:      ", address(bounty));

        vm.stopBroadcast();
    }
}
