from __future__ import annotations

import json
import re
from pathlib import Path


class LocalVectorIndex:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _collection_path(self, collection_name: str) -> Path:
        return self.root / f"{collection_name}.json"

    def _load(self, collection_name: str) -> list[dict]:
        path = self._collection_path(collection_name)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, collection_name: str, records: list[dict]) -> None:
        path = self._collection_path(collection_name)
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    def replace_many(self, collection_name: str, items: list[dict]) -> None:
        self._save(collection_name, list(items))

    def upsert_many(self, collection_name: str, items: list[dict]) -> None:
        existing = {record["id"]: record for record in self._load(collection_name)}
        for item in items:
            existing[item["id"]] = item
        self._save(collection_name, list(existing.values()))

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: dict | None = None,
    ) -> list[dict]:
        candidates = [
            record
            for record in self._load(collection_name)
            if _match_where(record.get("metadata", {}), where or {})
        ]
        scored = sorted(
            candidates,
            key=lambda item: _score(query_text, item.get("document", "")),
            reverse=True,
        )
        return [item for item in scored[:n_results] if _score(query_text, item.get("document", "")) > 0]


def _score(query_text: str, document: str) -> int:
    score = 0
    for term in _candidate_terms(query_text):
        if term and term in document:
            score += max(len(term), 1)
    if query_text in document:
        score += len(query_text) * 2
    return score


def _candidate_terms(query_text: str) -> list[str]:
    normalized = query_text.strip()
    if not normalized:
        return []

    terms: set[str] = {normalized}
    terms.update(part for part in normalized.split() if part)
    terms.update(re.findall(r"[A-Za-z0-9_]+", normalized))

    for run in re.findall(r"[\u4e00-\u9fff]+", normalized):
        terms.add(run)
        max_len = min(4, len(run))
        for size in range(2, max_len + 1):
            for start in range(0, len(run) - size + 1):
                terms.add(run[start : start + size])

    return sorted(terms, key=len, reverse=True)


def _match_where(metadata: dict, where: dict) -> bool:
    if not where:
        return True
    for key, condition in where.items():
        value = metadata.get(key)
        if isinstance(condition, dict):
            for op, expected in condition.items():
                if op == "$lte" and not (value is not None and value <= expected):
                    return False
                if op == "$gte" and not (value is not None and value >= expected):
                    return False
                if op == "$eq" and value != expected:
                    return False
        elif value != condition:
            return False
    return True
