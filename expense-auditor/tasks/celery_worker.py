import os
import json
import asyncio
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
import pytesseract
from PIL import Image

from tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.ai_agent import ComplianceAgent

load_dotenv()

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_receipt_data(file_path: str) -> dict:
    image = Image.open(file_path)
    ocr_text = pytesseract.image_to_string(image).strip()
    return {
        'raw_text': ocr_text,
        'ocr_text': ocr_text,
        'merchant': '',
        'amount': 0,
        'date': 'Unknown',
        'category': 'Other'
    }

@celery_app.task(bind=True, name='process_receipt')
def process_receipt_task(self, receipt_data: dict, user_profile: dict):
    db = SessionLocal()
    try:
        if not receipt_data.get('vision_extracted'):
            extracted = extract_receipt_data(receipt_data['file_path'])
            receipt_data.update(extracted)
            receipt_data['vision_extracted'] = True

        agent = ComplianceAgent()
        result = asyncio.run(agent.check_compliance(receipt_data, user_profile))

        transaction = Transaction(
            receipt_id=receipt_data.get('receipt_id'),
            user_id=user_profile.get('user_id'),
            merchant=receipt_data.get('merchant', ''),
            amount=abs(receipt_data.get('amount', 0)),
            date=receipt_data.get('date', ''),
            category=receipt_data.get('category', 'Other'),
            verdict=result['verdict'],
            explanation=result['explanation'],
            compliance_score=result.get('compliance_score', 0.5),
            reasoning_steps=json.dumps(result.get('reasoning_steps', []))
        )
        db.add(transaction)
        db.commit()

        return {
            'status': 'success',
            'verdict': result['verdict'],
            'explanation': result.get('explanation', ''),
            'compliance_score': result.get('compliance_score', 0.5),
            'reasoning_steps': result.get('reasoning_steps', [])
        }

    except IntegrityError:
        db.rollback()
        return {
            'status': 'duplicate',
            'verdict': 'FLAGGED',
            'explanation': f"Receipt {receipt_data.get('receipt_id')} already processed.",
            'compliance_score': 0.0,
            'reasoning_steps': []
        }

    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)

    finally:
        db.close()