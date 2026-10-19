// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/CaseRegistry.sol";
import "../src/AgentRegistry.sol";
import "../src/ReputationSettlement.sol";
import "../src/PredictionMarket.sol";
import "../src/EvidenceBounty.sol";

contract DeployVerdion is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envOr(
            "PRIVATE_KEY",
            uint256(0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80) // Anvil default key 0
        );

        vm.startBroadcast(deployerPrivateKey);

        CaseRegistry caseRegistry = new CaseRegistry();
        AgentRegistry agentRegistry = new AgentRegistry();
        ReputationSettlement settlement = new ReputationSettlement();
        PredictionMarket market = new PredictionMarket(address(agentRegistry), address(settlement));
        EvidenceBounty bounty = new EvidenceBounty(address(settlement));

        settlement.setContracts(address(market), address(bounty));

        console.log("=== Verdion Contract Deployment ===");
        console.log("CaseRegistry:        ", address(caseRegistry));
        console.log("AgentRegistry:       ", address(agentRegistry));
        console.log("ReputationSettlement:", address(settlement));
        console.log("PredictionMarket:    ", address(market));
        console.log("EvidenceBounty:      ", address(bounty));

        vm.stopBroadcast();
    }
}
