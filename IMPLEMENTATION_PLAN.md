# FieldFix AI — implementation plan

1. Build a replaceable repository over synthetic manuals and work orders, with idempotent SQLite ingestion.
2. Expose a FastAPI diagnosis workflow that retrieves evidence, produces schema-validated output, enforces citations, and falls back deterministically without an API key.
3. Build an industrial case-workspace UI covering diagnosis, evidence, execution trace, telemetry, approval, and service reporting.
4. Add backend unit/API tests, a Playwright end-to-end test, Docker Compose, GitHub Actions, and 20 evaluation cases.
5. Verify clean-start commands and review for safety, evidence grounding, and demo resilience.

