import json
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from app.db.session import get_db
from app.models.transaction import Transaction
from app.schemas.receipt import ReceiptUploadResponse, ReceiptStatusResponse, RecheckResponse
from tasks.celery_worker import process_receipt_task, celery_app 
from app.ai_agent import ComplianceAgent

router = APIRouter()
global_receipt_counter = 1

@router.post("/upload", response_model=ReceiptUploadResponse)
async def upload_receipt(receipt_file: UploadFile = File(...), user_id: str = Form(...), user_profile: str = Form(default="{}")):
    global global_receipt_counter
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
        tmp_file.write(await receipt_file.read())
        tmp_path = tmp_file.name
    
    receipt_data = {'receipt_id': f"RCP-{global_receipt_counter}", 'file_path': tmp_path, 'vision_extracted': False}
    global_receipt_counter += 1
    
    profile_dict = json.loads(user_profile)
    profile_dict['user_id'] = user_id
    
    task = process_receipt_task.delay(receipt_data=receipt_data, user_profile=profile_dict)
    return {"status": "queued", "task_id": str(task.id), "message": "Receipt queued"}

@router.get("/{task_id}/status", response_model=ReceiptStatusResponse)
async def get_receipt_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    if result.ready():
        return {"task_id": task_id, "status": "completed", "result": result.result if isinstance(result.result, dict) else {}}
    return {"task_id": task_id, "status": "processing", "progress": 0}