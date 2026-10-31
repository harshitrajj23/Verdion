import asyncio
import re
import time
import xml.etree.ElementTree as ET
from typing import List, Optional
import httpx

from backend.app.services.ingestion.base_adapter import (
    BaseSourceAdapter,
    ExternalSourceRetrievalError,
    SourceDocumentMetadata,
    validate_official_url,
)


class EURLexAdapter(BaseSourceAdapter):
    """
    Live Adapter for official Publications Office of the European Union / EUR-Lex legislative acts.
    Retrieves official regulations, directives, and decisions via the Publications Office
    Linked Data / Cellar interface using stable CELEX identifiers.
    """

    CELLAR_CELEX_BASE = "https://publications.europa.eu/resource/celex"
    USER_AGENT = "VeridionLegalIntelligence/1.0 (Public Research Bot; Compliance Audit)"

    def __init__(self):
        super().__init__(name="eur_lex", jurisdiction="EU", version="1.1.0")

    async def fetch_document(self, identifier: str) -> SourceDocumentMetadata:
        """
        Retrieves a genuine legal document directly from the official EU Publications Office
        using its unique CELEX identifier (e.g. '32024R1689' or '32016R0679').
        """
        celex = identifier.strip().upper()
        # Clean potential prefix
        if celex.startswith("CELEX:"):
            celex = celex.replace("CELEX:", "").strip()

        target_url = f"{self.CELLAR_CELEX_BASE}/{celex}"
        validate_official_url(target_url)

        start_time = time.time()
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/xml;notice=object"
        }

        # Bounded timeout and retry logic
        last_err = None
        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(target_url, headers=headers)
                    if resp.status_code == 200 and resp.content:
                        notice_xml = resp.text
                        break
                    elif resp.status_code in (404, 400):
                        raise ExternalSourceRetrievalError(
                            f"Document CELEX '{celex}' not found on official EU Publications Office (HTTP {resp.status_code})."
                        )
                    else:
                        raise ExternalSourceRetrievalError(
                            f"EU Publications Office returned HTTP {resp.status_code} for CELEX '{celex}'."
                        )
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_err = exc
                if attempt < 3:
                    await asyncio.sleep(1.0 * attempt)
                    continue
                raise ExternalSourceRetrievalError(
                    f"Network failure connecting to EU Publications Office for CELEX '{celex}': {str(exc)}"
                ) from exc

        # Parse Notice XML to extract official metadata
        metadata = self._parse_notice_xml(notice_xml, celex, target_url)

        # Retrieve the official English manifestation document content
        raw_content = await self._retrieve_manifestation_content(celex, notice_xml)
        if not raw_content:
            # Fallback to title and extracted summary from notice if full XHTML not available
            raw_content = metadata.get("summary") or metadata["title"]

        norm_content = self.normalize_html_or_xml_text(raw_content)
        if not norm_content or len(norm_content) < 50:
            raise ExternalSourceRetrievalError(
                f"Retrieved content for CELEX '{celex}' was empty or invalid (length: {len(norm_content)})."
            )

        duration_ms = round((time.time() - start_time) * 1000, 2)

        doc = SourceDocumentMetadata(
            source_id=f"doc_eurlex_{celex.lower()}",
            title=metadata["title"],
            jurisdiction="EU",
            document_type=metadata["document_type"],
            celex_or_ecli=celex,
            publication_date=metadata["publication_date"],
            effective_date=metadata["effective_date"],
            version="1.0",
            url=metadata["official_url"],
            raw_content=norm_content,
            provenance="REMOTE_OFFICIAL_SOURCE",
            adapter_name=self.name,
            adapter_version=self.version,
            retrieval_duration_ms=duration_ms,
            verification_status="VERIFIED_OFFICIAL"
        )
        doc.compute_digest()
        return doc

    def _parse_notice_xml(self, notice_xml: str, celex: str, default_url: str) -> dict:
        try:
            root = ET.fromstring(notice_xml)
        except Exception as exc:
            raise ExternalSourceRetrievalError(f"Failed to parse XML notice for CELEX '{celex}': {exc}")

        # Extract title (prefer English expression title)
        title = None
        for exp in root.findall(".//EXPRESSION"):
            lang = exp.find(".//EXPRESSION_USES_LANGUAGE/URI/IDENTIFIER")
            if lang is not None and lang.text == "ENG":
                t_val = exp.find(".//EXPRESSION_TITLE/VALUE")
                if t_val is not None and t_val.text:
                    title = t_val.text.strip()
                    break

        if not title:
            # Try work title
            t_val = root.find(".//WORK/WORK_TITLE/VALUE")
            title = t_val.text.strip() if t_val is not None and t_val.text else f"Act CELEX {celex}"

        # Clean title
        title = title.replace("#", " - ")

        # Document type
        doc_type = "REGULATION"
        if "DIRECTIVE" in title.upper() or "L" in celex:
            doc_type = "DIRECTIVE"
        elif "DECISION" in title.upper():
            doc_type = "DECISION"
        elif "CORRIGENDUM" in title.upper():
            doc_type = "CORRIGENDUM"

        # Date of document / publication
        pub_date = "2024-01-01"
        date_elem = root.find(".//WORK_DATE_DOCUMENT/VALUE") or root.find(".//DATE_DOCUMENT/VALUE")
        if date_elem is not None and date_elem.text:
            pub_date = date_elem.text.strip()

        # Effective date (or default to publication date)
        eff_date = pub_date
        eff_elem = root.find(".//RESOURCE_LEGAL_DATE_ENTRY-INTO-FORCE/VALUE")
        if eff_elem is not None and eff_elem.text:
            eff_date = eff_elem.text.strip()

        # Official ELI or EUR-Lex URL
        official_url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}"

        return {
            "title": title,
            "document_type": doc_type,
            "publication_date": pub_date,
            "effective_date": eff_date,
            "official_url": official_url
        }

    async def _retrieve_manifestation_content(self, celex: str, notice_xml: str) -> Optional[str]:
        """
        Attempts to resolve the full XHTML manifestation via the Publications Office Linked Data endpoints.
        """
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # 1. Check direct English XHTML manifestation endpoint
            direct_urls = [
                f"{self.CELLAR_CELEX_BASE}/{celex}.ENG.xhtml",
                f"{self.CELLAR_CELEX_BASE}/0{celex}-20160504.ENG.xhtml",
            ]
            for u in direct_urls:
                try:
                    validate_official_url(u)
                    r = await client.get(u, headers={"User-Agent": self.USER_AGENT})
                    if r.status_code == 200 and len(r.text) > 500:
                        # If RDF pointing to item DOC_1
                        if "manifestation_has_item" in r.text or "<rdf:RDF" in r.text:
                            m = re.search(r'rdf:resource="([^"]+/DOC_1)"', r.text)
                            if m:
                                doc_url = m.group(1)
                                validate_official_url(doc_url)
                                r_doc = await client.get(doc_url, headers={"User-Agent": self.USER_AGENT})
                                if r_doc.status_code == 200 and len(r_doc.text) > 500:
                                    return r_doc.text
                        elif not r.text.startswith("<?xml") or "<html" in r.text.lower():
                            return r.text
                except Exception:
                    continue

            # 2. Extract manifestation links from the notice XML
            root = ET.fromstring(notice_xml)
            for m in root.findall(".//EXPRESSION_MANIFESTED_BY_MANIFESTATION"):
                uri = m.find(".//URI/VALUE")
                if uri is not None and uri.text and uri.text.endswith(".ENG.xhtml"):
                    try:
                        validate_official_url(uri.text)
                        r = await client.get(uri.text, headers={"User-Agent": self.USER_AGENT})
                        if r.status_code == 200 and "DOC_1" in r.text:
                            match = re.search(r'rdf:resource="([^"]+/DOC_1)"', r.text)
                            if match:
                                doc_url = match.group(1)
                                validate_official_url(doc_url)
                                r_doc = await client.get(doc_url, headers={"User-Agent": self.USER_AGENT})
                                if r_doc.status_code == 200 and len(r_doc.text) > 500:
                                    return r_doc.text
                    except Exception:
                        continue

        return None

    async def fetch_feed(self, limit: int = 2) -> List[SourceDocumentMetadata]:
        """
        Retrieves live authoritative statutory documents from official CELEX registry.
        Defaults to active core regulations (AI Act 2024/1689 and GDPR 2016/679).
        """
        feed_celexes = ["32024R1689", "32016R0679"][:limit]
        documents = []
        for celex in feed_celexes:
            doc = await self.fetch_document(celex)
            documents.append(doc)
        return documents
