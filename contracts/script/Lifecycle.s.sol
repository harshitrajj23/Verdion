// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/AgentRegistry.sol";
import "../src/PredictionMarket.sol";
import "../src/ReputationSettlement.sol";

contract LifecycleHelper is Script {
    function computeCommitmentHash(
        uint256 chainId,
        bytes32 marketId,
        address agent,
        uint256 probabilityBps,
        bytes32 evidenceDigest,
        bytes32 nonce
    ) public pure returns (bytes32) {
        return keccak256(
            abi.encodePacked(
                chainId,
                marketId,
                agent,
                probabilityBps,
                evidenceDigest,
                nonce
            )
        );
    }
}
