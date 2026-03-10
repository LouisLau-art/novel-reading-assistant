from __future__ import annotations

from math import ceil


def chunk_text(
    chapter_idx: int,
    chapter_title: str,
    content: str,
    chapter_order: int | None = None,
    chunk_size: int = 120,
    overlap: int = 20,
) -> list[dict[str, int | str]]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    text = content.strip()
    if not text:
        return []

    chunks: list[dict[str, int | str]] = []
    start = 0
    step = chunk_size - overlap
    total = ceil(max(len(text) - overlap, 1) / step)
    order = chapter_order or chapter_idx

    for index in range(total):
        end = start + chunk_size
        chunk = text[start:end]
        if not chunk:
            break
        chunks.append(
            {
                "chunk_id": f"{order}-{index + 1}",
                "parent_id": f"chapter-{order}",
                "chapter_idx": chapter_idx,
                "chapter_order": order,
                "chapter_title": chapter_title,
                "text": chunk,
            }
        )
        if end >= len(text):
            break
        start += step

    return chunks
