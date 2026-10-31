from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CaseCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Case title")
    question: str = Field(..., min_length=5, description="Legal/compliance question to investigate")
    jurisdiction: str = Field(..., min_length=2, max_length=64, description="Applicable legal jurisdiction, e.g. 'EU', 'California'")
    assessment_date: str = Field(..., description="Assessment date (YYYY-MM-DD) for statutory applicability")
    facts: Dict[str, Any] = Field(..., description="Structured facts: data_categories, processing_purpose, affected_users, retention, etc.")
    document_references: Optional[List[str]] = Field(default=None, description="Optional document links or identifiers")
    provenance: Optional[str] = Field(default="OPERATIONAL", description="Data origin: 'OPERATIONAL', 'DEMO', 'TEST', or 'UNKNOWN'")


class CaseUpdateRequest(BaseModel):
    title: Optional[str] = None
    question: Optional[str] = None
    jurisdiction: Optional[str] = None
    facts: Optional[Dict[str, Any]] = None


class CaseResponse(BaseModel):
    id: str
    title: str
    question: str
    jurisdiction: str
    assessment_date: str
    facts: Dict[str, Any]
    scope_version: int
    status: str
    provenance: Optional[str] = "OPERATIONAL"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
