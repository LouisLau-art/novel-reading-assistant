from pathlib import Path

from app.api.cli import answer_question, ingest_source
from app.retrieval.alias_resolver import load_alias_map


def test_cli_helpers_can_ingest_and_answer_without_future_spoilers(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "初六之卷 塞上枕戈\n"
        "初六之卷\n"
        "塞上枕戈\n\n"
        "第一章 劫后梦醒世事更\n"
        "第一章\n"
        "劫后梦醒世事更\n"
        "韩冈，表字玉昆，刚刚醒来。\n\n"
        "第二章 后文剧透章\n"
        "第二章\n"
        "后文剧透章\n"
        "韩冈后来权势大变，这是后文信息。\n",
        encoding="utf-8",
    )

    index_root = tmp_path / "index"
    stats = ingest_source(source=source, index_root=index_root)

    assert stats["chapter_count"] == 2
    answer = answer_question(
        question="玉昆是谁",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
    )

    assert "仅基于你读到的第 1 章之前" in answer
    assert "第一章" in answer
    assert "第二章" not in answer


def test_cli_answer_can_expand_alias_to_canonical_name(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "韩冈刚刚醒来。\n",
        encoding="utf-8",
    )
    alias_file = tmp_path / "aliases.csv"
    alias_file.write_text(
        "alias,canonical_name,alias_type\n"
        "玉昆,韩冈,courtesy_name\n",
        encoding="utf-8",
    )

    index_root = tmp_path / "index"
    ingest_source(source=source, index_root=index_root)

    answer = answer_question(
        question="玉昆是谁",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
        alias_map=load_alias_map(alias_file),
    )

    assert "韩冈刚刚醒来" in answer
