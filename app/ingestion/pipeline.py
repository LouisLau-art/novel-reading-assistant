from __future__ import annotations

from pathlib import Path

from app.ingestion.chapter_parser import parse_novel_text
from app.ingestion.chunker import chunk_text


def ingest_txt_novel(path: Path) -> dict:
    source = Path(path)
    text = source.read_text(encoding="utf-8", errors="ignore")
    novel = parse_novel_text(text, title=source.stem)

    chunks: list[dict] = []
    for chapter in novel.chapters:
        for chunk in chunk_text(
            chapter_idx=chapter.chapter_idx,
            chapter_order=chapter.global_idx,
            chapter_title=chapter.title,
            content=chapter.content,
        ):
            chunks.append(
                {
                    "id": f"{source.stem}-{chunk['chunk_id']}",
                    "document": chunk["text"],
                    "metadata": {
                        "book_title": source.stem,
                        "volume_title": chapter.volume_title,
                        "chapter_idx": chapter.chapter_idx,
                        "chapter_order": chapter.global_idx,
                        "chapter_title": chapter.title,
                        "source_type": "novel",
                    },
                }
            )

    chapters = [
        {
            "chapter_idx": chapter.chapter_idx,
            "chapter_order": chapter.global_idx,
            "chapter_title": chapter.title,
            "volume_title": chapter.volume_title,
            "content": chapter.content,
        }
        for chapter in novel.chapters
    ]

    return {
        "book_title": source.stem,
        "volume_title": novel.volume_title,
        "chapters": chapters,
        "chunks": chunks,
    }
