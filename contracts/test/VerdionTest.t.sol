// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../src/CaseRegistry.sol";
import "../src/AgentRegistry.sol";
import "../src/ReputationSettlement.sol";
import "../src/PredictionMarket.sol";
import "../src/EvidenceBounty.sol";

contract VerdionTest is Test {
    CaseRegistry public caseRegistry;
    AgentRegistry public agentRegistry;
    ReputationSettlement public settlement;
    PredictionMarket public market;
    EvidenceBounty public bounty;

    address public admin = address(0xAA);
    address public evaluator = address(0xBB);
    address public agent1 = address(0x11);
    address public agent2 = address(0x22);
    address public agent3 = address(0x44);
    address public contributor = address(0x33);
    address public maliciousUser = address(0x66);

    bytes32 public caseId = keccak256("case_euaia_001");
    bytes32 public marketId = keccak256("mkt_gdpr_001");
    bytes32 public bountyId = keccak256("bounty_edpb_001");
    bytes32 public evidenceDigest = keccak256("canonical_evidence_digest_v1");

    function setUp() public {
        vm.startPrank(admin);

        caseRegistry = new CaseRegistry();
        agentRegistry = new AgentRegistry();
        settlement = new ReputationSettlement();
        market = new PredictionMarket(address(agentRegistry), address(settlement));
        bounty = new EvidenceBounty(address(settlement));

        settlement.setContracts(address(market), address(bounty));
        settlement.setAuthorizedEvaluator(evaluator);

        // Mint simulated credits for testing
        settlement.mintSimulatedCredits(admin, 1000000);

        // Register agents
        agentRegistry.registerAgent(agent1, AgentRegistry.AgentRole.QUANTITATIVE_FORECASTER, keccak256("gpt-4o-v1"));
        agentRegistry.registerAgent(agent2, AgentRegistry.AgentRole.QUANTITATIVE_FORECASTER, keccak256("claude-3-5-sonnet"));
        agentRegistry.registerAgent(agent3, AgentRegistry.AgentRole.QUANTITATIVE_FORECASTER, keccak256("qwen-2.5-7b"));

        vm.stopPrank();
    }

    // --- CASE REGISTRY TESTS ---
    function testCaseCreationAndVersioning() public {
        vm.prank(admin);
        caseRegistry.createCase(caseId, keccak256("scope_v1"), keccak256("corpus_v1"));

        (bytes32 id, uint256 version, address owner, CaseRegistry.CaseStatus status,,,) = caseRegistry.cases(caseId);
        assertEq(id, caseId);
        assertEq(version, 1);
        assertEq(owner, admin);
        assertEq(uint(status), uint(CaseRegistry.CaseStatus.DRAFT));

        // Update scope -> version 2
        vm.prank(admin);
        caseRegistry.updateCaseScope(caseId, keccak256("scope_v2"), keccak256("corpus_v1"));

        (, uint256 newVersion,,,,,) = caseRegistry.cases(caseId);
        assertEq(newVersion, 2);
    }

    // --- PREDICTION MARKET TESTS (§10, §12.2) ---
    function testMarketHappyPathCommitRevealAndSettlement() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;
        uint256 challengeDuration = 50;

        vm.prank(admin);
        market.createMarket(
            marketId,
            caseId,
            keccak256("question_compliance_gap"),
            commitDeadline,
            revealDeadline,
            challengeDuration,
            1000,
            evaluator
        );

        vm.prank(evaluator);
        market.publishMarket(marketId);

        // Agent 1: 80% (8000 bps)
        bytes32 nonce1 = bytes32(uint256(12345));
        bytes32 commitHash1 = keccak256(
            abi.encodePacked(
                block.chainid,
                marketId,
                agent1,
                uint256(8000),
                evidenceDigest,
                nonce1
            )
        );

        vm.prank(agent1);
        market.commitForecast(marketId, commitHash1);

        // Fast forward to reveal window
        vm.warp(commitDeadline + 1);

        vm.prank(agent1);
        market.revealForecast(marketId, 8000, evidenceDigest, nonce1);

        // Fast forward past reveal deadline
        vm.warp(revealDeadline + 1);

        // Evaluator proposes resolution (YES = true)
        vm.prank(evaluator);
        market.proposeResolution(marketId, true, evidenceDigest);

        // Fast forward past challenge duration
        vm.warp(block.timestamp + challengeDuration + 1);

        // Settle market
        vm.prank(evaluator);
        market.settleMarket(marketId);

        // Verify simulated credits rewarded
        uint256 creditsEarned = settlement.simulatedCredits(agent1);
        assertGt(creditsEarned, 0);

        // Verify Brier score update
        (uint256 totalEvaluated,, uint256 avgBrier,,,) = settlement.agentReputations(agent1);
        assertEq(totalEvaluated, 1);
        // (8000 - 10000)^2 / 10000 = (-2000)^2 / 10000 = 400 bps
        assertEq(avgBrier, 400);
    }

    // Step 1a: Access control test
    function testNonAdminCreateMarketReverts() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(evaluator);
        vm.expectRevert("PredictionMarket: caller is not admin");
        market.createMarket(
            marketId,
            caseId,
            keccak256("q"),
            commitDeadline,
            revealDeadline,
            50,
            1000,
            evaluator
        );
    }

    // Step 1b: Insufficient funds test
    function testInsufficientFundsWhenFundingMarket() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        uint256 adminBalance = settlement.simulatedCredits(admin);
        vm.prank(admin);
        vm.expectRevert("Insufficient credits");
        market.createMarket(
            marketId,
            caseId,
            keccak256("q"),
            commitDeadline,
            revealDeadline,
            50,
            adminBalance + 1,
            evaluator
        );
    }

    // Step 1b: Payout totals never exceed funding test
    function testPayoutNeverExceedsFunding() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;
        uint256 funding = 1000;

        vm.prank(admin);
        market.createMarket(
            marketId,
            caseId,
            keccak256("q"),
            commitDeadline,
            revealDeadline,
            50,
            funding,
            evaluator
        );

        vm.prank(evaluator);
        market.publishMarket(marketId);

        // 2 agents commit and reveal
        bytes32 nonce1 = bytes32(uint256(1));
        bytes32 nonce2 = bytes32(uint256(2));
        bytes32 commit1 = keccak256(abi.encodePacked(block.chainid, marketId, agent1, uint256(8000), evidenceDigest, nonce1));
        bytes32 commit2 = keccak256(abi.encodePacked(block.chainid, marketId, agent2, uint256(7000), evidenceDigest, nonce2));

        vm.prank(agent1);
        market.commitForecast(marketId, commit1);
        vm.prank(agent2);
        market.commitForecast(marketId, commit2);

        vm.warp(commitDeadline + 1);
        vm.prank(agent1);
        market.revealForecast(marketId, 8000, evidenceDigest, nonce1);
        vm.prank(agent2);
        market.revealForecast(marketId, 7000, evidenceDigest, nonce2);

        vm.warp(revealDeadline + 1);
        vm.prank(evaluator);
        market.proposeResolution(marketId, true, evidenceDigest);

        vm.warp(block.timestamp + 51);
        vm.prank(evaluator);
        market.settleMarket(marketId);

        uint256 agent1Credits = settlement.simulatedCredits(agent1);
        uint256 agent2Credits = settlement.simulatedCredits(agent2);
        uint256 totalPaid = agent1Credits + agent2Credits;

        assertEq(agent1Credits, 500);
        assertEq(agent2Credits, 500);
        assertEq(totalPaid, funding);
        assertLe(totalPaid, funding);
    }

    // Step 1c: Challenge after deadline reverts
    function testChallengeAfterDeadlineReverts() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(admin);
        market.createMarket(marketId, caseId, keccak256("q"), commitDeadline, revealDeadline, 50, 1000, evaluator);
        vm.prank(evaluator);
        market.publishMarket(marketId);

        vm.warp(revealDeadline + 1);
        vm.prank(evaluator);
        market.proposeResolution(marketId, true, evidenceDigest);

        // Fast forward past challenge deadline
        vm.warp(block.timestamp + 51);

        vm.prank(agent1);
        vm.expectRevert("Challenge window expired");
        market.challengeResolution(marketId, keccak256("reason"));
    }

    // Step 1c: Duplicate challenge reverts
    function testDuplicateChallengeReverts() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(admin);
        market.createMarket(marketId, caseId, keccak256("q"), commitDeadline, revealDeadline, 50, 1000, evaluator);
        vm.prank(evaluator);
        market.publishMarket(marketId);

        vm.warp(revealDeadline + 1);
        vm.prank(evaluator);
        market.proposeResolution(marketId, true, evidenceDigest);

        vm.prank(agent1);
        market.challengeResolution(marketId, keccak256("reason1"));

        vm.prank(agent2);
        vm.expectRevert("Market already challenged");
        market.challengeResolution(marketId, keccak256("reason2"));
    }

    // Step 1c: Non-agent cannot challenge
    function testNonAgentCannotChallenge() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(admin);
        market.createMarket(marketId, caseId, keccak256("q"), commitDeadline, revealDeadline, 50, 1000, evaluator);
        vm.prank(evaluator);
        market.publishMarket(marketId);

        vm.warp(revealDeadline + 1);
        vm.prank(evaluator);
        market.proposeResolution(marketId, true, evidenceDigest);

        vm.prank(maliciousUser);
        vm.expectRevert("PredictionMarket: challenger not active agent");
        market.challengeResolution(marketId, keccak256("reason"));
    }

    // Step 1c: Overturned outcome changes settlement target
    function testOverturnedOutcomeChangesSettlementTarget() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(admin);
        market.createMarket(marketId, caseId, keccak256("q"), commitDeadline, revealDeadline, 50, 1000, evaluator);
        vm.prank(evaluator);
        market.publishMarket(marketId);

        bytes32 nonce = bytes32(uint256(999));
        // Agent 1 forecasts 20% (2000 bps)
        bytes32 commit = keccak256(abi.encodePacked(block.chainid, marketId, agent1, uint256(2000), evidenceDigest, nonce));
        vm.prank(agent1);
        market.commitForecast(marketId, commit);

        vm.warp(commitDeadline + 1);
        vm.prank(agent1);
        market.revealForecast(marketId, 2000, evidenceDigest, nonce);

        vm.warp(revealDeadline + 1);
        // Evaluator proposes TRUE (target = 10000 bps)
        vm.prank(evaluator);
        market.proposeResolution(marketId, true, evidenceDigest);

        // Agent challenges
        vm.prank(agent1);
        market.challengeResolution(marketId, keccak256("new_precedent_shows_no_gap"));

        // Admin overturns outcome to FALSE (target = 0 bps)
        bytes32 overturnedEvidence = keccak256("overturned_digest");
        vm.prank(admin);
        market.resolveChallenge(marketId, false, overturnedEvidence);

        // Fast forward past challenge period
        vm.warp(block.timestamp + 51);

        vm.prank(evaluator);
        market.settleMarket(marketId);

        // Target changed to 0:
        // Diff = |2000 - 0| = 2000. Brier = (2000 * 2000) / 10000 = 400 bps.
        // If outcome had stayed TRUE: diff = |2000 - 10000| = 8000. Brier = 6400 bps.
        (,, uint256 avgBrier,,,) = settlement.agentReputations(agent1);
        assertEq(avgBrier, 400);
    }

    // Step 1d: CLOSED state transition on commit deadline
    function testClosedStateTransitionOnCommitDeadline() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(admin);
        market.createMarket(marketId, caseId, keccak256("q"), commitDeadline, revealDeadline, 50, 1000, evaluator);
        vm.prank(evaluator);
        market.publishMarket(marketId);

        // Before deadline cannot close
        vm.expectRevert("Commit deadline has not passed");
        market.closeMarket(marketId);

        // Warp past commit deadline
        vm.warp(commitDeadline + 1);
        market.closeMarket(marketId);

        (,,,,,,, PredictionMarket.MarketState state,,,,,,,,,,,,) = market.markets(marketId);
        assertEq(uint(state), uint(PredictionMarket.MarketState.CLOSED));
    }

    // Step 1e: Missing reveals rule (FR-051)
    function testMissingRevealRuleFR051() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(admin);
        market.createMarket(marketId, caseId, keccak256("q"), commitDeadline, revealDeadline, 50, 1000, evaluator);
        vm.prank(evaluator);
        market.publishMarket(marketId);

        // Agent 1 and Agent 2 both commit
        bytes32 nonce1 = bytes32(uint256(101));
        bytes32 nonce2 = bytes32(uint256(102));
        bytes32 commit1 = keccak256(abi.encodePacked(block.chainid, marketId, agent1, uint256(8000), evidenceDigest, nonce1));
        bytes32 commit2 = keccak256(abi.encodePacked(block.chainid, marketId, agent2, uint256(7000), evidenceDigest, nonce2));

        vm.prank(agent1);
        market.commitForecast(marketId, commit1);
        vm.prank(agent2);
        market.commitForecast(marketId, commit2);

        vm.warp(commitDeadline + 1);
        // Only Agent 1 reveals! Agent 2 fails to reveal.
        vm.prank(agent1);
        market.revealForecast(marketId, 8000, evidenceDigest, nonce1);

        vm.warp(revealDeadline + 1);
        vm.prank(evaluator);
        market.proposeResolution(marketId, true, evidenceDigest);

        vm.warp(block.timestamp + 51);
        vm.prank(evaluator);
        market.settleMarket(marketId);

        // Revealed agent receives the pool payout
        assertEq(settlement.simulatedCredits(agent1), 1000);
        // Unrevealed agent receives 0 reward credits (FR-051)
        assertEq(settlement.simulatedCredits(agent2), 0);
        // Unrevealed agent receives penalty Brier score (10000 bps)
        (,, uint256 avgBrierAgent2,,,) = settlement.agentReputations(agent2);
        assertEq(avgBrierAgent2, 10000);
    }

    function testLateCommitmentReverts() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(admin);
        market.createMarket(marketId, caseId, keccak256("q"), commitDeadline, revealDeadline, 50, 1000, evaluator);
        vm.prank(evaluator);
        market.publishMarket(marketId);

        // Fast forward past commit deadline
        vm.warp(commitDeadline + 1);

        bytes32 dummyCommit = keccak256("dummy");
        vm.prank(agent1);
        vm.expectRevert("Commitment deadline passed");
        market.commitForecast(marketId, dummyCommit);
    }

    function testCommitmentMismatchReverts() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(admin);
        market.createMarket(marketId, caseId, keccak256("q"), commitDeadline, revealDeadline, 50, 1000, evaluator);
        vm.prank(evaluator);
        market.publishMarket(marketId);

        bytes32 nonce = bytes32(uint256(777));
        bytes32 commitHash = keccak256(
            abi.encodePacked(block.chainid, marketId, agent1, uint256(6000), evidenceDigest, nonce)
        );

        vm.prank(agent1);
        market.commitForecast(marketId, commitHash);

        vm.warp(commitDeadline + 1);

        // Attempt reveal with wrong probability (e.g. 5000 instead of 6000)
        vm.prank(agent1);
        vm.expectRevert("PredictionMarket: commitment mismatch");
        market.revealForecast(marketId, 5000, evidenceDigest, nonce);
    }

    function testUnauthorizedResolutionFails() public {
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;

        vm.prank(admin);
        market.createMarket(marketId, caseId, keccak256("q"), commitDeadline, revealDeadline, 50, 1000, evaluator);
        vm.prank(evaluator);
        market.publishMarket(marketId);

        vm.warp(revealDeadline + 1);

        // Malicious user attempts to propose resolution
        vm.prank(maliciousUser);
        vm.expectRevert("PredictionMarket: unauthorized evaluator");
        market.proposeResolution(marketId, true, evidenceDigest);
    }

    function testDuplicateSettlementReverts() public {
        bytes32 settlementId = keccak256("settlement_unique_1");
        vm.prank(admin);
        settlement.settleForecast(settlementId, marketId, agent1, 500, 100);

        // Second attempt with same settlementId must revert
        vm.prank(admin);
        vm.expectRevert("Settlement already executed");
        settlement.settleForecast(settlementId, marketId, agent1, 500, 100);
    }

    // --- EVIDENCE BOUNTY TESTS (§11, §18.5) ---
    function testEvidenceBountyLifecycle() public {
        uint256 deadline = block.timestamp + 500;
        uint256 challengeDuration = 100;

        vm.prank(admin);
        bounty.createBounty(
            bountyId,
            caseId,
            keccak256("question_bounty"),
            250,
            deadline,
            challengeDuration,
            evaluator
        );

        bytes32 submissionId = keccak256("sub_001");
        vm.prank(contributor);
        bounty.submitEvidence(bountyId, submissionId, evidenceDigest, keccak256("provenance_url"));

        // Duplicate evidence submission must revert (FR-045)
        vm.prank(contributor);
        vm.expectRevert("Duplicate evidence digest already submitted");
        bounty.submitEvidence(bountyId, keccak256("sub_002"), evidenceDigest, keccak256("provenance_url"));

        // Reviewer evaluates submission according to rubric
        vm.prank(evaluator);
        bounty.recordReview(bountyId, submissionId, true, 8500);

        // Fast forward past challenge period
        vm.warp(block.timestamp + challengeDuration + 1);

        // Settle bounty
        vm.prank(evaluator);
        bounty.settleBounty(bountyId);

        assertEq(settlement.simulatedCredits(contributor), 250);
    }

    // Step 1 cleanup: Dust remainder test (pool 100 with 3 agents)
    function testDustRemainderAccounting() public {
        bytes32 dustMarketId = keccak256("mkt_dust_001");
        uint256 commitDeadline = block.timestamp + 100;
        uint256 revealDeadline = block.timestamp + 200;
        uint256 pool = 100; // 100 does not divide evenly by 3

        vm.prank(admin);
        market.createMarket(dustMarketId, caseId, keccak256("q_dust"), commitDeadline, revealDeadline, 50, pool, evaluator);
        vm.prank(evaluator);
        market.publishMarket(dustMarketId);

        bytes32 nonce1 = bytes32(uint256(111));
        bytes32 nonce2 = bytes32(uint256(222));
        bytes32 nonce3 = bytes32(uint256(333));

        bytes32 c1 = keccak256(abi.encodePacked(block.chainid, dustMarketId, agent1, uint256(8000), evidenceDigest, nonce1));
        bytes32 c2 = keccak256(abi.encodePacked(block.chainid, dustMarketId, agent2, uint256(7000), evidenceDigest, nonce2));
        bytes32 c3 = keccak256(abi.encodePacked(block.chainid, dustMarketId, agent3, uint256(6000), evidenceDigest, nonce3));

        vm.prank(agent1);
        market.commitForecast(dustMarketId, c1);
        vm.prank(agent2);
        market.commitForecast(dustMarketId, c2);
        vm.prank(agent3);
        market.commitForecast(dustMarketId, c3);

        vm.warp(commitDeadline + 1);

        vm.prank(agent1);
        market.revealForecast(dustMarketId, 8000, evidenceDigest, nonce1);
        vm.prank(agent2);
        market.revealForecast(dustMarketId, 7000, evidenceDigest, nonce2);
        vm.prank(agent3);
        market.revealForecast(dustMarketId, 6000, evidenceDigest, nonce3);

        vm.warp(revealDeadline + 1);

        vm.prank(evaluator);
        market.proposeResolution(dustMarketId, true, evidenceDigest);

        vm.warp(revealDeadline + 52);

        vm.prank(evaluator);
        market.settleMarket(dustMarketId);

        uint256 remainder = market.getMarketDustRemainder(dustMarketId);
        uint256 payout1 = settlement.simulatedCredits(agent1);
        uint256 payout2 = settlement.simulatedCredits(agent2);
        uint256 payout3 = settlement.simulatedCredits(agent3);
        uint256 sumOfPayouts = payout1 + payout2 + payout3;

        // With pool 100 and 3 agents: perAgentReward = 100 / 3 = 33, totalPayout = 99, remainder = 1
        assertEq(payout1, 33);
        assertEq(payout2, 33);
        assertEq(payout3, 33);
        assertEq(remainder, 1);
        assertEq(sumOfPayouts + remainder, pool, "Exact credit conservation: sum of payouts + remainder == pool");
    }

    event EvaluatorUpdated(address indexed previousEvaluator, address indexed authorizedEvaluator);
    event PredictionMarketUpdated(address indexed previousContract, address indexed predictionMarketContract);
    event EvidenceBountyUpdated(address indexed previousContract, address indexed evidenceBountyContract);

    // Step 1c: ReputationSettlement zero address reverts
    function testReputationSettlementSettersZeroAddressReverts() public {
        vm.startPrank(admin);

        vm.expectRevert("Invalid evaluator");
        settlement.setAuthorizedEvaluator(address(0));

        vm.expectRevert("Invalid prediction market address");
        settlement.setContracts(address(0), address(bounty));

        vm.expectRevert("Invalid evidence bounty address");
        settlement.setContracts(address(market), address(0));

        vm.stopPrank();
    }

    // Step 1c: ReputationSettlement setters emit events
    function testReputationSettlementSettersEmitEvents() public {
        address newEvaluator = address(0x999);
        address newMarket = address(0x888);
        address newBounty = address(0x777);

        vm.startPrank(admin);

        // Expect EvaluatorUpdated event
        vm.expectEmit(true, true, false, false);
        emit EvaluatorUpdated(evaluator, newEvaluator);
        settlement.setAuthorizedEvaluator(newEvaluator);
        assertEq(settlement.authorizedEvaluator(), newEvaluator);

        // Expect PredictionMarketUpdated and EvidenceBountyUpdated events
        vm.expectEmit(true, true, false, false);
        emit PredictionMarketUpdated(address(market), newMarket);
        vm.expectEmit(true, true, false, false);
        emit EvidenceBountyUpdated(address(bounty), newBounty);
        settlement.setContracts(newMarket, newBounty);
        assertEq(settlement.predictionMarketContract(), newMarket);
        assertEq(settlement.evidenceBountyContract(), newBounty);

        vm.stopPrank();
    }
}
