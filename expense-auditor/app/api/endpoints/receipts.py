import json
import tempfile
import uuid
from fastapi import APIRouter, UploadFile, File, Form
from celery.result import AsyncResult

from app.schemas.receipt import ReceiptUploadResponse, ReceiptStatusResponse
from tasks.celery_worker import process_receipt_task
from tasks.celery_app import celery_app

router = APIRouter()

@router.post("/upload", response_model=ReceiptUploadResponse)
async def upload_receipt(
    receipt_file: UploadFile = File(...),
    user_id: str = Form(...),
    user_profile: str = Form(default="{}")
):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
        tmp_file.write(await receipt_file.read())
        tmp_path = tmp_file.name

    receipt_data = {
        'receipt_id': f"RCP-{uuid.uuid4().hex[:8].upper()}",
        'file_path': tmp_path,
        'vision_extracted': False
    }

    profile_dict = json.loads(user_profile)
    profile_dict['user_id'] = user_id

    task = process_receipt_task.delay(
        receipt_data=receipt_data,
        user_profile=profile_dict
    )

    return ReceiptUploadResponse(
        status="queued",
        task_id=str(task.id),
        message="Receipt processing started"
    )


@router.get("/{task_id}/status", response_model=ReceiptStatusResponse)
async def get_receipt_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)

    if result.state == "PENDING":
        return {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "verdict": None,
            "explanation": None,
            "compliance_score": None,
            "reasoning_steps": None,
            "result": None
        }

    if result.failed():
        return {
            "task_id": task_id,
            "status": "failed",
            "progress": 0,
            "verdict": "FLAGGED",
            "explanation": str(result.result),
            "compliance_score": None,
            "reasoning_steps": None,
            "result": None
        }

    if result.ready():
        raw = result.result if isinstance(result.result, dict) else {}
        return {
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "verdict": raw.get("verdict"),
            "explanation": raw.get("explanation"),
            "compliance_score": raw.get("compliance_score"),
            "reasoning_steps": raw.get("reasoning_steps", []),
            "result": raw,
        }

    return {
        "task_id": task_id,
        "status": "processing",
        "progress": 50
    }