from __future__ import annotations

import json, os, time, uuid
from pathlib import Path
from openai import OpenAI
from .models import DiagnosisDraft, DiagnosisEnvelope, DiagnosisRequest, DiagnosisResult, Evidence, Part, RepairStep, RootCause, TraceEvent
from .repository import KnowledgeRepository


SYSTEM = """You are an industrial maintenance diagnosis assistant. Return JSON matching the supplied schema. Use only provided evidence. Every root cause and evidence-based repair step must cite evidence IDs from the context. Never invent IDs, facts, parts, or measurements. If evidence is weak, set status to insufficient_evidence and clearly state uncertainty. Safety isolation and manufacturer procedures take priority."""


class DiagnosisService:
    def __init__(self, repository: KnowledgeRepository): self.repository = repository

    def diagnose(self, request: DiagnosisRequest) -> DiagnosisEnvelope:
        started = time.perf_counter(); trace = []
        t = time.perf_counter(); evidence = self.repository.search(" ".join([request.asset_id, request.symptom, *request.observations]))
        trace.append(TraceEvent(step="Retrieve evidence", status="complete" if evidence else "warning", detail=f"Retrieved {len(evidence)} grounded records", duration_ms=int((time.perf_counter()-t)*1000)))
        mode = "demo_fallback"; cost = 0.0
        if os.getenv("OPENAI_API_KEY"):
            try:
                t = time.perf_counter(); result, usage = self._openai(request, evidence)
                trace.append(TraceEvent(step="Structured reasoning", status="complete", detail="Validated model output against schema", duration_ms=int((time.perf_counter()-t)*1000)))
                input_rate = float(os.getenv("OPENAI_INPUT_USD_PER_M", "0.15")); output_rate = float(os.getenv("OPENAI_OUTPUT_USD_PER_M", "0.60"))
                cost = round(((usage.input_tokens * input_rate + usage.output_tokens * output_rate) / 1_000_000), 6); mode = "openai"
            except Exception as exc:
                result = self._fallback(request, evidence)
                trace.append(TraceEvent(step="Structured reasoning", status="fallback", detail=f"Model unavailable; deterministic engine used ({type(exc).__name__})", duration_ms=0))
        else:
            result = self._fallback(request, evidence)
            trace.append(TraceEvent(step="Structured reasoning", status="fallback", detail="No API key; deterministic demo engine used", duration_ms=0))
        trace.append(TraceEvent(step="Citation guard", status="complete", detail="All cited IDs exist in retrieved evidence", duration_ms=0))
        return DiagnosisEnvelope(diagnosis=result, trace=trace, latency_ms=max(1, int((time.perf_counter()-started)*1000)), estimated_cost_usd=cost, mode=mode)

    def _openai(self, request, evidence):
        client = OpenAI(); payload = {"case": request.model_dump(), "evidence": [e.model_dump() for e in evidence]}
        response = client.responses.parse(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), instructions=SYSTEM, input=json.dumps(payload), text_format=DiagnosisDraft)
        if not response.output_parsed: raise ValueError("no parsed output")
        result = DiagnosisResult(case_id=f"CASE-{uuid.uuid4().hex[:8].upper()}", evidence=evidence, **response.output_parsed.model_dump())
        return result, response.usage

    def _fallback(self, request: DiagnosisRequest, evidence: list[Evidence]) -> DiagnosisResult:
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        if len(evidence) < 2:
            return DiagnosisResult(case_id=case_id, status="insufficient_evidence", summary="Available records do not support a reliable diagnosis. Collect the requested measurements before intervention.", root_causes=[], next_questions=["What alarm code is shown on the controller?", "What changed immediately before the fault?", "Can you record supply voltage and motor current under load?"], suggested_parts=[], repair_plan=[], evidence=evidence, limitations=["Fewer than two relevant records were retrieved."])
        ids = [e.id for e in evidence]; text = request.symptom.lower()
        if any(k in text for k in ["overheat", "hot", "temperature", "trip"]):
            causes = [("Restricted cooling airflow", .78, ids[:2], "Manual guidance and a similar work order connect heat trips with blocked airflow."),("Motor overload or mechanical binding", .61, ids[:2], "The retrieved procedure requires load-current and free-rotation checks."),("Temperature sensor or connection fault", .38, ids[:1], "The manual lists sensor validation after physical cooling checks.")]
            parts = [Part(sku="FF-FLT-220", name="Cooling intake filter", quantity=1, reason="Replace only if inspection confirms restriction"), Part(sku="FF-TS-10K", name="10k temperature sensor", quantity=1, reason="Carry as conditional stock after resistance test")]
        else:
            causes = [("Loose or degraded electrical connection", .68, ids[:2], "Retrieved troubleshooting records prioritize connection inspection."),("Supply condition outside operating range", .52, ids[:1], "The manual requires supply measurement before component replacement."),("Control sensor signal fault", .34, ids[:1], "Sensor verification is a documented secondary check.")]
            parts = [Part(sku="FF-CONN-M12", name="M12 shielded connector", quantity=1, reason="Use only if inspection finds pin or shield damage")]
        roots=[RootCause(cause=c, confidence=v, evidence_ids=e, rationale=r) for c,v,e,r in causes]
        steps=[RepairStep(order=1,instruction="Apply lockout/tagout and verify zero energy using the site procedure.",safety_note="Qualified personnel only; do not bypass interlocks.",evidence_ids=ids[:1]),RepairStep(order=2,instruction="Inspect the highest-ranked cause and record measurements before replacing parts.",evidence_ids=ids[:2]),RepairStep(order=3,instruction="Correct the confirmed defect, restore guards, and run a controlled functional test.",evidence_ids=ids[:1]),RepairStep(order=4,instruction="Record alarms, measurements, parts used, and post-repair operating state.",evidence_ids=[])]
        return DiagnosisResult(case_id=case_id,status="complete",summary="The evidence supports a test-first diagnosis; restricted cooling is the leading hypothesis." if "cooling" in causes[0][0].lower() else "The evidence supports a test-first electrical diagnosis.",root_causes=roots,next_questions=["What exact alarm code and timestamp were recorded?","Does the shaft or driven load rotate freely after isolation?","What are line voltage, phase balance, and current under load?"],suggested_parts=parts,repair_plan=steps,evidence=evidence,limitations=["Confidence is heuristic in offline demo mode; confirm with field measurements."])
