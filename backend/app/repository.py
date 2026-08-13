from __future__ import annotations

import json, re, sqlite3
from pathlib import Path
from .models import Evidence


class KnowledgeRepository:
    def __init__(self, db_path: Path, data_dir: Path):
        self.db_path, self.data_dir = db_path, data_dir

    def connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def ingest(self) -> int:
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, source_type TEXT, title TEXT, locator TEXT, content TEXT)")
            count = 0
            for path in sorted(self.data_dir.glob("*.json")):
                for doc in json.loads(path.read_text()):
                    db.execute("INSERT INTO documents VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET source_type=excluded.source_type,title=excluded.title,locator=excluded.locator,content=excluded.content", (doc["id"], doc["source_type"], doc["title"], doc["locator"], doc["content"]))
                    count += 1
            db.commit()
        return count

    def search(self, query: str, limit: int = 6) -> list[Evidence]:
        terms = set(re.findall(r"[a-z0-9]+", query.lower())) - {"the", "and", "is", "a", "to"}
        with self.connect() as db:
            rows = db.execute("SELECT id,source_type,title,locator,content FROM documents").fetchall()
        ranked = []
        for row in rows:
            words = set(re.findall(r"[a-z0-9]+", " ".join(row).lower()))
            overlap = len(terms & words)
            if overlap:
                score = min(1.0, overlap / max(3, len(terms)) + (0.15 if row[1] == "manual" else 0.1))
                ranked.append((score, row))
        ranked.sort(reverse=True, key=lambda x: x[0])
        return [Evidence(id=r[0], source_type=r[1], title=r[2], locator=r[3], excerpt=r[4][:340], score=round(s, 2)) for s, r in ranked[:limit]]
