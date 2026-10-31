import hashlib
import json
import math
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Union


CANONICAL_SCHEMA_VERSION = "veridion_decision_record_v1.0.0"
PROTOCOL_PROFILE_NAME = "VERIDION_CANONICAL_PROFILE_V1"


def normalize_unicode(text: str) -> str:
    """
    Applies Unicode NFC normalization to guarantee identical code point representation.
    NFC (Normalization Form C) combines characters into canonical composite form.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize("NFC", text)


def format_canonical_timestamp(ts: Union[datetime, str, None]) -> Optional[str]:
    """Formats timestamps deterministically in ISO 8601 UTC with explicit 'Z' suffix."""
    if ts is None:
        return None
    if isinstance(ts, str):
        # Normalize existing ISO string to UTC
        cleaned = ts.replace("+00:00", "Z")
        if not cleaned.endswith("Z") and "+" not in cleaned and "-" not in cleaned[10:]:
            cleaned += "Z"
        return cleaned
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        utc_ts = ts.astimezone(timezone.utc)
        return utc_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    raise TypeError(f"Invalid timestamp type: {type(ts).__name__}")


def sanitize_canonical_data(obj: Any) -> Any:
    """
    Recursively prepares data structures for VERIDION Canonical Serialization Profile (VCP-1):
    1. Rejects non-finite floating point numbers (NaN, Infinity, -Infinity) per RFC 8785 §3.2.2.3.
    2. Normalizes negative zero (-0.0) to 0.0 per RFC 8785 §3.2.2.3.
    3. Normalizes floats deterministically to 6 decimal places (VCP-1 application profile choice).
    4. Normalizes all strings to Unicode Normalization Form C (NFC).
    5. Formats datetimes strictly to UTC ISO 8601 with trailing 'Z'.
    6. Sorts dictionary keys lexicographically by Unicode NFC byte order.
    7. Converts sets to deterministically sorted lists.
    8. Preserves explicit None as JSON null.
    9. Rejects arbitrary unsupported types (functions, objects, sockets) with TypeError.
    """
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError(
                f"Non-finite float value '{obj}' is prohibited in canonical serialization (RFC 8785 §3.2.2.3)."
            )
        # Normalize negative zero (-0.0) to 0.0
        if obj == 0.0:
            return 0.0
        # VCP-1 application profile rule: 6 decimal places rounding
        rounded = round(obj, 6)
        return 0.0 if rounded == 0.0 else rounded
    if isinstance(obj, str):
        return normalize_unicode(obj)
    if isinstance(obj, datetime):
        return format_canonical_timestamp(obj)
    if isinstance(obj, set):
        # Convert sets deterministically by sanitizing and sorting items
        sanitized_items = [sanitize_canonical_data(x) for x in obj]
        return sorted(sanitized_items, key=lambda x: serialize_canonical_json(x))
    if isinstance(obj, (list, tuple)):
        return [sanitize_canonical_data(item) for item in obj]
    if isinstance(obj, dict):
        # Sort keys lexicographically by NFC string
        sorted_dict = {}
        for k in sorted(obj.keys(), key=lambda x: normalize_unicode(str(x))):
            norm_k = normalize_unicode(str(k))
            sorted_dict[norm_k] = sanitize_canonical_data(obj[k])
        return sorted_dict

    # Check for Pydantic BaseModel or dict-like objects
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        return sanitize_canonical_data(obj.dict())
    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        return sanitize_canonical_data(obj.model_dump())

    raise TypeError(
        f"Unsupported data type '{type(obj).__name__}' for canonical serialization. "
        f"Only JSON primitives, dicts, lists, datetimes, and sets are permitted."
    )


def serialize_canonical_json(data: Any) -> str:
    """
    Produces deterministic canonical JSON string under VCP-1:
    - NFC normalized
    - Sorted keys
    - No unnecessary whitespace (separators: (',', ':'))
    - UTF-8 characters preserved (ensure_ascii=False)
    """
    sanitized = sanitize_canonical_data(data)
    return json.dumps(sanitized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_canonical_sha256(data: Any) -> str:
    """
    Computes deterministic SHA-256 hex digest prefixed with 0x.
    """
    canonical_str = serialize_canonical_json(data)
    digest_bytes = hashlib.sha256(canonical_str.encode("utf-8")).digest()
    return "0x" + digest_bytes.hex()

