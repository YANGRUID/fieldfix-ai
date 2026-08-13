# Architecture

```mermaid
flowchart LR
  U["Field technician"] --> W["React case workspace"]
  W -->|REST| A["FastAPI diagnosis API"]
  A --> R["Retrieval service"]
  R --> S[("SQLite / JSON sources")]
  A --> L["OpenAI Responses API"]
  L --> V["Pydantic validation + citation guard"]
  A --> F["Deterministic demo engine"]
  F --> V
  V --> W
  W --> P["Human approval + service report"]
```

## Boundaries

- `backend/app/repository.py`: persistence and lexical retrieval. The service only depends on its interface.
- `backend/app/diagnosis.py`: orchestration, model adapter, fallback, citation guard, and telemetry.
- `backend/app/models.py`: API and model-output contracts.
- `backend/app/main.py`: HTTP boundary and lifecycle only.
- `frontend/src`: case-oriented UI and API adapter.

The workflow is deliberately a single agent pipeline: retrieve, reason, validate, approve, report.

