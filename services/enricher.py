import random
import re
from dataclasses import dataclass
from core.config import USE_MOCK_AI, OPENAI_API_KEY


@dataclass
class EnrichmentResult:
    industry: str
    company_description: str
    business_type: str
    ai_confidence: float


# ── Mock enrichment data ──────────────────────────────────────────────────────

INDUSTRY_KEYWORDS = {
    "Technology": ["tech", "software", "app", "digital", "cloud", "ai", "data", "cyber", "dev", "code", "sys", "net", "it"],
    "Finance": ["finance", "bank", "capital", "invest", "fund", "credit", "pay", "money", "wealth", "trading"],
    "Healthcare": ["health", "med", "pharma", "clinic", "care", "hospital", "bio", "life", "wellness", "therapy"],
    "E-commerce": ["shop", "store", "retail", "market", "commerce", "buy", "sell", "goods", "product"],
    "Marketing": ["market", "media", "agency", "creative", "brand", "ads", "pr", "content", "growth"],
    "Real Estate": ["realty", "property", "estate", "homes", "housing", "land", "build", "construct"],
    "Education": ["edu", "learn", "school", "academy", "train", "course", "teach", "tutor"],
    "Logistics": ["logistics", "supply", "ship", "freight", "transport", "delivery", "cargo", "fleet"],
    "Legal": ["law", "legal", "attorney", "counsel", "firm", "justice", "advocate"],
    "Consulting": ["consult", "advisory", "strategy", "solutions", "group", "partners", "associates"],
}

BUSINESS_TYPE_MAP = {
    "Technology": ("B2B", 0.85),
    "Finance": ("B2B", 0.80),
    "Healthcare": ("B2C", 0.75),
    "E-commerce": ("B2C", 0.90),
    "Marketing": ("B2B", 0.82),
    "Real Estate": ("B2C", 0.72),
    "Education": ("B2C", 0.78),
    "Logistics": ("B2B", 0.88),
    "Legal": ("B2B", 0.76),
    "Consulting": ("B2B", 0.84),
}

DESCRIPTIONS = {
    "Technology": "A technology company delivering innovative software solutions to streamline operations and accelerate digital transformation.",
    "Finance": "A financial services firm offering investment, lending, and wealth management solutions to individuals and businesses.",
    "Healthcare": "A healthcare organization focused on improving patient outcomes through modern medical solutions and care delivery.",
    "E-commerce": "An e-commerce company providing consumers with a seamless online shopping experience across multiple product categories.",
    "Marketing": "A marketing and creative agency helping brands grow their presence through data-driven campaigns and compelling content.",
    "Real Estate": "A real estate company specializing in property sales, rentals, and development for residential and commercial clients.",
    "Education": "An education provider delivering engaging learning experiences through modern curricula and skilled instructors.",
    "Logistics": "A logistics company providing end-to-end supply chain, freight, and delivery solutions for businesses of all sizes.",
    "Legal": "A law firm offering comprehensive legal services across corporate, commercial, and regulatory practice areas.",
    "Consulting": "A consulting firm partnering with organizations to solve complex business challenges through strategic insight and expertise.",
}


def _infer_industry_mock(company: str | None, website: str | None) -> str:
    text = " ".join(filter(None, [company, website])).lower()
    # Remove common domain suffixes
    text = re.sub(r"\.(com|io|net|co|org|ai|tech|app)", " ", text)

    scores = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        scores[industry] = sum(1 for kw in keywords if kw in text)

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Consulting"


def _mock_enrichment(company: str | None, website: str | None) -> EnrichmentResult:
    industry = _infer_industry_mock(company, website)
    business_type, base_confidence = BUSINESS_TYPE_MAP.get(industry, ("Unknown", 0.5))
    # Slight randomness to simulate real confidence variance
    confidence = round(min(1.0, base_confidence + random.uniform(-0.05, 0.08)), 2)
    description = DESCRIPTIONS.get(industry, "A company providing specialized services to its target market.")

    if company:
        description = description.replace("A ", f"{company} is a ", 1).replace("An ", f"{company} is an ", 1)

    return EnrichmentResult(
        industry=industry,
        company_description=description,
        business_type=business_type,
        ai_confidence=confidence,
    )


# ── Real OpenAI enrichment ────────────────────────────────────────────────────

async def _openai_enrichment(company: str | None, website: str | None) -> EnrichmentResult:
    try:
        from openai import AsyncOpenAI
        import json

        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        prompt = f"""You are a B2B sales intelligence analyst.

Given the following company info:
- Company Name: {company or 'Unknown'}
- Website: {website or 'Unknown'}

Return ONLY valid JSON with these exact keys:
{{
  "industry": "<single industry label>",
  "company_description": "<2-sentence description>",
  "business_type": "<B2B|B2C|Unknown>",
  "ai_confidence": <float 0.0-1.0 representing your confidence>
}}"""

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        return EnrichmentResult(
            industry=data.get("industry", "Unknown"),
            company_description=data.get("company_description", ""),
            business_type=data.get("business_type", "Unknown"),
            ai_confidence=float(data.get("ai_confidence", 0.5)),
        )
    except Exception as e:
        print(f"[OpenAI Error] {e} — falling back to mock")
        return _mock_enrichment(company, website)


# ── Public interface ──────────────────────────────────────────────────────────

async def enrich_lead(company: str | None, website: str | None) -> EnrichmentResult:
    if USE_MOCK_AI:
        return _mock_enrichment(company, website)
    return await _openai_enrichment(company, website)
