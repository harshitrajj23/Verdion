from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    id: str
    case_id: str
    event_type: str
    actor: str
    payload_digest: str
    payload: Dict[str, Any]
    tx_hash: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
