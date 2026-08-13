from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class DiagnosisRequest(BaseModel):
    asset_id: str = Field(min_length=1, max_length=80)
    symptom: str = Field(min_length=5, max_length=2000)
    observations: list[str] = Field(default_factory=list, max_length=20)


class Evidence(BaseModel):
    id: str
    source_type: Literal["manual", "work_order"]
    title: str
    excerpt: str
    locator: str
    score: float = Field(ge=0, le=1)


class RootCause(BaseModel):
    cause: str
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(min_length=1)
    rationale: str


class RepairStep(BaseModel):
    order: int = Field(ge=1)
    instruction: str
    safety_note: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class Part(BaseModel):
    sku: str
    name: str
    quantity: int = Field(ge=1)
    reason: str


class DiagnosisResult(BaseModel):
    case_id: str
    status: Literal["complete", "insufficient_evidence"]
    summary: str
    root_causes: list[RootCause] = Field(max_length=3)
    next_questions: list[str]
    suggested_parts: list[Part]
    repair_plan: list[RepairStep]
    evidence: list[Evidence]
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def citations_exist(self):
        ids = {e.id for e in self.evidence}
        cited = [i for c in self.root_causes for i in c.evidence_ids]
        cited += [i for s in self.repair_plan for i in s.evidence_ids]
        missing = set(cited) - ids
        if missing:
            raise ValueError(f"unknown evidence ids: {sorted(missing)}")
        if self.status == "complete" and not self.root_causes:
            raise ValueError("complete diagnosis requires root causes")
        return self

class DiagnosisDraft(BaseModel):
    status: Literal["complete", "insufficient_evidence"]
    summary: str
    root_causes: list[RootCause] = Field(max_length=3)
    next_questions: list[str]
    suggested_parts: list[Part]
    repair_plan: list[RepairStep]
    limitations: list[str] = Field(default_factory=list)


class TraceEvent(BaseModel):
    step: str
    status: Literal["complete", "fallback", "warning"]
    detail: str
    duration_ms: int


class DiagnosisEnvelope(BaseModel):
    diagnosis: DiagnosisResult
    trace: list[TraceEvent]
    latency_ms: int
    estimated_cost_usd: float
    mode: Literal["openai", "demo_fallback"]


class ApprovalRequest(BaseModel):
    approved: bool
    technician: str = Field(min_length=2, max_length=100)
    notes: str = Field(default="", max_length=1000)

class ReportRequest(BaseModel):
    diagnosis: DiagnosisResult
    approval: ApprovalRequest


class ServiceReport(BaseModel):
    report_id: str
    case_id: str
    generated_at: str
    approval: ApprovalRequest
    diagnosis_summary: str
    probable_cause: str
    evidence_references: list[str]
    repair_actions: list[str]
    parts: list[Part]

    @classmethod
    def from_diagnosis(cls, diagnosis: DiagnosisResult, approval: ApprovalRequest):
        return cls(
            report_id=f"SR-{diagnosis.case_id.split('-')[-1]}", case_id=diagnosis.case_id,
            generated_at=datetime.now(timezone.utc).isoformat(), approval=approval,
            diagnosis_summary=diagnosis.summary,
            probable_cause=diagnosis.root_causes[0].cause if diagnosis.root_causes else "Undetermined",
            evidence_references=sorted({i for c in diagnosis.root_causes for i in c.evidence_ids}),
            repair_actions=[s.instruction for s in diagnosis.repair_plan], parts=diagnosis.suggested_parts,
        )
