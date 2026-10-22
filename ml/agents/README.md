# Verdion Agent Swarm - Stage 2B

## Isolation Fence & Sentence-Index Rules (FR-012, FR-006)

1. **Isolation Fence Scaffolding**:
   - Isolation fence markers (`[DATA_ONLY_START]`, `[DATA_ONLY_END]`, and `<untrusted_evidence_passage>` tags) are passive data boundaries used strictly to defang prompt injection attempts.
   - Fence markers are **never** part of an extracted sentence.

2. **Canonical Verification**:
   - The verifier compares the code-computed `supporting_quote` against the canonical passage text in `ml/corpus/passages.json`, not against the fenced representation presented in the prompt.
   - If an extracted sentence contains any fence marker, the verifier sets `evidence_status = "UNSUPPORTED"` with reason code `QUOTE_HAS_FENCE_MARKER`.
   - The verifier never strips markers to forcibly accept an invalid quote.

3. **Sentence-Index Citation**:
   - Every claim must specify a `supporting_passage_id` (which must be in `evidence_refs`) and an integer `supporting_sentence_index`.
   - The model selects the integer index from the numbered sentence list presented in the prompt; it writes no quote text.
   - `supporting_quote` is computed by code directly from the canonical passage sentences.

## Verifier Reason Codes

When a claim is evaluated by `verify_claim_quote`, `evidence_status` is set to `SUPPORTED` only if all verification checks pass. Otherwise, `evidence_status` is set to `UNSUPPORTED` with a note containing one of the following reason codes:

- `NOT_IN_EVIDENCE_REFS`: The specified `supporting_passage_id` is missing or not listed in `evidence_refs`.
- `PASSAGE_NOT_FOUND`: Cited passage ID does not exist in `ml/corpus/passages.json`.
- `INDEX_OUT_OF_RANGE`: The `supporting_sentence_index` is out of bounds for the passage sentences.
- `QUOTE_EMPTY`: Extracted sentence is empty or contains only whitespace.
- `QUOTE_HAS_FENCE_MARKER`: Sentence contains prompt isolation fence scaffolding tokens.
- `QUOTE_NOT_VERBATIM`: Extracted sentence is not a verbatim substring of the canonical passage.
- `SENTENCE_TOO_LONG`: The extracted sentence exceeds the hard 60-word limit.

> **Note on Verifier Boundary**: `SUPPORTED` confirms that the cited sentence exists verbatim in the named passage within the word limit. It does not establish that the sentence legally supports the claim. That check is a human review step (PRD §8.4, §17.4).

