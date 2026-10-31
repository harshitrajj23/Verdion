// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MultiSigPauseController (PRD-SEC-015)
 * @notice Multi-signature governance contract for emergency circuit breakers.
 * @dev Enforces M-of-N threshold signatures (default: 3-of-5) for pausing and unpausing
 *      VERIDION contracts (e.g. PredictionMarket, EvidenceBounty).
 */

interface IPausableTarget {
    function setPaused(bool _paused) external;
}

contract MultiSigPauseController {
    // --- Events ---
    event SignerAdded(address indexed signer);
    event SignerRemoved(address indexed signer);
    event ThresholdChanged(uint256 newThreshold);
    event ProposalCreated(uint256 indexed proposalId, address indexed target, bool targetPaused, bytes32 reasonHash);
    event ProposalConfirmed(uint256 indexed proposalId, address indexed signer);
    event ProposalExecuted(uint256 indexed proposalId, address indexed executor);
    event ProposalRevoked(uint256 indexed proposalId, address indexed signer);

    // --- Structs ---
    enum ProposalType { PAUSE, UNPAUSE, ROTATE_SIGNER, UPDATE_THRESHOLD }

    struct Proposal {
        uint256 id;
        ProposalType pType;
        address targetContract;
        bool targetPaused;
        bytes32 reasonHash;
        address oldSigner;
        address newSigner;
        uint256 newThreshold;
        uint256 confirmations;
        bool executed;
        uint256 createdAt;
    }

    // --- State Variables ---
    address[] public signers;
    mapping(address => bool) public isSigner;
    uint256 public threshold;
    uint256 public proposalCount;

    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) public hasConfirmed;

    // --- Modifiers ---
    modifier onlySigner() {
        require(isSigner[msg.sender], "MultiSig: caller is not a designated signer");
        _;
    }

    modifier proposalExists(uint256 proposalId) {
        require(proposalId > 0 && proposalId <= proposalCount, "MultiSig: proposal does not exist");
        _;
    }

    modifier notExecuted(uint256 proposalId) {
        require(!proposals[proposalId].executed, "MultiSig: proposal already executed");
        _;
    }

    // --- Constructor ---
    constructor(address[] memory _initialSigners, uint256 _threshold) {
        require(_initialSigners.length >= 3, "MultiSig: minimum 3 signers required");
        require(_threshold >= 2 && _threshold <= _initialSigners.length, "MultiSig: invalid threshold");

        for (uint256 i = 0; i < _initialSigners.length; i++) {
            address s = _initialSigners[i];
            require(s != address(0), "MultiSig: zero address rejected");
            require(!isSigner[s], "MultiSig: duplicate signer rejected");

            isSigner[s] = true;
            signers.push(s);
            emit SignerAdded(s);
        }

        threshold = _threshold;
        emit ThresholdChanged(_threshold);
    }

    // --- Proposal Creation ---

    function proposeEmergencyPause(address _targetContract, bytes32 _reasonHash)
        external
        onlySigner
        returns (uint256)
    {
        require(_targetContract != address(0), "MultiSig: invalid target contract");
        return _createProposal(ProposalType.PAUSE, _targetContract, true, _reasonHash, address(0), address(0), 0);
    }

    function proposeUnpause(address _targetContract, bytes32 _reasonHash)
        external
        onlySigner
        returns (uint256)
    {
        require(_targetContract != address(0), "MultiSig: invalid target contract");
        return _createProposal(ProposalType.UNPAUSE, _targetContract, false, _reasonHash, address(0), address(0), 0);
    }

    function proposeSignerRotation(address _oldSigner, address _newSigner)
        external
        onlySigner
        returns (uint256)
    {
        require(isSigner[_oldSigner], "MultiSig: old signer does not exist");
        require(_newSigner != address(0) && !isSigner[_newSigner], "MultiSig: invalid new signer");
        return _createProposal(ProposalType.ROTATE_SIGNER, address(0), false, bytes32(0), _oldSigner, _newSigner, 0);
    }

    function proposeThresholdUpdate(uint256 _newThreshold)
        external
        onlySigner
        returns (uint256)
    {
        require(_newThreshold >= 2 && _newThreshold <= signers.length, "MultiSig: invalid threshold range");
        return _createProposal(ProposalType.UPDATE_THRESHOLD, address(0), false, bytes32(0), address(0), address(0), _newThreshold);
    }

    function _createProposal(
        ProposalType _pType,
        address _targetContract,
        bool _targetPaused,
        bytes32 _reasonHash,
        address _oldSigner,
        address _newSigner,
        uint256 _newThreshold
    ) internal returns (uint256) {
        proposalCount++;
        uint256 pid = proposalCount;

        proposals[pid] = Proposal({
            id: pid,
            pType: _pType,
            targetContract: _targetContract,
            targetPaused: _targetPaused,
            reasonHash: _reasonHash,
            oldSigner: _oldSigner,
            newSigner: _newSigner,
            newThreshold: _newThreshold,
            confirmations: 1,
            executed: false,
            createdAt: block.timestamp
        });

        hasConfirmed[pid][msg.sender] = true;

        emit ProposalCreated(pid, _targetContract, _targetPaused, _reasonHash);
        emit ProposalConfirmed(pid, msg.sender);

        return pid;
    }

    // --- Confirmation & Execution ---

    function confirmProposal(uint256 proposalId)
        external
        onlySigner
        proposalExists(proposalId)
        notExecuted(proposalId)
    {
        require(!hasConfirmed[proposalId][msg.sender], "MultiSig: signer already confirmed");

        hasConfirmed[proposalId][msg.sender] = true;
        proposals[proposalId].confirmations++;

        emit ProposalConfirmed(proposalId, msg.sender);
    }

    function executeProposal(uint256 proposalId)
        external
        onlySigner
        proposalExists(proposalId)
        notExecuted(proposalId)
    {
        Proposal storage p = proposals[proposalId];
        require(p.confirmations >= threshold, "MultiSig: threshold not reached");

        p.executed = true;

        if (p.pType == ProposalType.PAUSE || p.pType == ProposalType.UNPAUSE) {
            IPausableTarget(p.targetContract).setPaused(p.targetPaused);
        } else if (p.pType == ProposalType.ROTATE_SIGNER) {
            isSigner[p.oldSigner] = false;
            isSigner[p.newSigner] = true;
            for (uint256 i = 0; i < signers.length; i++) {
                if (signers[i] == p.oldSigner) {
                    signers[i] = p.newSigner;
                    break;
                }
            }
            emit SignerRemoved(p.oldSigner);
            emit SignerAdded(p.newSigner);
        } else if (p.pType == ProposalType.UPDATE_THRESHOLD) {
            threshold = p.newThreshold;
            emit ThresholdChanged(p.newThreshold);
        }

        emit ProposalExecuted(proposalId, msg.sender);
    }

    function getSigners() external view returns (address[] memory) {
        return signers;
    }
}

