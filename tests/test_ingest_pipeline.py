from pathlib import Path

from app.ingestion.pipeline import ingest_txt_novel


def test_ingest_txt_novel_builds_chunk_records(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "初六之卷 塞上枕戈\n"
        "初六之卷\n"
        "塞上枕戈\n\n"
        "第一章 劫后梦醒世事更\n"
        "第一章\n"
        "劫后梦醒世事更\n"
        "韩冈初登场。\n",
        encoding="utf-8",
    )
    payload = ingest_txt_novel(source)
    assert payload["book_title"] == "novel"
    assert payload["chapters"][0]["chapter_title"] == "第一章 劫后梦醒世事更"
    assert payload["chunks"]
    assert payload["chunks"][0]["metadata"]["chapter_idx"] == 1
    assert payload["chunks"][0]["metadata"]["chapter_order"] == 1


def test_ingest_txt_novel_tracks_global_chapter_order_across_volumes(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "卷一之卷 起始\n"
        "卷一之卷\n"
        "起始\n\n"
        "第一章 第一卷第一章\n"
        "第一章\n"
        "第一卷第一章\n"
        "前文内容。\n\n"
        "卷二之卷 续篇\n"
        "卷二之卷\n"
        "续篇\n\n"
        "第一章 第二卷第一章\n"
        "第一章\n"
        "第二卷第一章\n"
        "后文内容。\n",
        encoding="utf-8",
    )

    payload = ingest_txt_novel(source)

    assert payload["chapters"][0]["chapter_idx"] == 1
    assert payload["chapters"][0]["chapter_order"] == 1
    assert payload["chapters"][1]["chapter_idx"] == 1
    assert payload["chapters"][1]["chapter_order"] == 2
    assert payload["chunks"][0]["metadata"]["chapter_order"] == 1
    assert payload["chunks"][-1]["metadata"]["chapter_order"] == 2
