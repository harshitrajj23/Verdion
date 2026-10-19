// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/**
 * @title ReputationSettlement
 * @notice Handles simulated-credit balances, proper scoring rule records (Brier scores),
 * reputation tracking, and idempotent settlement accounting (FR-041, FR-047..FR-053, §10.6, §12.2).
 */
contract ReputationSettlement {
    address public admin;
    address public authorizedEvaluator;
    address public predictionMarketContract;
    address public evidenceBountyContract;

    // Simulated-credit balance (FR-041, FR-050)
    mapping(address => uint256) public simulatedCredits;

    // Settlement deduplication: settlementId => isSettled (FR-052)
    mapping(bytes32 => bool) public executedSettlements;

    struct AgentReputation {
        uint256 totalEvaluated;
        uint256 cumulativeBrierBps; // Sum of Brier scores in Basis Points (0 - 10000)
        uint256 averageBrierBps;    // Average Brier score (lower is better)
        uint256 reputationScore;    // 0 - 1000 scale
        uint256 totalCreditsEarned;
        uint256 lastUpdated;
    }

    mapping(address => AgentReputation) public agentReputations;

    event CreditsMinted(address indexed recipient, uint256 amount);
    event CreditsTransferred(address indexed from, address indexed to, uint256 amount);
    event EvaluatorUpdated(address indexed previousEvaluator, address indexed authorizedEvaluator);
    event PredictionMarketUpdated(address indexed previousContract, address indexed predictionMarketContract);
    event EvidenceBountyUpdated(address indexed previousContract, address indexed evidenceBountyContract);
    event SettlementExecuted(
        bytes32 indexed settlementId,
        bytes32 indexed targetId,
        address indexed participant,
        uint256 brierBps,
        uint256 rewardCredits,
        uint256 timestamp
    );
    event ReputationUpdated(address indexed agent, uint256 totalEvaluated, uint256 averageBrierBps, uint256 reputationScore);

    modifier onlyAdmin() {
        require(msg.sender == admin, "ReputationSettlement: caller is not admin");
        _;
    }

    modifier onlyAuthorizedCaller() {
        require(
            msg.sender == admin ||
            msg.sender == authorizedEvaluator ||
            msg.sender == predictionMarketContract ||
            msg.sender == evidenceBountyContract,
            "ReputationSettlement: unauthorized caller"
        );
        _;
    }

    constructor() {
        admin = msg.sender;
        authorizedEvaluator = msg.sender;
        emit EvaluatorUpdated(address(0), msg.sender);
    }

    function setAuthorizedEvaluator(address _evaluator) external onlyAdmin {
        require(_evaluator != address(0), "Invalid evaluator");
        address oldEvaluator = authorizedEvaluator;
        authorizedEvaluator = _evaluator;
        emit EvaluatorUpdated(oldEvaluator, _evaluator);
    }

    function setContracts(address _predictionMarket, address _evidenceBounty) external onlyAdmin {
        require(_predictionMarket != address(0), "Invalid prediction market address");
        require(_evidenceBounty != address(0), "Invalid evidence bounty address");
        address oldMarket = predictionMarketContract;
        address oldBounty = evidenceBountyContract;
        predictionMarketContract = _predictionMarket;
        emit PredictionMarketUpdated(oldMarket, _predictionMarket);
        evidenceBountyContract = _evidenceBounty;
        emit EvidenceBountyUpdated(oldBounty, _evidenceBounty);
    }

    /**
     * @notice Demo faucet for simulated credits
     */
    function mintSimulatedCredits(address recipient, uint256 amount) external onlyAuthorizedCaller {
        require(recipient != address(0), "Invalid recipient");
        simulatedCredits[recipient] += amount;
        emit CreditsMinted(recipient, amount);
    }

    /**
     * @notice Transfers simulated credits between participants
     */
    function transferCredits(address from, address to, uint256 amount) external onlyAuthorizedCaller {
        require(simulatedCredits[from] >= amount, "Insufficient credits");
        simulatedCredits[from] -= amount;
        simulatedCredits[to] += amount;
        emit CreditsTransferred(from, to, amount);
    }

    /**
     * @notice Records a forecast settlement idempotently and updates Brier score & reputation (FR-048, FR-052)
     */
    function settleForecast(
        bytes32 settlementId,
        bytes32 marketId,
        address agent,
        uint256 brierScoreBps, // (p - y)^2 in basis points [0..10000]
        uint256 rewardCredits
    ) external onlyAuthorizedCaller {
        require(!executedSettlements[settlementId], "Settlement already executed");
        require(agent != address(0), "Invalid agent address");
        require(brierScoreBps <= 10000, "Brier score exceeds 10000 bps");

        executedSettlements[settlementId] = true;

        // Credit reward
        if (rewardCredits > 0) {
            if (msg.sender == predictionMarketContract) {
                require(simulatedCredits[msg.sender] >= rewardCredits, "ReputationSettlement: insufficient market funds");
                simulatedCredits[msg.sender] -= rewardCredits;
            }
            simulatedCredits[agent] += rewardCredits;
        }

        // Update Reputation & Brier score history (FR-047, FR-048)
        AgentReputation storage rep = agentReputations[agent];
        rep.totalEvaluated += 1;
        rep.cumulativeBrierBps += brierScoreBps;
        rep.averageBrierBps = rep.cumulativeBrierBps / rep.totalEvaluated;
        rep.totalCreditsEarned += rewardCredits;
        rep.lastUpdated = block.timestamp;

        // Proper scoring rule reputation metric (FR-049: guard against small sample inflation)
        // Score = (10000 - avgBrier) * min(N, 10) / 10
        uint256 rawQuality = 10000 > rep.averageBrierBps ? (10000 - rep.averageBrierBps) : 0;
        uint256 sampleWeight = rep.totalEvaluated >= 10 ? 10 : rep.totalEvaluated;
        rep.reputationScore = (rawQuality * sampleWeight) / 100; // Normalized 0..1000

        emit SettlementExecuted(settlementId, marketId, agent, brierScoreBps, rewardCredits, block.timestamp);
        emit ReputationUpdated(agent, rep.totalEvaluated, rep.averageBrierBps, rep.reputationScore);
    }

    /**
     * @notice Records an evidence bounty settlement idempotently (FR-050, FR-052)
     */
    function settleBounty(
        bytes32 settlementId,
        bytes32 bountyId,
        address contributor,
        uint256 rewardCredits
    ) external onlyAuthorizedCaller {
        require(!executedSettlements[settlementId], "Settlement already executed");
        require(contributor != address(0), "Invalid contributor address");

        executedSettlements[settlementId] = true;
        simulatedCredits[contributor] += rewardCredits;

        emit SettlementExecuted(settlementId, bountyId, contributor, 0, rewardCredits, block.timestamp);
    }

    function isSettled(bytes32 settlementId) external view returns (bool) {
        return executedSettlements[settlementId];
    }
}
