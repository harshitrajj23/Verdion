// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EvidenceBounty
 * @dev On-chain tracking of research bounties, submission digests, challenges, and idempotent settlement.
 * PRD Section 11 & 12.2: Track bounty state, simulated funding, submission digests, review
 */
contract EvidenceBounty {
    address public evaluator;
    address public admin;

    enum BountyState { CREATED, OPEN, REVIEW, CHALLENGE, SETTLED, CANCELLED }

    struct Bounty {
        string bountyId;
        string caseId;
        uint256 rewardAmount;
        uint256 deadline;
        uint256 challengeWindow;
        BountyState state;
        string winningSubmissionId;
        address winnerAddress;
        bool settled;
    }

    struct Submission {
        string submissionId;
        address contributor;
        bytes32 contentDigest;
        uint256 submittedAt;
    }

    // bountyId => Bounty
    mapping(string => Bounty) public bounties;
    // bountyId => submissionId => Submission
    mapping(string => mapping(string => Submission)) public submissions;
    // bountyId => digest => exists (duplicate prevention)
    mapping(string => mapping(bytes32 => bool)) public digestExists;

    event BountyOpened(string indexed bountyId, string caseId, uint256 rewardAmount, uint256 deadline);
    event EvidenceSubmitted(string indexed bountyId, string submissionId, address indexed contributor, bytes32 digest);
    event BountyChallenged(string indexed bountyId, string submissionId, address indexed challenger, string reason);
    event BountySettled(string indexed bountyId, string winningSubmissionId, address indexed winner, uint256 reward);

    modifier onlyEvaluator() {
        require(msg.sender == evaluator || msg.sender == admin, "EvidenceBounty: caller not evaluator");
        _;
    }

    constructor(address _evaluator) {
        admin = msg.sender;
        evaluator = _evaluator;
    }

    function createBounty(
        string calldata bountyId,
        string calldata caseId,
        uint256 rewardAmount,
        uint256 deadline,
        uint256 challengeWindow
    ) external {
        require(bounties[bountyId].deadline == 0, "Bounty already exists");
        require(deadline > block.timestamp, "Deadline must be future");

        bounties[bountyId] = Bounty({
            bountyId: bountyId,
            caseId: caseId,
            rewardAmount: rewardAmount,
            deadline: deadline,
            challengeWindow: challengeWindow,
            state: BountyState.OPEN,
            winningSubmissionId: "",
            winnerAddress: address(0),
            settled: false
        });

        emit BountyOpened(bountyId, caseId, rewardAmount, deadline);
    }

    function submitEvidence(
        string calldata bountyId,
        string calldata submissionId,
        bytes32 contentDigest
    ) external {
        Bounty storage b = bounties[bountyId];
        require(b.state == BountyState.OPEN, "Bounty not open");
        require(block.timestamp <= b.deadline, "Bounty deadline passed");
        require(!digestExists[bountyId][contentDigest], "Duplicate digest submitted");

        submissions[bountyId][submissionId] = Submission({
            submissionId: submissionId,
            contributor: msg.sender,
            contentDigest: contentDigest,
            submittedAt: block.timestamp
        });
        digestExists[bountyId][contentDigest] = true;

        emit EvidenceSubmitted(bountyId, submissionId, msg.sender, contentDigest);
    }

    function challengeBounty(
        string calldata bountyId,
        string calldata submissionId,
        string calldata reason
    ) external {
        Bounty storage b = bounties[bountyId];
        require(b.state == BountyState.OPEN || b.state == BountyState.REVIEW, "Not challengeable");
        b.state = BountyState.CHALLENGE;
        emit BountyChallenged(bountyId, submissionId, msg.sender, reason);
    }

    function settleBounty(
        string calldata bountyId,
        string calldata winningSubmissionId,
        address winnerAddress
    ) external onlyEvaluator {
        Bounty storage b = bounties[bountyId];
        require(!b.settled, "Bounty already settled");
        require(winnerAddress != address(0), "Invalid winner address");

        b.winningSubmissionId = winningSubmissionId;
        b.winnerAddress = winnerAddress;
        b.settled = true;
        b.state = BountyState.SETTLED;

        emit BountySettled(bountyId, winningSubmissionId, winnerAddress, b.rewardAmount);
    }
}
