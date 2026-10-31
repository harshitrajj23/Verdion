import abc
import hashlib
import ipaddress
import re
import socket
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field


class ExternalSourceRetrievalError(Exception):
    """Raised when an official external legal source retrieval fails."""
    pass


class SSRFSecurityViolation(Exception):
    """Raised when an outbound URL violates SSRF security policy."""
    pass


ALLOWED_OFFICIAL_HOSTS = {
    "publications.europa.eu",
    "curia.europa.eu",
    "www.edpb.europa.eu",
    "edpb.europa.eu",
    "eur-lex.europa.eu"
}


def validate_official_url(url: str) -> None:
    """
    Validates that a URL points strictly to an authorized official legal publisher.
    Guarantees SSRF protection by verifying host allowlist and blocking loopback/private IPs.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFSecurityViolation(f"Unsupported URL scheme: {parsed.scheme}")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise SSRFSecurityViolation("Missing hostname in URL")

    # Check against allowlisted official domains
    is_allowed = any(hostname == h or hostname.endswith("." + h) for h in ALLOWED_OFFICIAL_HOSTS)
    if not is_allowed:
        raise SSRFSecurityViolation(f"Host '{hostname}' is not in the allowlist of official legal publishers: {ALLOWED_OFFICIAL_HOSTS}")

    # Check IP addresses (block loopback, private ranges, metadata services)
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise SSRFSecurityViolation(f"Access to private/local IP address '{hostname}' is strictly forbidden.")
    except ValueError:
        # Hostname is a domain name, which is expected
        pass


class SourceDocumentMetadata(BaseModel):
    source_id: str
    title: str
    jurisdiction: str = "EU"
    document_type: str  # REGULATION, DIRECTIVE, CJEU_JUDGMENT, EDPB_GUIDELINE, CORRIGENDUM
    celex_or_ecli: Optional[str] = None
    publication_date: str
    effective_date: str
    version: str = "1.0"
    url: str
    raw_content: str
    digest: str = ""
    provenance: str = "REMOTE_OFFICIAL_SOURCE"
    adapter_name: str = "base"
    adapter_version: str = "1.0.0"
    retrieval_timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    retrieval_duration_ms: float = 0.0
    verification_status: str = "VERIFIED_OFFICIAL"

    def compute_digest(self) -> str:
        norm = " ".join(self.raw_content.split())
        self.digest = "0x" + hashlib.sha256(norm.encode("utf-8")).hexdigest()
        return self.digest


class BaseSourceAdapter(abc.ABC):
    """
    Abstract adapter for official legal source feeds (EUR-Lex, CJEU InfoCuria, EDPB).
    Guarantees deterministic normalization, stable identity, passage segmentation,
    SHA-256 cryptographic digests, and strict SSRF allowlisting.
    """

    def __init__(self, name: str, jurisdiction: str = "EU", version: str = "1.0.0"):
        self.name = name
        self.jurisdiction = jurisdiction
        self.version = version

    @abc.abstractmethod
    async def fetch_feed(self, limit: int = 5) -> List[SourceDocumentMetadata]:
        """Fetches metadata and authorized content from the source change feed."""
        pass

    @abc.abstractmethod
    async def fetch_document(self, identifier: str) -> SourceDocumentMetadata:
        """Fetches a specific document by its authoritative official identifier (CELEX, ECLI, etc.)."""
        pass

    def normalize_html_or_xml_text(self, text: str) -> str:
        """
        Converts raw HTML/XML to structured, legible legal text
        while faithfully preserving article headers, paragraphs, and numbering.
        """
        if not text:
            return ""

        # Remove scripts and styles
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Convert block breaks and headers to double newlines
        text = re.sub(r"<(p|div|h[1-6]|tr|li|table|blockquote)[^>]*>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        # Remove remaining tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Decode basic entities
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
        # Normalize carriage returns and consecutive spaces
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return text.strip()

    def normalize_text(self, text: str) -> str:
        """Strips noise while preserving meaningful statutory structure."""
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def segment_passages(self, doc: SourceDocumentMetadata) -> List[Dict[str, Any]]:
        """
        Segments a legal document into identifiable, digestable passages.
        Uses conservative clause segmentation to preserve proviso conditions.
        """
        passages: List[Dict[str, Any]] = []
        raw = self.normalize_text(doc.raw_content)

        # Split by major statutory blocks (Articles, Paragraphs, Recitals, Judgment Points)
        pattern = r"\n+(?=(?:Article\s+\d+|Paragraph\s+\d+|Recital\s+\d+|Judgment\s+Point\s+\d+|Point\s+\d+|§\s*\d+))"
        blocks = re.split(pattern, raw, flags=re.IGNORECASE)

        if len(blocks) <= 1:
            # Fallback split on paragraphs if no statutory headers
            blocks = re.split(r"\n\s*\n+", raw)

        for idx, block in enumerate(blocks):
            clean_block = block.strip()
            if not clean_block or len(clean_block) < 30:
                continue

            # Extract passage reference (e.g., Article 6(1)(f) or Paragraph 32)
            header_match = re.match(
                r"^((?:Article|Paragraph|Recital|Judgment\s+Point|Point|§)\s+[^:\n]+)",
                clean_block,
                flags=re.IGNORECASE
            )
            ref_name = header_match.group(1).strip() if header_match else f"{doc.source_id}_sec_{idx+1}"

            # Compute SHA-256 digest over normalized block content
            norm_content = " ".join(clean_block.split())
            digest = "0x" + hashlib.sha256(norm_content.encode("utf-8")).hexdigest()
            passage_id = f"pass_{doc.source_id}_{idx+1}"

            passages.append({
                "id": passage_id,
                "document_id": doc.source_id,
                "passage_reference": ref_name,
                "content_reference": f"{doc.title} - {ref_name}",
                "text": clean_block,
                "digest": digest,
                "source_version": doc.version,
                "provenance": doc.provenance
            })

        return passages
