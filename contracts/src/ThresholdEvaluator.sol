// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ThresholdEvaluator (PRD-SC-008)
 * @notice Multi-evaluator threshold cryptographic signature verification for market resolutions.
 * @dev Implements EIP-712 structured hashing, ascending signer deduplication, replay defense,
 *      and cross-language Python/Solidity parity.
 */

contract ThresholdEvaluator {
    // --- EIP-712 Type Hashes ---
    bytes32 public constant EIP712_DOMAIN_TYPEHASH = keccak256(
        "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
    );

    bytes32 public constant RESOLUTION_TYPEHASH = keccak256(
        "MarketResolution(bytes32 marketId,uint8 outcome,uint256 nonce,bytes32 evidenceDigest)"
    );

    bytes32 public immutable DOMAIN_SEPARATOR;
    uint256 public immutable INITIAL_CHAIN_ID;

    // --- State Variables ---
    address public owner;
    uint256 public threshold;
    address[] public evaluators;
    mapping(address => bool) public isEvaluator;
    mapping(bytes32 => mapping(uint256 => bool)) public usedNonces;
    mapping(bytes32 => bool) public isMarketResolved;
    mapping(bytes32 => uint8) public resolvedOutcomes;

    // --- Events ---
    event EvaluatorAdded(address indexed evaluator);
    event EvaluatorRemoved(address indexed evaluator);
    event ThresholdUpdated(uint256 newThreshold);
    event MarketResolvedByThreshold(
        bytes32 indexed marketId,
        uint8 outcome,
        uint256 signatureCount,
        bytes32 evidenceDigest
    );

    // --- Modifiers ---
    modifier onlyOwner() {
        require(msg.sender == owner, "ThresholdEvaluator: caller is not owner");
        _;
    }

    // --- Constructor ---
    constructor(address[] memory _evaluators, uint256 _threshold) {
        require(_evaluators.length >= 2, "ThresholdEvaluator: minimum 2 evaluators required");
        require(_threshold >= 2 && _threshold <= _evaluators.length, "ThresholdEvaluator: invalid threshold");

        owner = msg.sender;
        INITIAL_CHAIN_ID = block.chainid;
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                EIP712_DOMAIN_TYPEHASH,
                keccak256(bytes("VERIDION_EVALUATOR")),
                keccak256(bytes("1")),
                block.chainid,
                address(this)
            )
        );

        for (uint256 i = 0; i < _evaluators.length; i++) {
            address ev = _evaluators[i];
            require(ev != address(0), "ThresholdEvaluator: zero address rejected");
            require(!isEvaluator[ev], "ThresholdEvaluator: duplicate evaluator rejected");

            isEvaluator[ev] = true;
            evaluators.push(ev);
            emit EvaluatorAdded(ev);
        }

        threshold = _threshold;
        emit ThresholdUpdated(_threshold);
    }

    // --- Hash Computations ---

    function getResolutionDigest(
        bytes32 marketId,
        uint8 outcome,
        uint256 nonce,
        bytes32 evidenceDigest
    ) public view returns (bytes32) {
        bytes32 structHash = keccak256(
            abi.encode(
                RESOLUTION_TYPEHASH,
                marketId,
                outcome,
                nonce,
                evidenceDigest
            )
        );

        return keccak256(
            abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash)
        );
    }

    // --- Resolution Verification ---

    function resolveMarketWithThreshold(
        bytes32 marketId,
        uint8 outcome,
        uint256 nonce,
        bytes32 evidenceDigest,
        bytes[] calldata signatures
    ) external {
        require(!isMarketResolved[marketId], "ThresholdEvaluator: market already resolved");
        require(!usedNonces[marketId][nonce], "ThresholdEvaluator: nonce already used");
        require(outcome <= 1, "ThresholdEvaluator: outcome must be 0 or 1");
        require(signatures.length >= threshold, "ThresholdEvaluator: threshold not reached");

        bytes32 digest = getResolutionDigest(marketId, outcome, nonce, evidenceDigest);

        address lastSigner = address(0);

        for (uint256 i = 0; i < signatures.length; i++) {
            address signer = recoverSigner(digest, signatures[i]);
            require(isEvaluator[signer], "ThresholdEvaluator: unauthorized signer");
            require(signer > lastSigner, "ThresholdEvaluator: signatures must be strictly ascending (no duplicates)");
            lastSigner = signer;
        }

        usedNonces[marketId][nonce] = true;
        isMarketResolved[marketId] = true;
        resolvedOutcomes[marketId] = outcome;

        emit MarketResolvedByThreshold(marketId, outcome, signatures.length, evidenceDigest);
    }

    function recoverSigner(bytes32 digest, bytes memory sig) public pure returns (address) {
        require(sig.length == 65, "ThresholdEvaluator: invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }

        if (v < 27) {
            v += 27;
        }
        require(v == 27 || v == 28, "ThresholdEvaluator: invalid v value");

        address signer = ecrecover(digest, v, r, s);
        require(signer != address(0), "ThresholdEvaluator: ecrecover failed");
        return signer;
    }

    // --- Governance ---

    function updateThreshold(uint256 newThreshold) external onlyOwner {
        require(newThreshold >= 2 && newThreshold <= evaluators.length, "Invalid threshold");
        threshold = newThreshold;
        emit ThresholdUpdated(newThreshold);
    }

    function addEvaluator(address newEvaluator) external onlyOwner {
        require(newEvaluator != address(0) && !isEvaluator[newEvaluator], "Invalid evaluator");
        isEvaluator[newEvaluator] = true;
        evaluators.push(newEvaluator);
        emit EvaluatorAdded(newEvaluator);
    }

    function getEvaluators() external view returns (address[] memory) {
        return evaluators;
    }
}

