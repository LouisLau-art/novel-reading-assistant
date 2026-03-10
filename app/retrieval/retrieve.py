from __future__ import annotations


def filter_by_progress(docs: list[dict], current_chapter_idx: int) -> list[dict]:
    return [
        doc
        for doc in docs
        if int(doc.get("chapter_order", doc.get("chapter_idx", current_chapter_idx)))
        <= current_chapter_idx
    ]
