from pydantic import BaseModel
from typing import Optional, Dict, Any

class ReceiptUploadResponse(BaseModel):
    status: str
    task_id: str
    message: str

class ReceiptStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[int] = 0
    result: Optional[Dict[str, Any]] = None

class RecheckResponse(BaseModel):
    status: str
    transaction_id: int
    new_verdict: str
    new_score: float