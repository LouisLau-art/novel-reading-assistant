from __future__ import annotations

import json
import math
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
        path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )

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

        query_terms = _candidate_terms(query_text)
        corpus_documents = [cand.get("document", "") for cand in candidates]
        idf, avgdl = _compute_idf(corpus_documents, query_terms)

        scored = sorted(
            candidates,
            key=lambda item: _score(query_terms, item.get("document", ""), idf, avgdl),
            reverse=True,
        )
        return [
            item
            for item in scored[:n_results]
            if _score(query_terms, item.get("document", ""), idf, avgdl) > 0
        ]

def _compute_idf(
    corpus_documents: list[str], query_terms: list[str]
) -> tuple[dict[str, float], float]:

    N = len(corpus_documents)
    if N == 0:
        return {}, 0.0

    idf = {}
    doc_terms_list = [_candidate_terms(doc) for doc in corpus_documents]
    avgdl = sum(len(dt) for dt in doc_terms_list) / N

    for q_term in query_terms:
        n_qi = sum(1 for dt in doc_terms_list if q_term in dt)
        idf[q_term] = math.log(1.0 + (N - n_qi + 0.5) / (n_qi + 0.5))

    return idf, avgdl

def _score(
    query_terms: list[str],
    document: str,
    idf: dict[str, float],
    avgdl: float,
) -> float:
    k1 = 1.2
    b = 0.75
    score = 0.0
    doc_terms = _candidate_terms(document)
    doc_len = len(doc_terms)

    if doc_len == 0 or avgdl == 0.0:
        return 0.0

    for q_term in query_terms:
        if q_term in doc_terms:
            tf = document.count(q_term)
            score += (
                idf.get(q_term, 0.0)
                * (tf * (k1 + 1))
                / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
            )

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
