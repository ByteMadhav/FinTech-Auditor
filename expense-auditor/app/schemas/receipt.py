from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ReceiptUploadResponse(BaseModel):
    status: str
    task_id: str
    message: str


class ReceiptStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[int] = 0
    verdict: Optional[str] = None
    explanation: Optional[str] = None
    compliance_score: Optional[float] = None
    reasoning_steps: Optional[List[str]] = None
    result: Optional[Dict[str, Any]] = None


class RecheckResponse(BaseModel):
    status: str
    transaction_id: int
    new_verdict: str
    new_score: float