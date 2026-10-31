import asyncio
import re
import time
from typing import List, Optional
import httpx

from backend.app.services.ingestion.base_adapter import (
    BaseSourceAdapter,
    ExternalSourceRetrievalError,
    SourceDocumentMetadata,
    validate_official_url,
)


class EDPBAdapter(BaseSourceAdapter):
    """
    Live Adapter for official European Data Protection Board (EDPB) Guidelines and Opinions.
    Retrieves adopted guidelines, recommendations, and public consultations directly from
    the official EDPB website (www.edpb.europa.eu).
    """

    EDPB_BASE = "https://www.edpb.europa.eu"
    GUIDANCE_URL = "https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en"
    USER_AGENT = "VeridionLegalIntelligence/1.0 (Public Research Bot; EDPB Ingestion)"

    DEFAULT_GUIDELINES = {
        "ai_web_scraping": "guidelines-032026-on-web-scraping-in-the-context-of-generative-ai_en",
        "scientific_research": "guidelines-12026-on-processing-of-personal-data-for-scientific-research_en",
        "pseudonymisation": "guidelines-012025-on-pseudonymisation_en",
        "blockchain": "guidelines-022025-on-processing-of-personal-data-through-blockchain_en"
    }

    def __init__(self):
        super().__init__(name="edpb", jurisdiction="EU", version="1.0.0")

    async def fetch_document(self, identifier: str) -> SourceDocumentMetadata:
        """
        Retrieves a genuine EDPB guideline document by its slug or preset key.
        Example identifiers: 'guidelines-032026-on-web-scraping-in-the-context-of-generative-ai_en'
        or preset 'ai_web_scraping'.
        """
        slug = identifier.strip()
        if slug in self.DEFAULT_GUIDELINES:
            slug = self.DEFAULT_GUIDELINES[slug]

        if slug.startswith("http"):
            target_url = slug
        elif slug.startswith("/"):
            target_url = f"{self.EDPB_BASE}{slug}"
        else:
            target_url = f"{self.EDPB_BASE}/public-consultations/{slug}"

        validate_official_url(target_url)

        start_time = time.time()
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml"
        }

        # Bounded HTTP retrieval with retries
        last_err = None
        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    resp = await client.get(target_url, headers=headers)
                    if resp.status_code == 200 and resp.content:
                        html_text = resp.text
                        final_url = str(resp.url)
                        break
                    elif resp.status_code in (404, 400):
                        raise ExternalSourceRetrievalError(
                            f"EDPB guideline '{slug}' not found on official site (HTTP {resp.status_code})."
                        )
                    else:
                        raise ExternalSourceRetrievalError(
                            f"EDPB site returned HTTP {resp.status_code} for guideline '{slug}'."
                        )
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_err = exc
                if attempt < 3:
                    await asyncio.sleep(1.0 * attempt)
                    continue
                raise ExternalSourceRetrievalError(
                    f"Network failure connecting to EDPB for guideline '{slug}': {str(exc)}"
                ) from exc

        # Extract title from HTML
        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, flags=re.DOTALL | re.IGNORECASE)
        if title_match:
            title = self.normalize_html_or_xml_text(title_match.group(1))
        else:
            title = slug.replace("-", " ").title()

        # Extract main article/content body
        content_match = re.search(r"<article[^>]*>(.*?)</article>", html_text, flags=re.DOTALL | re.IGNORECASE)
        if content_match:
            body_html = content_match.group(1)
        else:
            main_match = re.search(r"<main[^>]*>(.*?)</main>", html_text, flags=re.DOTALL | re.IGNORECASE)
            body_html = main_match.group(1) if main_match else html_text

        norm_content = self.normalize_html_or_xml_text(body_html)
        if not norm_content or len(norm_content) < 50:
            raise ExternalSourceRetrievalError(
                f"Retrieved EDPB guideline content for '{slug}' was empty or invalid (length: {len(norm_content)})."
            )

        # Extract date if present
        date_match = re.search(r"\b(\d{1,2}\s+[A-Za-z]+\s+202\d|\d{4}-\d{2}-\d{2})\b", norm_content)
        pub_date = date_match.group(1) if date_match else "2026-01-01"

        duration_ms = round((time.time() - start_time) * 1000, 2)
        source_id = f"doc_edpb_{slug.lower().replace('-', '_')[:32]}"

        doc = SourceDocumentMetadata(
            source_id=source_id,
            title=f"EDPB {title}",
            jurisdiction="EU",
            document_type="EDPB_GUIDELINE",
            celex_or_ecli=slug[:32],
            publication_date=pub_date,
            effective_date=pub_date,
            version="1.0",
            url=final_url,
            raw_content=norm_content,
            provenance="REMOTE_OFFICIAL_SOURCE",
            adapter_name=self.name,
            adapter_version=self.version,
            retrieval_duration_ms=duration_ms,
            verification_status="VERIFIED_OFFICIAL"
        )
        doc.compute_digest()
        return doc

    async def fetch_feed(self, limit: int = 1) -> List[SourceDocumentMetadata]:
        """
        Discovers and retrieves live EDPB guidelines from the official guidance portal.
        """
        validate_official_url(self.GUIDANCE_URL)
        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(self.GUIDANCE_URL, headers=headers)
                if resp.status_code != 200:
                    raise ExternalSourceRetrievalError(
                        f"Failed to fetch EDPB guidance directory (HTTP {resp.status_code})."
                    )
                html_text = resp.text
        except Exception as exc:
            raise ExternalSourceRetrievalError(f"Network failure connecting to EDPB guidance portal: {exc}")

        # Find guideline links
        links = re.findall(r'href="(/public-consultations/[^"]+)"', html_text)
        if not links:
            links = [f"/public-consultations/{self.DEFAULT_GUIDELINES['ai_web_scraping']}"]

        # Deduplicate while preserving order
        unique_links = []
        for link in links:
            if link not in unique_links:
                unique_links.append(link)

        documents = []
        for link in unique_links[:limit]:
            doc = await self.fetch_document(link)
            documents.append(doc)

        return documents
