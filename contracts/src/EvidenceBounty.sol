// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "./ReputationSettlement.sol";

/**
 * @title EvidenceBounty
 * @notice Protocol for funding, submitting, reviewing, challenging, and settling evidence bounties
 * using simulated credits (PRD §11, §12.2, FR-040..FR-046).
 */
contract EvidenceBounty {
    enum BountyState {
        CREATED,
        FUNDED,
        OPEN,
        REVIEW,
        CHALLENGE,
        AWARDED,
        REJECTED,
        CANCELLED,
        SETTLED
    }

    struct Submission {
        bytes32 submissionId;
        address contributor;
        bytes32 evidenceDigest;
        bytes32 provenanceHash;
        uint256 submittedAt;
        bool isAccepted;
        uint256 scoreBps; // Rubric score in bps (0..10000)
    }

    struct Bounty {
        bytes32 bountyId;
        bytes32 caseId;
        bytes32 questionHash;
        uint256 rewardCredits;
        uint256 deadline;
        uint256 challengeDuration;
        uint256 challengeDeadline;
        BountyState state;
        address reviewer;
        address creator;
        bytes32 winningSubmissionId;
        address challenger;
        bytes32 challengeReasonHash;
    }

    address public admin;
    bool public paused;
    ReputationSettlement public immutable settlementContract;

    // bountyId => Bounty
    mapping(bytes32 => Bounty) public bounties;
    // bountyId => submissionId => Submission
    mapping(bytes32 => mapping(bytes32 => Submission)) public submissions;
    // bountyId => list of submissionIds
    mapping(bytes32 => bytes32[]) internal bountySubmissionList;
    // bountyId => evidenceDigest => exists (FR-045 duplicate check)
    mapping(bytes32 => mapping(bytes32 => bool)) public digestSubmitted;

    event BountyCreated(bytes32 indexed bountyId, bytes32 indexed caseId, uint256 rewardCredits, uint256 deadline, address indexed reviewer);
    event BountyFunded(bytes32 indexed bountyId, uint256 rewardCredits);
    event EvidenceSubmitted(bytes32 indexed bountyId, bytes32 indexed submissionId, address indexed contributor, bytes32 evidenceDigest);
    event ReviewRecorded(bytes32 indexed bountyId, bytes32 indexed submissionId, bool isAccepted, uint256 scoreBps, uint256 challengeDeadline);
    event DecisionChallenged(bytes32 indexed bountyId, address indexed challenger, bytes32 reasonHash);
    event WinningSubmissionSelected(bytes32 indexed bountyId, bytes32 indexed winningSubmissionId);
    event BountySettled(bytes32 indexed bountyId, bytes32 indexed winningSubmissionId, address indexed recipient, uint256 rewardCredits);
    event BountyCancelled(bytes32 indexed bountyId, bytes32 reason);
    event Paused(address account);
    event Unpaused(address account);

    modifier onlyAdmin() {
        require(msg.sender == admin, "EvidenceBounty: caller is not admin");
        _;
    }

    modifier onlyReviewer(bytes32 bountyId) {
        require(
            msg.sender == bounties[bountyId].reviewer || msg.sender == admin,
            "EvidenceBounty: unauthorized reviewer"
        );
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "EvidenceBounty: paused");
        _;
    }

    constructor(address _settlementContract) {
        require(_settlementContract != address(0), "Invalid settlement contract");
        admin = msg.sender;
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
     * @notice Creates a new evidence bounty (FR-040)
     */
    function createBounty(
        bytes32 bountyId,
        bytes32 caseId,
        bytes32 questionHash,
        uint256 rewardCredits,
        uint256 deadline,
        uint256 challengeDuration,
        address reviewer
    ) external whenNotPaused {
        require(bountyId != bytes32(0), "Invalid bountyId");
        require(bounties[bountyId].bountyId == bytes32(0), "Bounty already exists");
        require(rewardCredits > 0, "Reward must be positive");
        require(deadline > block.timestamp, "Deadline must be in future");
        require(reviewer != address(0), "Invalid reviewer");

        bounties[bountyId] = Bounty({
            bountyId: bountyId,
            caseId: caseId,
            questionHash: questionHash,
            rewardCredits: rewardCredits,
            deadline: deadline,
            challengeDuration: challengeDuration,
            challengeDeadline: 0,
            state: BountyState.OPEN,
            reviewer: reviewer,
            creator: msg.sender,
            winningSubmissionId: bytes32(0),
            challenger: address(0),
            challengeReasonHash: bytes32(0)
        });

        emit BountyCreated(bountyId, caseId, rewardCredits, deadline, reviewer);
    }

    /**
     * @notice Submits evidence reference with provenance hash and canonical digest (FR-042)
     */
    function submitEvidence(
        bytes32 bountyId,
        bytes32 submissionId,
        bytes32 evidenceDigest,
        bytes32 provenanceHash
    ) external whenNotPaused {
        Bounty storage b = bounties[bountyId];
        require(b.state == BountyState.OPEN, "Bounty is not open for submissions");
        require(block.timestamp <= b.deadline, "Bounty deadline has expired");
        require(submissionId != bytes32(0), "Invalid submissionId");
        require(evidenceDigest != bytes32(0), "Invalid evidenceDigest");
        require(!digestSubmitted[bountyId][evidenceDigest], "Duplicate evidence digest already submitted");

        digestSubmitted[bountyId][evidenceDigest] = true;
        submissions[bountyId][submissionId] = Submission({
            submissionId: submissionId,
            contributor: msg.sender,
            evidenceDigest: evidenceDigest,
            provenanceHash: provenanceHash,
            submittedAt: block.timestamp,
            isAccepted: false,
            scoreBps: 0
        });

        bountySubmissionList[bountyId].push(submissionId);
        emit EvidenceSubmitted(bountyId, submissionId, msg.sender, evidenceDigest);
    }

    /**
     * @notice Records reviewer evaluation according to rubric and begins challenge window (FR-043, FR-044)
     */
    function recordReview(
        bytes32 bountyId,
        bytes32 submissionId,
        bool isAccepted,
        uint256 scoreBps
    ) external onlyReviewer(bountyId) whenNotPaused {
        Bounty storage b = bounties[bountyId];
        require(b.state == BountyState.OPEN || b.state == BountyState.REVIEW, "Invalid state for review");
        require(submissions[bountyId][submissionId].submissionId != bytes32(0), "Submission not found");
        require(scoreBps <= 10000, "Score bps must be <= 10000");

        Submission storage sub = submissions[bountyId][submissionId];
        sub.isAccepted = isAccepted;
        sub.scoreBps = scoreBps;

        if (isAccepted) {
            b.winningSubmissionId = submissionId;
            emit WinningSubmissionSelected(bountyId, submissionId);
            b.state = BountyState.CHALLENGE;
            b.challengeDeadline = block.timestamp + b.challengeDuration;
        } else {
            b.state = BountyState.REJECTED;
        }

        emit ReviewRecorded(bountyId, submissionId, isAccepted, scoreBps, b.challengeDeadline);
    }

    /**
     * @notice Allows challenge within challenge window (FR-046)
     */
    function challengeDecision(bytes32 bountyId, bytes32 reasonHash) external whenNotPaused {
        Bounty storage b = bounties[bountyId];
        require(b.state == BountyState.CHALLENGE, "Bounty not in CHALLENGE window");
        require(block.timestamp <= b.challengeDeadline, "Challenge window expired");
        require(b.challenger == address(0), "Decision already challenged");
        require(reasonHash != bytes32(0), "Reason hash cannot be empty");

        b.challenger = msg.sender;
        b.challengeReasonHash = reasonHash;

        emit DecisionChallenged(bountyId, msg.sender, reasonHash);
    }

    /**
     * @notice Settles bounty and executes idempotent payout of simulated credits (FR-050, FR-052)
     */
    function settleBounty(bytes32 bountyId) external onlyReviewer(bountyId) whenNotPaused {
        Bounty storage b = bounties[bountyId];
        require(b.state == BountyState.CHALLENGE, "Bounty not in challenge state");
        require(block.timestamp > b.challengeDeadline, "Challenge deadline not yet elapsed");
        require(b.winningSubmissionId != bytes32(0), "No winning submission assigned");

        b.state = BountyState.SETTLED;
        Submission memory sub = submissions[bountyId][b.winningSubmissionId];

        emit BountySettled(bountyId, b.winningSubmissionId, sub.contributor, b.rewardCredits);

        bytes32 settlementId = keccak256(abi.encodePacked(bountyId, sub.contributor, block.chainid));
        settlementContract.settleBounty(settlementId, bountyId, sub.contributor, b.rewardCredits);
    }

    /**
     * @notice Cancels or voids bounty (FR-051)
     */
    function cancelBounty(bytes32 bountyId, bytes32 reason) external onlyReviewer(bountyId) whenNotPaused {
        Bounty storage b = bounties[bountyId];
        require(b.state != BountyState.SETTLED, "Bounty already settled");
        b.state = BountyState.CANCELLED;
        emit BountyCancelled(bountyId, reason);
    }

    function getSubmissions(bytes32 bountyId) external view returns (bytes32[] memory) {
        return bountySubmissionList[bountyId];
    }
}
