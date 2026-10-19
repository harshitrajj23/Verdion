// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ReputationSettlement
 * @dev On-chain settlement record, Brier score calibration tracking, and credit accounting.
 * PRD Section 12.2: Record authorized scores and simulated rewards; settlement idempotency
 */
contract ReputationSettlement {
    address public evaluator;
    address public admin;

    struct AgentMetric {
        uint256 sampleCount;
        uint256 totalBrierScoreBps;
        uint256 simulatedCredits;
    }

    mapping(address => AgentMetric) public agentMetrics;
    mapping(bytes32 => bool) public settledTransactions;

    event ScoreRecorded(address indexed agentAddress, uint256 brierScoreBps, uint256 updatedCreditBalance);
    event SettlementExecuted(bytes32 indexed settlementKey, address indexed recipient, uint256 rewardAmount);

    modifier onlyEvaluator() {
        require(msg.sender == evaluator || msg.sender == admin, "Caller not authorized evaluator");
        _;
    }

    constructor(address _evaluator) {
        admin = msg.sender;
        evaluator = _evaluator;
    }

    function recordScoreAndReward(
        address agentAddress,
        uint256 brierScoreBps,
        uint256 rewardCredits,
        bytes32 settlementKey
    ) external onlyEvaluator {
        require(!settledTransactions[settlementKey], "Settlement already processed for this key");

        settledTransactions[settlementKey] = true;

        AgentMetric storage m = agentMetrics[agentAddress];
        m.sampleCount += 1;
        m.totalBrierScoreBps += brierScoreBps;
        m.simulatedCredits += rewardCredits;

        emit ScoreRecorded(agentAddress, brierScoreBps, m.simulatedCredits);
        emit SettlementExecuted(settlementKey, agentAddress, rewardCredits);
    }

    function getAverageBrierBps(address agentAddress) external view returns (uint256) {
        AgentMetric memory m = agentMetrics[agentAddress];
        if (m.sampleCount == 0) return 2500; // default 0.25 in bps
        return m.totalBrierScoreBps / m.sampleCount;
    }
}
