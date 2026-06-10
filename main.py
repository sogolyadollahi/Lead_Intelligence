from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.database import init_db
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Lead Intelligence & Enrichment System",
    description="Production-style backend for AI-powered lead enrichment and scoring.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["Leads"])


@app.get("/")
def root():
    return {
        "service": "Lead Intelligence & Enrichment System",
        "version": "1.0.0",
        "docs": "/docs",
    }
