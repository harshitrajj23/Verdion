// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CaseRegistry
 * @dev Manages legal case versioning, scope registrations, and evidence digests on-chain.
 * PRD Section 12.2: "Register case/version identifiers and evidence digests"
 */
contract CaseRegistry {
    address public owner;

    struct CaseRecord {
        string caseId;
        uint256 scopeVersion;
        bytes32 evidenceRootDigest;
        string jurisdiction;
        uint256 registeredAt;
    }

    mapping(string => CaseRecord) public cases;
    mapping(string => bytes32[]) public caseEvidenceDigests;

    event CaseRegistered(string indexed caseId, uint256 scopeVersion, string jurisdiction, bytes32 evidenceRootDigest);
    event EvidenceDigestAdded(string indexed caseId, bytes32 digest);

    modifier onlyOwner() {
        require(msg.sender == owner, "CaseRegistry: caller is not the owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function registerCase(
        string calldata caseId,
        uint256 scopeVersion,
        string calldata jurisdiction,
        bytes32 evidenceRootDigest
    ) external {
        cases[caseId] = CaseRecord({
            caseId: caseId,
            scopeVersion: scopeVersion,
            evidenceRootDigest: evidenceRootDigest,
            jurisdiction: jurisdiction,
            registeredAt: block.timestamp
        });

        emit CaseRegistered(caseId, scopeVersion, jurisdiction, evidenceRootDigest);
    }

    function recordEvidenceDigest(string calldata caseId, bytes32 digest) external {
        caseEvidenceDigests[caseId].push(digest);
        emit EvidenceDigestAdded(caseId, digest);
    }

    function getEvidenceDigests(string calldata caseId) external view returns (bytes32[] memory) {
        return caseEvidenceDigests[caseId];
    }
}
