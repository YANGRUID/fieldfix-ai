from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .diagnosis import DiagnosisService
from .models import DiagnosisEnvelope, DiagnosisRequest, ReportRequest, ServiceReport
from .repository import KnowledgeRepository

ROOT = Path(__file__).resolve().parents[2]
repo = KnowledgeRepository(Path(os.getenv("DATABASE_PATH", ROOT / "data/fieldfix.db")), Path(os.getenv("DATA_DIR", ROOT / "data/sources")))
@asynccontextmanager
async def lifespan(_: FastAPI):
    repo.ingest()
    yield
app = FastAPI(title="FieldFix AI API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","), allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health(): return {"status":"ok", "documents": repo.ingest()}

@app.post("/api/diagnose", response_model=DiagnosisEnvelope)
def diagnose(request: DiagnosisRequest): return DiagnosisService(repo).diagnose(request)

@app.post("/api/reports", response_model=ServiceReport)
def report(request: ReportRequest):
    if not request.approval.approved: raise HTTPException(409, "Human approval is required before report generation")
    return ServiceReport.from_diagnosis(request.diagnosis, request.approval)
