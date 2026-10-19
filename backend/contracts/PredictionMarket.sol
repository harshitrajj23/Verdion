// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title PredictionMarket
 * @dev On-chain forecast commitments, reveals, challenge periods, and authorized settlement.
 * PRD Section 10 & 12.2: Commit-reveal with H(chainId, marketId, agentId, prob, digest, nonce)
 */
contract PredictionMarket {
    address public evaluator;
    address public admin;

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
        string marketId;
        string caseId;
        uint256 commitDeadline;
        uint256 revealDeadline;
        uint256 resolutionDeadline;
        uint256 challengeWindow;
        MarketState state;
        uint8 proposedOutcome; // 0 or 1
        string resolutionReference;
        uint256 totalReveals;
        uint256 aggregateProbBps;
    }

    struct ForecastCommitment {
        bytes32 commitmentHash;
        uint256 probBps;
        bytes32 evidenceDigest;
        bool revealed;
    }

    // marketId => Market
    mapping(string => Market) public markets;
    // marketId => agentId => ForecastCommitment
    mapping(string => mapping(string => ForecastCommitment)) public commitments;
    // marketId => agentId => hasCommitted
    mapping(string => mapping(string => bool)) public hasCommitted;

    event MarketCreated(string indexed marketId, string caseId, uint256 commitDeadline, uint256 revealDeadline);
    event ForecastCommitted(string indexed marketId, string agentId, bytes32 commitmentHash);
    event ForecastRevealed(string indexed marketId, string agentId, uint256 probBps, bytes32 evidenceDigest);
    event ResolutionProposed(string indexed marketId, uint8 outcome, string resolutionReference);
    event MarketChallenged(string indexed marketId, address indexed challenger, string reason);
    event MarketSettled(string indexed marketId, uint8 finalOutcome, uint256 totalReveals);

    modifier onlyEvaluator() {
        require(msg.sender == evaluator || msg.sender == admin, "PredictionMarket: caller not evaluator");
        _;
    }

    constructor(address _evaluator) {
        admin = msg.sender;
        evaluator = _evaluator;
    }

    function createMarket(
        string calldata marketId,
        string calldata caseId,
        uint256 commitDeadline,
        uint256 revealDeadline,
        uint256 resolutionDeadline,
        uint256 challengeWindow
    ) external {
        require(markets[marketId].commitDeadline == 0, "Market already exists");
        require(commitDeadline > block.timestamp, "Commit deadline must be future");
        require(revealDeadline > commitDeadline, "Reveal deadline must follow commit");

        markets[marketId] = Market({
            marketId: marketId,
            caseId: caseId,
            commitDeadline: commitDeadline,
            revealDeadline: revealDeadline,
            resolutionDeadline: resolutionDeadline,
            challengeWindow: challengeWindow,
            state: MarketState.PUBLISHED,
            proposedOutcome: 0,
            resolutionReference: "",
            totalReveals: 0,
            aggregateProbBps: 0
        });

        emit MarketCreated(marketId, caseId, commitDeadline, revealDeadline);
    }

    function commitForecast(
        string calldata marketId,
        string calldata agentId,
        bytes32 commitmentHash
    ) external {
        Market storage m = markets[marketId];
        require(m.state == MarketState.PUBLISHED, "Market not accepting commitments");
        require(block.timestamp <= m.commitDeadline, "Commitment deadline passed");
        require(!hasCommitted[marketId][agentId], "Agent already committed");

        commitments[marketId][agentId] = ForecastCommitment({
            commitmentHash: commitmentHash,
            probBps: 0,
            evidenceDigest: bytes32(0),
            revealed: false
        });
        hasCommitted[marketId][agentId] = true;

        emit ForecastCommitted(marketId, agentId, commitmentHash);
    }

    function revealForecast(
        string calldata marketId,
        string calldata agentId,
        uint256 probBps,
        bytes32 evidenceDigest,
        bytes32 nonce
    ) external {
        Market storage m = markets[marketId];
        require(m.state == MarketState.PUBLISHED || m.state == MarketState.REVEAL, "Market not in reveal stage");
        require(probBps <= 10000, "Probability BPS must be <= 10000");

        ForecastCommitment storage fc = commitments[marketId][agentId];
        require(hasCommitted[marketId][agentId], "No commitment exists");
        require(!fc.revealed, "Already revealed");

        // Verify hash matching PRD Section 10.4:
        // H(chainId, marketId, agentId, probability, evidenceDigest, nonce)
        bytes32 computedHash = keccak256(
            abi.encode(block.chainid, marketId, agentId, probBps, evidenceDigest, nonce)
        );
        require(computedHash == fc.commitmentHash, "Commitment mismatch");

        fc.revealed = true;
        fc.probBps = probBps;
        fc.evidenceDigest = evidenceDigest;

        m.totalReveals += 1;
        m.aggregateProbBps = (m.aggregateProbBps * (m.totalReveals - 1) + probBps) / m.totalReveals;
        m.state = MarketState.REVEAL;

        emit ForecastRevealed(marketId, agentId, probBps, evidenceDigest);
    }

    function proposeResolution(
        string calldata marketId,
        uint8 proposedOutcome,
        string calldata resolutionReference
    ) external onlyEvaluator {
        Market storage m = markets[marketId];
        require(m.state != MarketState.SETTLED && m.state != MarketState.VOID, "Cannot resolve settled market");
        require(proposedOutcome <= 1, "Outcome must be 0 or 1");

        m.proposedOutcome = proposedOutcome;
        m.resolutionReference = resolutionReference;
        m.state = MarketState.RESOLUTION_PROPOSED;

        emit ResolutionProposed(marketId, proposedOutcome, resolutionReference);
    }

    function challengeResolution(string calldata marketId, string calldata reason) external {
        Market storage m = markets[marketId];
        require(m.state == MarketState.RESOLUTION_PROPOSED, "Not in challenge stage");
        m.state = MarketState.CHALLENGE;
        emit MarketChallenged(marketId, msg.sender, reason);
    }

    function settleMarket(string calldata marketId) external onlyEvaluator {
        Market storage m = markets[marketId];
        require(m.state == MarketState.RESOLUTION_PROPOSED || m.state == MarketState.CHALLENGE, "Not ready for settlement");
        m.state = MarketState.SETTLED;
        emit MarketSettled(marketId, m.proposedOutcome, m.totalReveals);
    }
}
