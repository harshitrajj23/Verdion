import json
import logging
import re
from typing import Any, Dict, Optional

SENSITIVE_PATTERNS = [
    re.compile(r"0x[a-fA-F0-9]{64}"),  # Private keys
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"(password|secret|api_key|token)[\"']?\s*[:=]\s*[\"']?([^\"'\s]+)", re.IGNORECASE),
]


def redact_sensitive_text(text: str) -> str:
    """Redacts private keys, secret tokens, and confidential tokens from logs."""
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(r"[REDACTED]", redacted)
    return redacted


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON with trace ID and redaction."""

    def format(self, record: logging.LogRecord) -> str:
        trace_id = getattr(record, "trace_id", "none")
        case_id = getattr(record, "case_id", "none")

        raw_message = record.getMessage()
        safe_message = redact_sensitive_text(raw_message)

        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "trace_id": trace_id,
            "case_id": case_id,
            "message": safe_message,
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
