import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from models.lead import Lead
from models.schemas import EnrichedLeadResponse, UploadResponse, LeadInput
from services.pipeline import process_leads_from_df, process_leads_from_list
from utils.exporter import export_leads_to_csv, export_leads_to_json

router = APIRouter()


@router.post("/upload-leads", response_model=UploadResponse)
async def upload_leads(
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Upload a CSV file of leads for processing."""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided. Send a CSV file.")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported for file upload.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse CSV: {e}")

    leads, stats = await process_leads_from_df(df, db)

    return UploadResponse(
        stats=stats,
        leads=[EnrichedLeadResponse.model_validate(l) for l in leads],
    )


@router.post("/submit-leads", response_model=UploadResponse)
async def submit_leads_json(
    leads_input: list[LeadInput],
    db: Session = Depends(get_db),
):
    """Submit leads as a JSON list."""
    if not leads_input:
        raise HTTPException(status_code=400, detail="Empty leads list.")

    raw = [l.model_dump() for l in leads_input]
    leads, stats = await process_leads_from_list(raw, db)

    return UploadResponse(
        stats=stats,
        leads=[EnrichedLeadResponse.model_validate(l) for l in leads],
    )


@router.get("/leads", response_model=list[EnrichedLeadResponse])
def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    quality: Optional[str] = Query(None, description="Filter by quality: Low, Medium, High"),
    batch_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve stored leads with optional filtering."""
    query = db.query(Lead)
    if quality:
        query = query.filter(Lead.lead_quality_label == quality)
    if batch_id:
        query = query.filter(Lead.batch_id == batch_id)
    leads = query.order_by(Lead.lead_score.desc()).offset(skip).limit(limit).all()
    return [EnrichedLeadResponse.model_validate(l) for l in leads]


@router.get("/lead/{lead_id}", response_model=EnrichedLeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a single enriched lead by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found.")
    return EnrichedLeadResponse.model_validate(lead)


@router.get("/export/csv")
def export_csv(
    quality: Optional[str] = None,
    batch_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Export all (or filtered) leads to a CSV file."""
    query = db.query(Lead)
    if quality:
        query = query.filter(Lead.lead_quality_label == quality)
    if batch_id:
        query = query.filter(Lead.batch_id == batch_id)
    leads = query.order_by(Lead.lead_score.desc()).all()

    if not leads:
        raise HTTPException(status_code=404, detail="No leads found matching criteria.")

    filepath = export_leads_to_csv(leads)
    return FileResponse(filepath, media_type="text/csv", filename="leads_export.csv")


@router.get("/export/json")
def export_json(
    quality: Optional[str] = None,
    batch_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Export leads as structured JSON."""
    query = db.query(Lead)
    if quality:
        query = query.filter(Lead.lead_quality_label == quality)
    if batch_id:
        query = query.filter(Lead.batch_id == batch_id)
    leads = query.order_by(Lead.lead_score.desc()).all()

    return JSONResponse(content=export_leads_to_json(leads))


@router.delete("/leads")
def clear_leads(db: Session = Depends(get_db)):
    """Clear all leads (dev/testing only)."""
    count = db.query(Lead).count()
    db.query(Lead).delete()
    db.commit()
    return {"deleted": count}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Return aggregate stats for the dashboard."""
    from sqlalchemy import func
    total = db.query(func.count(Lead.id)).scalar()
    high = db.query(func.count(Lead.id)).filter(Lead.lead_quality_label == "High").scalar()
    medium = db.query(func.count(Lead.id)).filter(Lead.lead_quality_label == "Medium").scalar()
    low = db.query(func.count(Lead.id)).filter(Lead.lead_quality_label == "Low").scalar()
    avg_score = db.query(func.avg(Lead.lead_score)).scalar()

    return {
        "total_leads": total,
        "high_quality": high,
        "medium_quality": medium,
        "low_quality": low,
        "average_score": round(avg_score or 0, 1),
    }
