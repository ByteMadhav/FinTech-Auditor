from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    
    merchant = Column(String, nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    date = Column(String, nullable=True)
    category = Column(String, nullable=True)
    
    verdict = Column(String, nullable=True)
    explanation = Column(Text, nullable=True)
    compliance_score = Column(Float, nullable=True)
    reasoning_steps = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())