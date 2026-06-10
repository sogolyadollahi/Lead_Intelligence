import csv
import json
import os
from datetime import datetime
from pathlib import Path
from core.config import EXPORTS_DIR


def export_leads_to_csv(leads: list, filename: str | None = None) -> str:
    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"leads_export_{ts}.csv"

    filepath = EXPORTS_DIR / filename

    fieldnames = [
        "id", "name", "email", "company", "website",
        "industry", "business_type", "company_description",
        "ai_confidence", "lead_score", "lead_quality_label",
        "email_valid", "batch_id", "created_at",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow({field: getattr(lead, field, "") for field in fieldnames})

    return str(filepath)


def export_leads_to_json(leads: list) -> list[dict]:
    result = []
    for lead in leads:
        result.append({
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "website": lead.website,
            "enrichment": {
                "industry": lead.industry,
                "business_type": lead.business_type,
                "company_description": lead.company_description,
                "ai_confidence": lead.ai_confidence,
            },
            "scoring": {
                "lead_score": lead.lead_score,
                "lead_quality_label": lead.lead_quality_label,
            },
            "meta": {
                "email_valid": bool(lead.email_valid),
                "batch_id": lead.batch_id,
                "created_at": str(lead.created_at),
            },
        })
    return result
