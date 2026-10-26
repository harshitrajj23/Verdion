// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../script/Deploy.s.sol";

contract DeployScriptTest is Test {
    function testDeployScriptCoreSteps() public {
        uint256 testDeployerKey = 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef;
        address deployer = vm.addr(testDeployerKey);

        vm.startBroadcast(testDeployerKey);

        CaseRegistry caseRegistry = new CaseRegistry();
        AgentRegistry agentRegistry = new AgentRegistry();
        ReputationSettlement settlement = new ReputationSettlement();
        PredictionMarket market = new PredictionMarket(address(agentRegistry), address(settlement));
        EvidenceBounty bounty = new EvidenceBounty(address(settlement));

        settlement.setContracts(address(market), address(bounty));
        settlement.setAuthorizedEvaluator(deployer);
        settlement.mintSimulatedCredits(deployer, 1_000_000);

        vm.stopBroadcast();

        // 1. Assert evaluator equals deployer
        assertEq(settlement.authorizedEvaluator(), deployer, "Evaluator must equal deployer");

        // 2. Assert deployer has simulated credits
        assertEq(settlement.simulatedCredits(deployer), 1_000_000, "Deployer must have 1,000,000 simulated credits");

        // 3. Assert fundMarket succeeds via createMarket funding
        bytes32 caseId = keccak256("test_case");
        bytes32 marketId = keccak256("test_market");
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.startPrank(deployer);
        caseRegistry.createCase(caseId, keccak256("scope"), keccak256("corpus"));

        market.createMarket(
            marketId,
            caseId,
            keccak256("question"),
            commitDeadline,
            revealDeadline,
            50,
            1000,
            deployer
        );

        // Verify deployer credits were deducted and transferred to market
        assertEq(settlement.simulatedCredits(deployer), 999_000, "Deployer balance must decrease by funded amount");
        assertEq(settlement.simulatedCredits(address(market)), 1000, "Market contract must hold funded credits");

        vm.stopPrank();
    }

    function testCommitmentHashVector() public pure {
        bytes32 expected = 0x3df6407fdb7eece6a9a9179142955b119acd0e02629b683f16c199a90433c8fc;
        bytes32 actual = keccak256(
            abi.encodePacked(
                uint256(11155111),
                bytes32(hex"1111111111111111111111111111111111111111111111111111111111111111"),
                address(0x34867B3Ad7B4353BA08bD74664E8bF27836e2888),
                uint256(6500),
                bytes32(hex"2222222222222222222222222222222222222222222222222222222222222222"),
                bytes32(hex"3333333333333333333333333333333333333333333333333333333333333333")
            )
        );
        require(actual == expected, "Vector mismatch");
    }

    function testCommitmentHashVector31337() public {
        bytes32 expected = 0x5fb6b56580af9bfadf64e4f205aa1854a5261e37cc54e6e41acc373f398acaf3;
        bytes memory packed = abi.encodePacked(
            uint256(31337),
            bytes32(0x28ae417f244d0e508d7a27a92b0434f79694b0cab002e4a00c2939ad46e05b3e),
            address(0x34867B3Ad7B4353BA08bD74664E8bF27836e2888),
            uint256(6500),
            bytes32(hex"2222222222222222222222222222222222222222222222222222222222222222"),
            bytes32(hex"3333333333333333333333333333333333333333333333333333333333333333")
        );
        bytes32 actual = keccak256(packed);
        emit log_named_bytes32("keccak", actual);
        require(actual == expected, "Vector mismatch");
    }
}


