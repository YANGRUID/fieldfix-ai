# ADR 003: Validate before presenting

Status: Accepted

Model output is parsed into Pydantic models. A cross-field validator rejects citations absent from retrieved evidence. Sparse retrieval produces an explicit `insufficient_evidence` result. Offline fallback follows the same schema and guard.
