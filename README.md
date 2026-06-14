# ⚡ Lead Intelligence & Enrichment System

A production-style MVP backend for AI-powered lead qualification, enrichment, and scoring — built for agencies and SaaS teams.

---

## 🏗️ Architecture

```
lead_intelligence/
├── main.py                  # FastAPI entrypoint
├── streamlit_app.py         # Streamlit UI
├── requirements.txt
│
├── api/
│   └── routes.py            # All API endpoints
│
├── core/
│   ├── config.py            # Settings & constants
│   └── database.py          # SQLAlchemy engine & session
│
├── models/
│   ├── lead.py              # SQLAlchemy ORM model
│   └── schemas.py           # Pydantic request/response schemas
│
├── services/
│   ├── pipeline.py          # Main orchestrator
│   ├── enricher.py          # AI enrichment (OpenAI + mock fallback)
│   └── scorer.py            # Lead scoring engine
│
├── utils/
│   ├── cleaner.py           # Data cleaning & normalization
│   └── exporter.py          # CSV/JSON export
│
└── data/
    ├── leads.db             # SQLite database (auto-created)
    └── sample_leads.csv     # Example input
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Set your OpenAI API key

```bash
export OPENAI_API_KEY=sk-...
```

> Without this, the system uses a smart mock enrichment engine with industry keyword matching.

### 3. Run the FastAPI backend

```bash
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 4. Run the Streamlit UI

```bash
streamlit run streamlit_app.py
```

Opens at: http://localhost:8501

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/upload-leads` | Upload CSV file |
| `POST` | `/api/v1/submit-leads` | Submit JSON list of leads |
| `GET` | `/api/v1/leads` | Get all leads (with filters) |
| `GET` | `/api/v1/lead/{id}` | Get single lead by ID |
| `GET` | `/api/v1/export/csv` | Download leads as CSV |
| `GET` | `/api/v1/export/json` | Download leads as JSON |
| `GET` | `/api/v1/stats` | Dashboard statistics |
| `DELETE` | `/api/v1/leads` | Clear all leads |

### Example: Upload CSV via curl

```bash
curl -X POST http://localhost:8000/api/v1/upload-leads \
  -F "file=@data/sample_leads.csv"
```

### Example: Submit JSON

```bash
curl -X POST http://localhost:8000/api/v1/submit-leads \
  -H "Content-Type: application/json" \
  -d '[
    {"name": "Alice Chen", "email": "alice@techflow.io", "company": "TechFlow", "website": "techflow.io"},
    {"name": "Bob Smith", "email": "bob@healthco.com", "company": "HealthCo"}
  ]'
```

---

## 🧠 Enrichment Engine

Each lead is enriched with:
- **Industry** — inferred from company name / domain
- **Business Type** — B2B / B2C / Unknown
- **Company Description** — AI-generated 2-sentence summary
- **AI Confidence Score** — 0.0 to 1.0

When `OPENAI_API_KEY` is set, uses GPT-3.5-turbo. Otherwise, a deterministic keyword-matching mock handles enrichment automatically.

---

## 📊 Scoring System

| Signal | Points |
|--------|--------|
| Valid email | +30 |
| Company name present | +20 |
| Website present | +20 |
| AI confidence (0–1 × 30) | 0–30 |
| **Max score** | **100** |

**Quality Labels:**
- 🟢 **High** — Score ≥ 70
- 🟡 **Medium** — Score ≥ 40
- 🔴 **Low** — Score < 40

---

## 📄 Sample Input

```csv
name,email,company,website
Alice Chen,alice@techflow.io,TechFlow Solutions,techflow.io
Bob Martinez,bob.martinez@gmail.com,HealthFirst Clinic,healthfirst.com
Carol Johnson,,RetailNow,
```

## 📦 Sample Output (JSON)

```json
{
  "id": 1,
  "name": "Alice Chen",
  "email": "alice@techflow.io",
  "company": "TechFlow Solutions",
  "website": "https://techflow.io",
  "enrichment": {
    "industry": "Technology",
    "business_type": "B2B",
    "company_description": "TechFlow Solutions is a technology company delivering innovative software solutions...",
    "ai_confidence": 0.88
  },
  "scoring": {
    "lead_score": 95,
    "lead_quality_label": "High"
  },
  "meta": {
    "email_valid": true,
    "batch_id": "f1a55271",
    "created_at": "2024-01-15T10:23:45"
  }
}
```

---

## 🔧 Extending to SaaS

- Add auth middleware (JWT / API keys) in `core/`
- Add per-user lead isolation with `user_id` FK on `Lead`
- Replace SQLite with PostgreSQL for production
- Add Celery + Redis for async batch processing
- Wrap enricher to support multiple AI providers
- Add webhook support for CRM push (HubSpot, Salesforce)

## Demo Video

[▶ Watch Demo](demo/demo.mp4)