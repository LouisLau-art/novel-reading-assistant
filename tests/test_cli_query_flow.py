from pathlib import Path

from app.api.cli import answer_question, ingest_source
from app.retrieval.alias_resolver import load_alias_map
from app.retrieval.vector_index import LocalVectorIndex


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


def test_answer_question_can_use_llm_client_without_future_spoilers(tmp_path: Path):
    class FakeLLM:
        def __init__(self) -> None:
            self.prompt = ""

        def chat(self, prompt: str) -> str:
            self.prompt = prompt
            return "这是 LLM 生成的最终回答。"

    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "韩冈刚刚醒来。\n\n"
        "第二章 后文剧透章\n"
        "韩冈后来权势大变。\n",
        encoding="utf-8",
    )

    index_root = tmp_path / "index"
    ingest_source(source=source, index_root=index_root)
    llm = FakeLLM()

    answer = answer_question(
        question="韩冈是谁",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
        llm_client=llm,
    )

    assert answer == "这是 LLM 生成的最终回答。"
    assert "第二章" not in llm.prompt
    assert "第一章" in llm.prompt


def test_cli_helpers_do_not_leak_later_volumes_with_reset_chapter_numbers(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "卷一之卷 起始\n"
        "卷一之卷\n"
        "起始\n\n"
        "第一章 第一卷第一章\n"
        "第一章\n"
        "第一卷第一章\n"
        "韩冈刚刚醒来，这是开篇内容。\n\n"
        "卷二之卷 续篇\n"
        "卷二之卷\n"
        "续篇\n\n"
        "第一章 第二卷第一章\n"
        "第一章\n"
        "第二卷第一章\n"
        "韩冈后来入相，这是后文内容。\n",
        encoding="utf-8",
    )

    index_root = tmp_path / "index"
    ingest_source(source=source, index_root=index_root)

    answer = answer_question(
        question="韩冈是谁",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
    )

    assert "第一卷第一章" in answer
    assert "第二卷第一章" not in answer
    assert "后文内容" not in answer


def test_answer_question_prefers_global_chapter_order_for_same_chapter_numbers(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "卷一之卷 起始\n"
        "卷一之卷\n"
        "起始\n\n"
        "第一章 第一卷第一章\n"
        "第一章\n"
        "第一卷第一章\n"
        "韩冈初登场。\n\n"
        "卷二之卷 续篇\n"
        "卷二之卷\n"
        "续篇\n\n"
        "第一章 第二卷第一章\n"
        "第一章\n"
        "第二卷第一章\n"
        "韩冈 韩冈 韩冈 这是明显后文。\n",
        encoding="utf-8",
    )

    index_root = tmp_path / "index"
    ingest_source(source=source, index_root=index_root)

    answer = answer_question(
        question="韩冈是谁",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
        n_results=10,
    )

    assert "第一卷第一章" in answer
    assert "第二卷第一章" not in answer
    assert "明显后文" not in answer


def test_answer_question_excludes_future_volume_even_if_only_future_chunk_matches(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "卷一之卷 起始\n"
        "卷一之卷\n"
        "起始\n\n"
        "第一章 第一卷第一章\n"
        "第一章\n"
        "第一卷第一章\n"
        "韩冈初登场。\n\n"
        "卷二之卷 续篇\n"
        "卷二之卷\n"
        "续篇\n\n"
        "第一章 第二卷第一章\n"
        "第一章\n"
        "第二卷第一章\n"
        "后文关键词只出现在这里。\n",
        encoding="utf-8",
    )

    index_root = tmp_path / "index"
    ingest_source(source=source, index_root=index_root)

    answer = answer_question(
        question="后文关键词",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
        n_results=10,
    )

    assert "第二卷第一章" not in answer
    assert "后文关键词只出现在这里" not in answer


def test_answer_question_uses_chapter_order_before_ranking_results(tmp_path: Path):
    index_root = tmp_path / "index"
    index = LocalVectorIndex(index_root)
    index.upsert_many(
        "novel",
        [
            {
                "id": "future",
                "document": "韩冈在第二卷已经位极人臣。",
                "metadata": {
                    "chapter_idx": 1,
                    "chapter_order": 2,
                    "chapter_title": "第二卷第一章",
                },
            },
            {
                "id": "past",
                "document": "韩冈刚刚醒来。",
                "metadata": {
                    "chapter_idx": 1,
                    "chapter_order": 1,
                    "chapter_title": "第一卷第一章",
                },
            },
        ],
    )

    answer = answer_question(
        question="韩冈是谁",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
        n_results=1,
    )

    assert "第一卷第一章" in answer
    assert "第二卷第一章" not in answer
    assert "位极人臣" not in answer


def test_answer_question_prefers_subject_term_over_generic_question_suffix(tmp_path: Path):
    index_root = tmp_path / "index"
    index = LocalVectorIndex(index_root)
    index.upsert_many(
        "novel",
        [
            {
                "id": "generic",
                "document": "贺方看着字帖，心想这到底是什么意思。",
                "metadata": {
                    "chapter_idx": 1,
                    "chapter_order": 1,
                    "chapter_title": "第一章",
                },
            },
            {
                "id": "target",
                "document": "边地百姓常被征发起来充当民夫，负责运粮和筑城。",
                "metadata": {
                    "chapter_idx": 1,
                    "chapter_order": 1,
                    "chapter_title": "第一章",
                },
            },
        ],
    )

    answer = answer_question(
        question="民夫是什么意思",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
        n_results=1,
    )

    assert "充当民夫" in answer
    assert "这到底是什么意思" not in answer


def test_answer_question_strips_meaning_suffix_for_term_queries(tmp_path: Path):
    index_root = tmp_path / "index"
    index = LocalVectorIndex(index_root)
    index.upsert_many(
        "novel",
        [
            {
                "id": "generic",
                "document": "韩冈一时想不明白这是什么意思，心里只觉得莫名其妙。",
                "metadata": {
                    "chapter_idx": 1,
                    "chapter_order": 1,
                    "chapter_title": "第一章",
                },
            },
            {
                "id": "target",
                "document": "所谓养娘，是宋代对家养婢女的一种称呼。",
                "metadata": {
                    "chapter_idx": 1,
                    "chapter_order": 1,
                    "chapter_title": "第一章",
                },
            },
        ],
    )

    answer = answer_question(
        question="养娘是什么意思",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
        n_results=1,
    )

    assert "所谓养娘" in answer
    assert "莫名其妙" not in answer


def test_ingest_source_replaces_existing_collection_contents(tmp_path: Path):
    first_source = tmp_path / "first.txt"
    first_source.write_text(
        "第一章 开始\n"
        "这是旧索引内容。\n",
        encoding="utf-8",
    )
    second_source = tmp_path / "second.txt"
    second_source.write_text(
        "第一章 开始\n"
        "这是新索引内容。\n",
        encoding="utf-8",
    )

    index_root = tmp_path / "index"
    ingest_source(source=first_source, index_root=index_root, collection_name="novel")
    ingest_source(source=second_source, index_root=index_root, collection_name="novel")

    answer = answer_question(
        question="旧索引内容",
        chapter_idx=1,
        index_root=index_root,
        collection_name="novel",
        n_results=10,
    )

    assert "这是旧索引内容。" not in answer
    assert "这是新索引内容。" in answer
