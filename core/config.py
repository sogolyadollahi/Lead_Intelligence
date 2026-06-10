import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR}/data/leads.db"
EXPORTS_DIR = BASE_DIR / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_MOCK_AI = not bool(OPENAI_API_KEY)

SCORE_WEIGHTS = {
    "has_email": 30,
    "has_company": 20,
    "has_website": 20,
    "ai_confidence": 30,
}

QUALITY_THRESHOLDS = {
    "High": 70,
    "Medium": 40,
    "Low": 0,
}
