import uuid
import asyncio
import pandas as pd
from sqlalchemy.orm import Session

from models.lead import Lead
from models.schemas import ProcessingStats
from utils.cleaner import clean_dataframe, clean_lead_dict, validate_email
from services.enricher import enrich_lead
from services.scorer import score_lead


async def _process_single_lead(row: dict, batch_id: str, db: Session) -> Lead:
    cleaned = clean_lead_dict(row)

    if not cleaned["name"]:
        return None

    enrichment = await enrich_lead(cleaned["company"], cleaned["website"])
    email_valid = validate_email(cleaned["email"])
    score, quality = score_lead(
        email=cleaned["email"],
        company=cleaned["company"],
        website=cleaned["website"],
        ai_confidence=enrichment.ai_confidence,
        email_valid=email_valid,
    )

    lead = Lead(
        name=cleaned["name"],
        email=cleaned["email"],
        company=cleaned["company"],
        website=cleaned["website"],
        industry=enrichment.industry,
        company_description=enrichment.company_description,
        business_type=enrichment.business_type,
        ai_confidence=enrichment.ai_confidence,
        lead_score=score,
        lead_quality_label=quality,
        email_valid=int(email_valid),
        batch_id=batch_id,
    )
    db.add(lead)
    return lead


async def process_leads_from_df(df: pd.DataFrame, db: Session) -> tuple[list[Lead], ProcessingStats]:
    batch_id = str(uuid.uuid4())[:8]
    total_received = len(df)

    df, duplicates_removed, invalid_removed = clean_dataframe(df)

    tasks = [
        _process_single_lead(row.to_dict(), batch_id, db)
        for _, row in df.iterrows()
    ]
    results = await asyncio.gather(*tasks)
    leads = [r for r in results if r is not None]

    db.commit()
    for lead in leads:
        db.refresh(lead)

    stats = ProcessingStats(
        total_received=total_received,
        duplicates_removed=duplicates_removed,
        invalid_removed=invalid_removed,
        successfully_processed=len(leads),
        batch_id=batch_id,
    )
    return leads, stats


async def process_leads_from_list(raw_leads: list[dict], db: Session) -> tuple[list[Lead], ProcessingStats]:
    df = pd.DataFrame(raw_leads)
    return await process_leads_from_df(df, db)
