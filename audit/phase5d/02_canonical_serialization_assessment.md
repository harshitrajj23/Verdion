# Phase 5D — Canonical Serialization Protocol Assessment (VCP-1)

## Executive Summary

Audit systems fail when independent reviewers running on different platforms, runtimes, or languages generate divergent hashes for semantically identical regulatory records. Phase 5C introduced canonicalization, but presented custom application rules (Unicode NFC normalization, 6-decimal float rounding) as if they were base RFC 8785 behavior, while omitting critical IEEE 754 edge cases (`NaN`, `Infinity`, `-0.0`).

Phase 5D formalizes the **VERIDION Canonical Serialization Protocol Profile v1 (VCP-1)** in [`backend/app/core/canonical.py`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/core/canonical.py).

---

## 1. RFC 8785 vs. VCP-1 Application Profile

| Technical Dimension | Base RFC 8785 (JCS) Standard | VCP-1 Profile Enforcement | Rationale for Protocol Choice |
| :--- | :--- | :--- | :--- |
| **Number Formatting** | ECMAScript IEEE 754 float-to-string (e.g. `0.3333333333333333`). | **Rounded to 6 decimal places** (`0.333333`). | Prevents platform-specific floating point epsilon divergence between x86, ARM64, and WebAssembly Python runtimes. |
| **Non-Finite Floats** | MUST terminate with an error (§3.2.2.3). | **Rejects `NaN`, `Infinity`, `-Infinity` with `ValueError`.** | Standards-compliant: Standard JSON grammar (RFC 8259) prohibits non-finite values. |
| **Negative Zero** | `-0` MUST be serialized as `0` (§3.2.2.3). | **Normalizes `-0.0` to `0.0`.** | Eliminates sign discrepancy in zero values. |
| **Unicode Strings** | Requires UTF-8, preserves code point sequences. | **Enforces Unicode NFC normalization.** | Guarantees that composed characters (e.g., `é` as `\u00e9`) and decomposed characters (`e\u0301`) yield identical SHA-256 byte digests. |
| **Dictionary Keys** | Lexicographical sort by UTF-16 code units (§3.2.3). | **Sorted by Unicode NFC string order.** | Compatible with standard UTF-8 lexicographical sorting across Python, Node.js, and Solidity. |
| **Array Semantics** | Preserves array element order exactly (§3.2.1). | **Preserves list/tuple order; sorts sets deterministically.** | Legal citations have explicit sequential dependency; sets are unordered collections converted to sorted lists. |
| **Null Values** | Explicit `null` preserved; undefined keys omitted (§3.2.2). | **`None` serialized as explicit JSON `null`.** | Consistent schema representation across database and offline export packages. |
| **Separators** | Compact: no whitespace outside strings (`","`, `":"`). | **Strict `(",", ":")` separators without newlines.** | Prevents whitespace-induced hash divergences. |

---

## 2. Formal VCP-1 Protocol Specification

### Rule 1: Type Acceptance Matrix
Only the following data types are permitted in a canonical decision record payload:
1. `NoneType` $\rightarrow$ JSON `null`
2. `bool` $\rightarrow$ JSON `true` / `false`
3. `int` $\rightarrow$ Arbitrary-precision decimal integer string
4. `float` $\rightarrow$ Finite 64-bit IEEE 754 float, rounded to 6 decimal places
5. `str` $\rightarrow$ UTF-8 string normalized to NFC
6. `datetime` $\rightarrow$ ISO 8601 UTC string with trailing `Z`
7. `list` / `tuple` $\rightarrow$ JSON array, element order preserved
8. `set` $\rightarrow$ JSON array, elements sanitized and sorted deterministically
9. `dict` $\rightarrow$ JSON object, keys sorted lexicographically

*Rejection Rule:* Any instance of `type(obj)` not in the matrix (including lambdas, sockets, custom class instances without serializable dict representation, `NaN`, and `Infinity`) raises `TypeError` or `ValueError` immediately.

### Rule 2: Float Representation & Deterministic Rounding
$$\text{CleanFloat}(x) = \begin{cases} 
\text{error}(\text{"Non-finite"}) & \text{if } x \in \{\text{NaN}, \infty, -\infty\} \\
0.0 & \text{if } x = -0.0 \text{ or } \text{round}(x, 6) = 0.0 \\
\text{round}(x, 6) & \text{otherwise}
\end{cases}$$

### Rule 3: Digest Algorithm
$$\text{RecordDigest} = \text{SHA256}\Big(\text{UTF8}(\text{serialize\_canonical\_json}(\text{Payload} \setminus \{\text{record\_digest}\}))\Big)$$

---

## 3. Protocol Test Vectors & Verification Evidence

The following protocol test vectors are executed in [`backend/tests/test_phase5d_adversarial.py`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/tests/test_phase5d_adversarial.py):

### Vector A: NFC Normalization
- Input: `{"title": "Regulacio\u0301n"}` (NFD decomposed)
- Output String: `{"title":"Regulación"}` (NFC composed: `\u00f3`)
- SHA-256 Digest: `0x24a0d95015b61e29cf90dd3a411e7492c7d9796013a77d5440751939d35f4df2`
- **Result:** **PASS**

### Vector B: Negative Zero and Float Precision
- Input: `{"negative_zero": -0.0, "pi": 3.141592653589793, "small": 0.0000001}`
- Output String: `{"negative_zero":0.0,"pi":3.141593,"small":0.0}`
- **Result:** **PASS**

### Vector C: Set Deterministic Sorting
- Input A: `{"items": {"charlie", "bravo", "alpha"}}`
- Input B: `{"items": {"alpha", "charlie", "bravo"}}`
- Output String: `{"items":["alpha","bravo","charlie"]}`
- Digest A == Digest B: **True**
- **Result:** **PASS**

### Vector D: Non-Finite Rejection
- Input: `{"score": float("nan")}` $\rightarrow$ Raises `ValueError("Non-finite float value 'nan' is prohibited")`
- Input: `{"score": float("inf")}` $\rightarrow$ Raises `ValueError("Non-finite float value 'inf' is prohibited")`
- **Result:** **PASS**
