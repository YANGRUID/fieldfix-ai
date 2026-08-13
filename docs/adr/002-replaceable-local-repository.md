# ADR 002: SQLite behind a repository boundary

Status: Accepted

Synthetic JSON is the source package; idempotent ingestion upserts into SQLite. Diagnosis code depends on `KnowledgeRepository`, allowing later replacement with hybrid/vector search while keeping API contracts stable.
