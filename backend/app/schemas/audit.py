from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    id: str
    case_id: str
    sequence_number: Optional[int] = 1
    event_type: str
    actor: str
    payload_digest: str
    payload: Dict[str, Any]
    previous_event_digest: Optional[str] = None
    event_digest: Optional[str] = None
    tx_hash: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
