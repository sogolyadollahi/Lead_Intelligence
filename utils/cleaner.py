import re
import pandas as pd
from typing import Optional


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def validate_email(email: Optional[str]) -> bool:
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def normalize_email(email: Optional[str]) -> Optional[str]:
    if not email or not isinstance(email, str):
        return None
    cleaned = email.strip().lower()
    return cleaned if validate_email(cleaned) else None


def normalize_string(value: Optional[str]) -> Optional[str]:
    if not value or not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def normalize_website(url: Optional[str]) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    url = url.strip().lower()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url if url else None


def clean_lead_dict(raw: dict) -> dict:
    return {
        "name": normalize_string(raw.get("name")),
        "email": normalize_email(raw.get("email")),
        "company": normalize_string(raw.get("company")),
        "website": normalize_website(raw.get("website")),
    }


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Returns (cleaned_df, duplicates_removed, invalid_removed)"""
    original_count = len(df)

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Ensure required columns exist
    for col in ["name", "email", "company", "website"]:
        if col not in df.columns:
            df[col] = None

    # Drop rows with no name (minimum requirement)
    df["name"] = df["name"].apply(normalize_string)
    invalid_mask = df["name"].isna()
    invalid_removed = int(invalid_mask.sum())
    df = df[~invalid_mask].copy()

    # Remove duplicates by email (if present) or name+company
    before_dedup = len(df)
    df["_email_norm"] = df["email"].apply(normalize_email)
    df["_dedup_key"] = df.apply(
        lambda r: r["_email_norm"] if r["_email_norm"] else f"{r['name']}|{r.get('company', '')}",
        axis=1,
    )
    df = df.drop_duplicates(subset=["_dedup_key"], keep="first")
    df = df.drop(columns=["_dedup_key", "_email_norm"])
    duplicates_removed = before_dedup - len(df)

    # Normalize all fields
    df["email"] = df["email"].apply(normalize_email)
    df["company"] = df["company"].apply(normalize_string)
    df["website"] = df["website"].apply(normalize_website)

    return df, duplicates_removed, invalid_removed
