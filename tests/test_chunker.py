from app.ingestion.chunker import chunk_text


def test_chunk_text_preserves_chapter_metadata():
    chunks = chunk_text(
        chapter_idx=12,
        chapter_title="第十二章 风起",
        content="甲乙丙丁戊己庚辛壬癸" * 20,
        chunk_size=40,
        overlap=10,
    )
    assert chunks
    assert chunks[0]["chapter_idx"] == 12
    assert chunks[0]["chapter_title"] == "第十二章 风起"
