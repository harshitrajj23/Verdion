// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "./AgentRegistry.sol";
import "./ReputationSettlement.sol";

/**
 * @title PredictionMarket
 * @notice Binary evaluation forecast market with commit-reveal scheme, state machine,
 * challenge window, and proper scoring rule settlement (PRD §10, §12.2, FR-031..FR-039).
 */
contract PredictionMarket {
    enum MarketState {
        DRAFT,
        PUBLISHED,
        REVEAL,
        CLOSED,
        RESOLUTION_PROPOSED,
        CHALLENGE,
        SETTLED,
        VOID
    }

    struct Market {
        bytes32 marketId;
        bytes32 caseId;
        bytes32 questionHash;
        uint256 commitDeadline;
        uint256 revealDeadline;
        uint256 challengeDuration;
        uint256 challengeDeadline;
        MarketState state;
        bool proposedOutcome; // true = YES / COMPLIANCE_GAP, false = NO
        bytes32 resolutionEvidenceDigest;
        address authorizedEvaluator;
        uint256 totalCommitted;
        uint256 totalRevealed;
        uint256 totalRewardPool;
        uint256 fundedAmount;
        uint256 totalPaidOut;
        address challenger;
        bytes32 challengeReasonHash;
        bool challengeResolved;
        uint256 dustRemainder;
    }

    struct ForecastCommitment {
        bytes32 commitmentHash;
        uint256 committedAt;
        bool revealed;
        uint256 probabilityBps; // Revealed probability in Basis Points (0..10000)
        bytes32 evidenceDigest;
    }

    address public admin;
    bool public paused;
    AgentRegistry public immutable agentRegistry;
    ReputationSettlement public immutable settlementContract;

    // marketId => Market
    mapping(bytes32 => Market) public markets;
    // marketId => agentAddress => ForecastCommitment
    mapping(bytes32 => mapping(address => ForecastCommitment)) public commitments;
    // marketId => list of committed agent addresses (FR-051)
    mapping(bytes32 => address[]) internal committedAgents;
    // marketId => list of revealed agent addresses
    mapping(bytes32 => address[]) internal revealedAgents;

    event MarketCreated(bytes32 indexed marketId, bytes32 indexed caseId, uint256 commitDeadline, uint256 revealDeadline, address indexed evaluator);
    event MarketFunded(bytes32 indexed marketId, uint256 amountFunded, uint256 totalRewardPool);
    event MarketPublished(bytes32 indexed marketId);
    event MarketClosed(bytes32 indexed marketId);
    event ForecastCommitted(bytes32 indexed marketId, address indexed agent, bytes32 commitmentHash, uint256 timestamp);
    event ForecastRevealed(bytes32 indexed marketId, address indexed agent, uint256 probabilityBps, bytes32 evidenceDigest);
    event ResolutionProposed(bytes32 indexed marketId, bool outcome, bytes32 resolutionEvidenceDigest, uint256 challengeDeadline);
    event ResolutionChallenged(bytes32 indexed marketId, address indexed challenger, bytes32 reasonHash);
    event ChallengeResolved(bytes32 indexed marketId, bool finalOutcome, bytes32 evidenceDigest, bool overturned);
    event MarketSettled(bytes32 indexed marketId, bool finalOutcome, uint256 totalRevealed, uint256 timestamp);
    event MarketVoided(bytes32 indexed marketId, bytes32 reason);
    event Paused(address account);
    event Unpaused(address account);

    modifier onlyAdmin() {
        require(msg.sender == admin, "PredictionMarket: caller is not admin");
        _;
    }

    modifier onlyEvaluator(bytes32 marketId) {
        require(
            msg.sender == markets[marketId].authorizedEvaluator || msg.sender == admin,
            "PredictionMarket: unauthorized evaluator"
        );
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "PredictionMarket: paused");
        _;
    }

    constructor(address _agentRegistry, address _settlementContract) {
        require(_agentRegistry != address(0) && _settlementContract != address(0), "Invalid constructor addresses");
        admin = msg.sender;
        agentRegistry = AgentRegistry(_agentRegistry);
        settlementContract = ReputationSettlement(_settlementContract);
    }

    function setPaused(bool _paused) external onlyAdmin {
        paused = _paused;
        if (_paused) {
            emit Paused(msg.sender);
        } else {
            emit Unpaused(msg.sender);
        }
    }

    /**
     * @notice Creates a new forecast market in DRAFT state (FR-031). Restriced to admin.
     * Funds the reward pool from the caller's credit ledger balance.
     */
    function createMarket(
        bytes32 marketId,
        bytes32 caseId,
        bytes32 questionHash,
        uint256 commitDeadline,
        uint256 revealDeadline,
        uint256 challengeDuration,
        uint256 rewardPool,
        address evaluator
    ) external onlyAdmin whenNotPaused {
        require(marketId != bytes32(0), "Invalid marketId");
        require(markets[marketId].marketId == bytes32(0), "Market already exists");
        require(commitDeadline > block.timestamp, "Commit deadline must be in future");
        require(revealDeadline > commitDeadline, "Reveal deadline must follow commit deadline");
        require(evaluator != address(0), "Invalid evaluator");

        markets[marketId] = Market({
            marketId: marketId,
            caseId: caseId,
            questionHash: questionHash,
            commitDeadline: commitDeadline,
            revealDeadline: revealDeadline,
            challengeDuration: challengeDuration,
            challengeDeadline: 0,
            state: MarketState.DRAFT,
            proposedOutcome: false,
            resolutionEvidenceDigest: bytes32(0),
            authorizedEvaluator: evaluator,
            totalCommitted: 0,
            totalRevealed: 0,
            totalRewardPool: rewardPool,
            fundedAmount: rewardPool,
            totalPaidOut: 0,
            challenger: address(0),
            challengeReasonHash: bytes32(0),
            challengeResolved: false,
            dustRemainder: 0
        });

        emit MarketCreated(marketId, caseId, commitDeadline, revealDeadline, evaluator);
        if (rewardPool > 0) {
            emit MarketFunded(marketId, rewardPool, rewardPool);
            settlementContract.transferCredits(msg.sender, address(this), rewardPool);
        }
    }

    /**
     * @notice Adds additional simulated credits to a market reward pool from the admin's balance.
     */
    function fundMarket(bytes32 marketId, uint256 amount) external onlyAdmin whenNotPaused {
        Market storage m = markets[marketId];
        require(m.marketId != bytes32(0), "Market does not exist");
        require(m.state != MarketState.SETTLED && m.state != MarketState.VOID, "Market already settled or void");
        require(amount > 0, "Amount must be positive");

        m.totalRewardPool += amount;
        m.fundedAmount += amount;
        emit MarketFunded(marketId, amount, m.totalRewardPool);

        settlementContract.transferCredits(msg.sender, address(this), amount);
    }

    /**
     * @notice Publishes market, opening the commitment window (FR-031, §10.3)
     */
    function publishMarket(bytes32 marketId) external onlyEvaluator(marketId) whenNotPaused {
        Market storage m = markets[marketId];
        require(m.state == MarketState.DRAFT, "PredictionMarket: market not in DRAFT state");
        require(block.timestamp < m.commitDeadline, "Commit deadline already passed");

        m.state = MarketState.PUBLISHED;
        emit MarketPublished(marketId);
    }

    /**
     * @notice Transitions market to CLOSED when commit deadline has elapsed (§10.4, threat model).
     */
    function closeMarket(bytes32 marketId) external whenNotPaused {
        Market storage m = markets[marketId];
        require(block.timestamp > m.commitDeadline, "Commit deadline has not passed");
        require(
            m.state == MarketState.PUBLISHED || m.state == MarketState.REVEAL,
            "Invalid state for closing"
        );

        m.state = MarketState.CLOSED;
        emit MarketClosed(marketId);
    }

    /**
     * @notice Submits a commit hash H(chainId, marketId, agent, prob, digest, nonce) (FR-033, §10.4)
     */
    function commitForecast(bytes32 marketId, bytes32 commitmentHash) external whenNotPaused {
        Market storage m = markets[marketId];
        require(m.state == MarketState.PUBLISHED, "Market not accepting commitments");
        require(block.timestamp <= m.commitDeadline, "Commitment deadline passed");
        require(commitmentHash != bytes32(0), "Invalid commitment hash");
        require(commitments[marketId][msg.sender].commitmentHash == bytes32(0), "Duplicate commitment not allowed");
        require(agentRegistry.isAgentActive(msg.sender), "Agent not active in registry");

        commitments[marketId][msg.sender] = ForecastCommitment({
            commitmentHash: commitmentHash,
            committedAt: block.timestamp,
            revealed: false,
            probabilityBps: 0,
            evidenceDigest: bytes32(0)
        });

        committedAgents[marketId].push(msg.sender);
        m.totalCommitted += 1;
        emit ForecastCommitted(marketId, msg.sender, commitmentHash, block.timestamp);
    }

    /**
     * @notice Reveals forecast and validates against original commitment (FR-034, §10.4)
     */
    function revealForecast(
        bytes32 marketId,
        uint256 probabilityBps,
        bytes32 evidenceDigest,
        bytes32 nonce
    ) external whenNotPaused {
        Market storage m = markets[marketId];
        require(block.timestamp > m.commitDeadline, "Reveal window not open yet");
        require(block.timestamp <= m.revealDeadline, "Reveal deadline passed");
        require(probabilityBps <= 10000, "Probability basis points must be <= 10000");

        if (m.state == MarketState.PUBLISHED || m.state == MarketState.CLOSED) {
            m.state = MarketState.REVEAL;
        }
        require(m.state == MarketState.REVEAL, "Market not in REVEAL state");

        ForecastCommitment storage c = commitments[marketId][msg.sender];
        require(c.commitmentHash != bytes32(0), "No commitment found for caller");
        require(!c.revealed, "Already revealed");

        // Canonical commitment reconstruction matching §10.4:
        // H(chainId, marketId, agentId, probability, evidenceDigest, nonce)
        bytes32 expectedHash = keccak256(
            abi.encodePacked(
                block.chainid,
                marketId,
                msg.sender,
                probabilityBps,
                evidenceDigest,
                nonce
            )
        );

        require(expectedHash == c.commitmentHash, "PredictionMarket: commitment mismatch");

        c.revealed = true;
        c.probabilityBps = probabilityBps;
        c.evidenceDigest = evidenceDigest;

        revealedAgents[marketId].push(msg.sender);
        m.totalRevealed += 1;

        emit ForecastRevealed(marketId, msg.sender, probabilityBps, evidenceDigest);
    }

    /**
     * @notice Evaluator proposes resolution outcome, opening challenge window (FR-038, §10.5)
     */
    function proposeResolution(
        bytes32 marketId,
        bool outcome,
        bytes32 resolutionEvidenceDigest
    ) external onlyEvaluator(marketId) whenNotPaused {
        Market storage m = markets[marketId];
        require(block.timestamp > m.revealDeadline, "Reveal deadline has not passed");
        require(
            m.state == MarketState.REVEAL || m.state == MarketState.PUBLISHED || m.state == MarketState.CLOSED,
            "Invalid state for resolution"
        );

        m.proposedOutcome = outcome;
        m.resolutionEvidenceDigest = resolutionEvidenceDigest;
        m.challengeDeadline = block.timestamp + m.challengeDuration;
        m.state = MarketState.RESOLUTION_PROPOSED;

        emit ResolutionProposed(marketId, outcome, resolutionEvidenceDigest, m.challengeDeadline);
    }

    /**
     * @notice Allows registered agent participants to challenge resolution within challenge window (FR-046, §12.2)
     */
    function challengeResolution(bytes32 marketId, bytes32 reasonHash) external whenNotPaused {
        Market storage m = markets[marketId];
        require(m.challenger == address(0), "Market already challenged");
        require(m.state == MarketState.RESOLUTION_PROPOSED, "Not in RESOLUTION_PROPOSED state");
        require(block.timestamp <= m.challengeDeadline, "Challenge window expired");
        require(reasonHash != bytes32(0), "Reason hash cannot be empty");
        require(agentRegistry.isAgentActive(msg.sender), "PredictionMarket: challenger not active agent");

        m.challenger = msg.sender;
        m.challengeReasonHash = reasonHash;
        m.state = MarketState.CHALLENGE;

        emit ResolutionChallenged(marketId, msg.sender, reasonHash);
    }

    /**
     * @notice Resolves a pending challenge, upholding or overturning the proposed outcome.
     * Callable only by admin. Allows settlement once resolved.
     */
    function resolveChallenge(
        bytes32 marketId,
        bool outcome,
        bytes32 evidenceDigest
    ) external onlyAdmin whenNotPaused {
        Market storage m = markets[marketId];
        require(m.state == MarketState.CHALLENGE, "Market not in CHALLENGE state");
        require(evidenceDigest != bytes32(0), "Invalid evidence digest");

        bool overturned = (outcome != m.proposedOutcome);
        m.proposedOutcome = outcome;
        m.resolutionEvidenceDigest = evidenceDigest;
        m.challengeResolved = true;
        m.state = MarketState.RESOLUTION_PROPOSED;

        emit ChallengeResolved(marketId, outcome, evidenceDigest, overturned);
    }

    /**
     * @notice Settles market and executes idempotent payouts and Brier score tracking (FR-048..FR-052).
     * FR-051 Missing Reveals Rule: unrevealed commitments score zero/max error and receive no reward.
     */
    function settleMarket(bytes32 marketId) external onlyEvaluator(marketId) whenNotPaused {
        Market storage m = markets[marketId];
        require(
            m.state == MarketState.RESOLUTION_PROPOSED,
            "Market not ready for settlement"
        );
        require(block.timestamp > m.challengeDeadline, "Challenge period still active");
        if (m.challenger != address(0)) {
            require(m.challengeResolved, "Challenge not resolved");
        }

        m.state = MarketState.SETTLED;
        uint256 n = revealedAgents[marketId].length;

        uint256 perAgentReward = 0;
        uint256 totalPayout = 0;
        uint256 remainder = 0;
        uint256 targetBps = m.proposedOutcome ? 10000 : 0;

        if (n > 0) {
            perAgentReward = m.totalRewardPool / n;
            totalPayout = perAgentReward * n;
            remainder = m.totalRewardPool - totalPayout;

            require(m.totalRewardPool >= totalPayout, "PredictionMarket: insufficient reward pool");
            m.totalRewardPool -= totalPayout;
            m.totalPaidOut += totalPayout;
            m.dustRemainder = remainder;
            require(m.totalPaidOut <= m.fundedAmount, "PredictionMarket: payout exceeds funding");
        }

        emit MarketSettled(marketId, m.proposedOutcome, n, block.timestamp);

        // FR-051 Rule: Missing reveals receive zero reward and maximum Brier penalty (10000 bps)
        uint256 totalCommittedCount = committedAgents[marketId].length;
        for (uint256 j = 0; j < totalCommittedCount; j++) {
            address committer = committedAgents[marketId][j];
            if (!commitments[marketId][committer].revealed) {
                bytes32 unrevealedSettlementId = keccak256(abi.encodePacked(marketId, committer, "unrevealed", block.chainid));
                settlementContract.settleForecast(unrevealedSettlementId, marketId, committer, 10000, 0);
            }
        }

        for (uint256 i = 0; i < n; i++) {
            address agent = revealedAgents[marketId][i];
            ForecastCommitment memory c = commitments[marketId][agent];

            // Brier score calculation: (p - y)^2
            // Since p and y are in bps [0..10000], diff is in [0..10000]
            uint256 diff = c.probabilityBps > targetBps ? (c.probabilityBps - targetBps) : (targetBps - c.probabilityBps);
            // (diff * diff) / 10000 gives Brier score in bps
            uint256 brierBps = (diff * diff) / 10000;

            bytes32 settlementId = keccak256(abi.encodePacked(marketId, agent, block.chainid));
            settlementContract.settleForecast(settlementId, marketId, agent, brierBps, perAgentReward);
        }
    }

    function getMarketDustRemainder(bytes32 marketId) external view returns (uint256) {
        return markets[marketId].dustRemainder;
    }

    /**
     * @notice Voids market when resolution criteria cannot be established (FR-039)
     */
    function voidMarket(bytes32 marketId, bytes32 reason) external onlyEvaluator(marketId) whenNotPaused {
        Market storage m = markets[marketId];
        require(m.state != MarketState.SETTLED, "Market already settled");
        m.state = MarketState.VOID;
        emit MarketVoided(marketId, reason);
    }

    function getRevealedAgents(bytes32 marketId) external view returns (address[] memory) {
        return revealedAgents[marketId];
    }

    function getCommittedAgents(bytes32 marketId) external view returns (address[] memory) {
        return committedAgents[marketId];
    }
}
