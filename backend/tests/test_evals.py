import json
from pathlib import Path
from app.diagnosis import DiagnosisService
from app.models import DiagnosisRequest
from app.main import repo

def test_all_eval_cases_meet_retrieval_and_abstention_contract():
    cases=json.loads((Path(__file__).parents[2]/'evals/cases.json').read_text()); repo.ingest(); service=DiagnosisService(repo)
    for case in cases:
        result=service.diagnose(DiagnosisRequest(asset_id=case['asset'],symptom=case['symptom'])).diagnosis
        assert result.status==case['expected_status'],case['id']
        if case['expected_evidence']:
            assert case['expected_evidence'] in {e.id for e in result.evidence},case['id']
        if result.status=='complete':
            ids={e.id for e in result.evidence}
            assert all(set(c.evidence_ids)<=ids for c in result.root_causes),case['id']
