// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/**
 * @title CaseRegistry
 * @notice On-chain registry for Verdion legal cases, versioned scopes, and evidence digests (FR-001..FR-004, FR-026, §12.2).
 * Stores only minimal identifiers and cryptographic digests to prevent private data leakage (FR-054, §17.3).
 */
contract CaseRegistry {
    enum CaseStatus {
        DRAFT,
        RETRIEVAL,
        ANALYSIS,
        INVESTIGATION,
        REVIEW,
        COMPLETED,
        FAILED
    }

    struct CaseRecord {
        bytes32 caseId;
        uint256 currentVersion;
        address owner;
        CaseStatus status;
        bytes32 scopeHash;
        uint256 createdAt;
        uint256 updatedAt;
    }

    struct CaseVersion {
        uint256 version;
        bytes32 scopeHash;
        bytes32 sourceCorpusDigest;
        uint256 timestamp;
    }

    address public admin;
    bool public paused;

    // caseId => CaseRecord
    mapping(bytes32 => CaseRecord) public cases;
    // caseId => version => CaseVersion
    mapping(bytes32 => mapping(uint256 => CaseVersion)) public caseVersions;
    // caseId => evidenceDigest => exists
    mapping(bytes32 => mapping(bytes32 => bool)) public evidenceDigests;

    event CaseCreated(bytes32 indexed caseId, address indexed owner, uint256 version, bytes32 scopeHash, uint256 timestamp);
    event CaseVersionUpdated(bytes32 indexed caseId, uint256 newVersion, bytes32 newScopeHash, bytes32 corpusDigest, uint256 timestamp);
    event CaseStatusChanged(bytes32 indexed caseId, CaseStatus oldStatus, CaseStatus newStatus, uint256 timestamp);
    event EvidenceDigestAnchored(bytes32 indexed caseId, bytes32 indexed evidenceDigest, uint256 timestamp);
    event Paused(address account);
    event Unpaused(address account);

    modifier onlyAdmin() {
        require(msg.sender == admin, "CaseRegistry: caller is not admin");
        _;
    }

    modifier onlyCaseOwner(bytes32 caseId) {
        require(cases[caseId].owner == msg.sender || msg.sender == admin, "CaseRegistry: unauthorized");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "CaseRegistry: paused");
        _;
    }

    constructor() {
        admin = msg.sender;
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
     * @notice Registers a new case with an initial version and scope hash
     */
    function createCase(
        bytes32 caseId,
        bytes32 scopeHash,
        bytes32 sourceCorpusDigest
    ) external whenNotPaused {
        require(caseId != bytes32(0), "CaseRegistry: invalid caseId");
        require(cases[caseId].caseId == bytes32(0), "CaseRegistry: case already exists");
        require(scopeHash != bytes32(0), "CaseRegistry: invalid scopeHash");

        cases[caseId] = CaseRecord({
            caseId: caseId,
            currentVersion: 1,
            owner: msg.sender,
            status: CaseStatus.DRAFT,
            scopeHash: scopeHash,
            createdAt: block.timestamp,
            updatedAt: block.timestamp
        });

        caseVersions[caseId][1] = CaseVersion({
            version: 1,
            scopeHash: scopeHash,
            sourceCorpusDigest: sourceCorpusDigest,
            timestamp: block.timestamp
        });

        emit CaseCreated(caseId, msg.sender, 1, scopeHash, block.timestamp);
    }

    /**
     * @notice Records an updated scope or facts as a new version (FR-003)
     */
    function updateCaseScope(
        bytes32 caseId,
        bytes32 newScopeHash,
        bytes32 newCorpusDigest
    ) external onlyCaseOwner(caseId) whenNotPaused {
        CaseRecord storage c = cases[caseId];
        require(c.caseId != bytes32(0), "CaseRegistry: case does not exist");
        require(newScopeHash != bytes32(0), "CaseRegistry: invalid newScopeHash");

        c.currentVersion += 1;
        c.scopeHash = newScopeHash;
        c.updatedAt = block.timestamp;

        caseVersions[caseId][c.currentVersion] = CaseVersion({
            version: c.currentVersion,
            scopeHash: newScopeHash,
            sourceCorpusDigest: newCorpusDigest,
            timestamp: block.timestamp
        });

        emit CaseVersionUpdated(caseId, c.currentVersion, newScopeHash, newCorpusDigest, block.timestamp);
    }

    /**
     * @notice Updates the lifecycle status of a case (FR-004)
     */
    function updateStatus(bytes32 caseId, CaseStatus newStatus) external onlyCaseOwner(caseId) whenNotPaused {
        CaseRecord storage c = cases[caseId];
        require(c.caseId != bytes32(0), "CaseRegistry: case does not exist");
        CaseStatus oldStatus = c.status;
        c.status = newStatus;
        c.updatedAt = block.timestamp;

        emit CaseStatusChanged(caseId, oldStatus, newStatus, block.timestamp);
    }

    /**
     * @notice Anchors an accepted evidence digest for tamper-evident provenance (FR-026, FR-055)
     */
    function anchorEvidenceDigest(bytes32 caseId, bytes32 evidenceDigest) external onlyCaseOwner(caseId) whenNotPaused {
        require(cases[caseId].caseId != bytes32(0), "CaseRegistry: case does not exist");
        require(evidenceDigest != bytes32(0), "CaseRegistry: invalid evidenceDigest");
        require(!evidenceDigests[caseId][evidenceDigest], "CaseRegistry: digest already anchored");

        evidenceDigests[caseId][evidenceDigest] = true;
        emit EvidenceDigestAnchored(caseId, evidenceDigest, block.timestamp);
    }
}
