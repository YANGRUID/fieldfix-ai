import os
os.environ.pop("OPENAI_API_KEY", None)
from fastapi.testclient import TestClient
from app.main import app, repo

client=TestClient(app)
def test_ingestion_is_idempotent():
    assert repo.ingest()==repo.ingest()==8

def test_grounded_offline_diagnosis_and_report():
    with client:
        response=client.post('/api/diagnose',json={'asset_id':'AX-200-P17','symptom':'T17 overheat trip and weak airflow','observations':['hot motor']})
    assert response.status_code==200
    body=response.json(); d=body['diagnosis']; ids={e['id'] for e in d['evidence']}
    assert body['mode']=='demo_fallback'; assert len(d['root_causes'])==3
    assert all(set(c['evidence_ids']) <= ids for c in d['root_causes'])
    report=client.post('/api/reports',json={'diagnosis':d,'approval':{'approved':True,'technician':'Test Tech','notes':''}})
    assert report.status_code==200 and report.json()['probable_cause']==d['root_causes'][0]['cause']

def test_unknown_problem_declares_insufficient_evidence():
    with client:
        d=client.post('/api/diagnose',json={'asset_id':'ZZ-999','symptom':'purple display flickers mysteriously'}).json()['diagnosis']
    assert d['status']=='insufficient_evidence' and not d['root_causes']

def test_unapproved_report_is_rejected():
    with client:
        d=client.post('/api/diagnose',json={'asset_id':'AX-200','symptom':'overheat trip weak airflow'}).json()['diagnosis']
    assert client.post('/api/reports',json={'diagnosis':d,'approval':{'approved':False,'technician':'Test Tech'}}).status_code==409
