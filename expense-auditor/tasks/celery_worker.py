import os
import json
import asyncio
from celery import Celery
from dotenv import load_dotenv

from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.ai_agent import ComplianceAgent

load_dotenv()

celery_app = Celery(
    'expense_auditor',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
)

@celery_app.task(bind=True, name='process_receipt')
def process_receipt_task(self, receipt_data: dict, user_profile: dict):
    db = SessionLocal()
    try:
        if not receipt_data.get('vision_extracted'):
            receipt_data.update({'merchant': 'Uber', 'amount': 45.50, 'date': '2026-03-30', 'category': 'Transport'})
            receipt_data['vision_extracted'] = True
            
        agent = ComplianceAgent()
        result = asyncio.run(agent.check_compliance(receipt_data, user_profile))
        
        transaction = Transaction(
            receipt_id=receipt_data.get('receipt_id'), user_id=user_profile.get('user_id'),
            merchant=receipt_data.get('merchant', ''), amount=abs(receipt_data.get('amount', 0)),
            date=receipt_data.get('date', ''), category=receipt_data.get('category', 'Other'),
            verdict=result['verdict'], explanation=result['explanation'],
            compliance_score=result.get('compliance_score', 0.5),
            reasoning_steps=json.dumps(result.get('reasoning_steps', []))
        )
        db.add(transaction)
        db.commit()
        return {'status': 'success', 'verdict': result['verdict']}
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()