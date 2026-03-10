from __future__ import annotations

import json
from pathlib import Path


class ReadingStateStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, book_id: str, chapter_idx: int) -> None:
        payload = {"book_id": book_id, "chapter_idx": chapter_idx}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> dict[str, int | str]:
        if not self.path.exists():
            return {"book_id": "", "chapter_idx": 0}
        return json.loads(self.path.read_text(encoding="utf-8"))
