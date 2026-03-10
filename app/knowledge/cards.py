from __future__ import annotations

import json
from pathlib import Path


def load_character_cards(path: Path) -> dict[str, dict]:
    cards: dict[str, dict] = {}
    for record in _load_jsonl(path):
        canonical_name = str(record.get("canonical_name", "")).strip()
        if not canonical_name:
            continue
        cards[canonical_name] = record
    return cards


def load_history_cards(path: Path) -> list[dict]:
    return _load_jsonl(path)


def _load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            records.append(payload)
    return records
