from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class LeadInput(BaseModel):
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None


class EnrichedLeadResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    company: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    company_description: Optional[str]
    business_type: Optional[str]
    ai_confidence: float
    lead_score: int
    lead_quality_label: str
    email_valid: bool
    created_at: datetime
    batch_id: Optional[str]

    model_config = {"from_attributes": True}


class ProcessingStats(BaseModel):
    total_received: int
    duplicates_removed: int
    invalid_removed: int
    successfully_processed: int
    batch_id: str


class UploadResponse(BaseModel):
    stats: ProcessingStats
    leads: list[EnrichedLeadResponse]
