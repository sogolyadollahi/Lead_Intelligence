from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from core.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    # Raw / cleaned fields
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    company = Column(String, nullable=True)
    website = Column(String, nullable=True)
    # Enrichment
    industry = Column(String, nullable=True)
    company_description = Column(Text, nullable=True)
    business_type = Column(String, nullable=True)  # B2B / B2C / Unknown
    ai_confidence = Column(Float, default=0.0)
    # Scoring
    lead_score = Column(Integer, default=0)
    lead_quality_label = Column(String, default="Low")
    # Meta
    email_valid = Column(Integer, default=0)  # 0/1 boolean
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    batch_id = Column(String, nullable=True)  # group by upload
