import { keccak256, encodePacked, stringToBytes } from 'viem';

/**
 * Deterministically sorts object keys recursively for canonical JSON representation.
 */
export function canonicalizeJson(obj: unknown): string {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalizeJson).join(',') + ']';
  }
  const sortedKeys = Object.keys(obj as Record<string, unknown>).sort();
  const entries = sortedKeys.map(
    (key) => `${JSON.stringify(key)}:${canonicalizeJson((obj as Record<string, unknown>)[key])}`
  );
  return '{' + entries.join(',') + '}';
}

/**
 * Computes canonical evidence digest (FR-026) using Keccak256 of canonical JSON string.
 */
export function computeEvidenceDigest(evidencePayload: {
  document_id: string;
  passage_reference: string;
  content: string;
  source_metadata: {
    title: string;
    authority: string;
    jurisdiction: string;
    effective_date: string;
  };
}): `0x${string}` {
  const canonicalString = canonicalizeJson(evidencePayload);
  return keccak256(stringToBytes(canonicalString));
}

/**
 * Computes commitment hash matching Solidity PredictionMarket:
 * keccak256(abi.encodePacked(uint256 chainId, bytes32 marketId, address agentId, uint256 probabilityBps, bytes32 evidenceDigest, bytes32 nonce))
 * 
 * Note: probability is encoded as Basis Points (0 - 10000) for exact integer precision on EVM.
 */
export function computeCommitmentHash(
  chainId: bigint,
  marketId: `0x${string}`,
  agentAddress: `0x${string}`,
  probabilityBps: bigint,
  evidenceDigest: `0x${string}`,
  nonce: `0x${string}`
): `0x${string}` {
  if (probabilityBps < 0n || probabilityBps > 10000n) {
    throw new Error('Probability basis points must be between 0 and 10000');
  }
  return keccak256(
    encodePacked(
      ['uint256', 'bytes32', 'address', 'uint256', 'bytes32', 'bytes32'],
      [chainId, marketId, agentAddress, probabilityBps, evidenceDigest, nonce]
    )
  );
}

/**
 * Helper to generate a random 32-byte secret nonce
 */
export function generateNonce(): `0x${string}` {
  const randomBytes = new Uint8Array(32);
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    crypto.getRandomValues(randomBytes);
  } else {
    // Node environment fallback
    const nodeCrypto = require('crypto');
    return `0x${nodeCrypto.randomBytes(32).toString('hex')}` as `0x${string}`;
  }
  const hex = Array.from(randomBytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
  return `0x${hex}` as `0x${string}`;
}
