import re
from typing import Dict, Any

class PromptInjectionIsolation:
    """
    Implements security fence FR-012 / TH-01:
    Treats retrieved statutory/case text as strictly passive untrusted data.
    Sanitizes, escapes system control sequences, and wraps content in explicit isolation fences.
    """
    
    # Adversarial patterns that attempt to hijack instruction hierarchy
    FORBIDDEN_DIRECTIVES = [
        r"ignore (all )?previous instructions",
        r"system prompt:",
        r"you are now an? (unrestricted|admin|evaluator)",
        r"disregard (the )?(above|rules|policy)",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[INST\]",
        r"\[/INST\]",
        r"```(system|admin)"
    ]

    @classmethod
    def sanitize_untrusted_text(cls, text: str) -> str:
        """Sanitizes text by defanging prompt-injection patterns while preserving legal citation content."""
        sanitized = text
        for pattern in cls.FORBIDDEN_DIRECTIVES:
            sanitized = re.sub(pattern, "[DEFANGED_INSTRUCTION]", sanitized, flags=re.IGNORECASE)
        return sanitized

    @classmethod
    def format_isolated_passage(cls, passage: Dict[str, Any]) -> str:
        """
        Wraps untrusted passage in explicit passive data fences so LLM parses it
        strictly as cited reference data, never as system instructions.
        """
        safe_content = cls.sanitize_untrusted_text(passage.get("content", ""))
        passage_id = passage.get("passage_id", "unknown")
        doc_id = passage.get("document_id", "unknown")
        ref = passage.get("passage_reference", "")
        eff_date = passage.get("effective_date", "unknown")

        return (
            f"<untrusted_evidence_passage id=\"{passage_id}\" doc=\"{doc_id}\" ref=\"{ref}\" effective=\"{eff_date}\">\n"
            f"[DATA_ONLY_START]\n"
            f"{safe_content}\n"
            f"[DATA_ONLY_END]\n"
            f"</untrusted_evidence_passage>"
        )
