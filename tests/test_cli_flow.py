import subprocess
import sys
from pathlib import Path

from app.api.cli import build_request

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_build_request_keeps_question_and_progress():
    req = build_request("玉昆是谁", chapter_idx=120)
    assert req["question"] == "玉昆是谁"
    assert req["chapter_idx"] == 120


def test_cli_ask_supports_alias_file(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text("第一章 开始\n韩冈刚刚醒来。\n", encoding="utf-8")
    alias_file = tmp_path / "aliases.csv"
    alias_file.write_text(
        "alias,canonical_name,alias_type\n玉昆,韩冈,courtesy_name\n",
        encoding="utf-8",
    )
    index_root = tmp_path / "index"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "app.api.cli",
            "ingest",
            "--source",
            str(source),
            "--index-root",
            str(index_root),
            "--collection-name",
            "novel",
        ],
        check=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.api.cli",
            "ask",
            "--question",
            "玉昆是谁",
            "--chapter-idx",
            "1",
            "--index-root",
            str(index_root),
            "--collection-name",
            "novel",
            "--alias-file",
            str(alias_file),
        ],
        check=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert "韩冈刚刚醒来" in result.stdout


def test_cli_ask_supports_character_and_history_card_files(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text("第一章 开始\n韩冈刚刚醒来。\n", encoding="utf-8")
    alias_file = tmp_path / "aliases.csv"
    alias_file.write_text(
        "alias,canonical_name,alias_type\n玉昆,韩冈,courtesy_name\n",
        encoding="utf-8",
    )
    character_cards_file = tmp_path / "character_cards.jsonl"
    character_cards_file.write_text(
        '{"canonical_name":"韩冈","first_chapter_idx":1,"summary":"韩冈，截至第一章前的重要人物。"}\n',
        encoding="utf-8",
    )
    history_cards_file = tmp_path / "history_cards.jsonl"
    history_cards_file.write_text(
        '{"keywords":["韩冈","新法"],"min_chapter_idx":1,"summary":"这里涉及北宋政局与新法讨论。"}\n',
        encoding="utf-8",
    )
    index_root = tmp_path / "index"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "app.api.cli",
            "ingest",
            "--source",
            str(source),
            "--index-root",
            str(index_root),
            "--collection-name",
            "novel",
        ],
        check=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.api.cli",
            "ask",
            "--question",
            "玉昆是谁",
            "--chapter-idx",
            "1",
            "--index-root",
            str(index_root),
            "--collection-name",
            "novel",
            "--alias-file",
            str(alias_file),
            "--character-cards-file",
            str(character_cards_file),
            "--history-cards-file",
            str(history_cards_file),
        ],
        check=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert "韩冈，截至第一章前的重要人物。" in result.stdout
    assert "这里涉及北宋政局与新法讨论。" in result.stdout


def test_cli_bootstrap_seed_command_generates_seed_files(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "韩冈，字玉昆，刚刚醒来。\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.api.cli",
            "bootstrap-seed",
            "--source",
            str(source),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert "character_count" in result.stdout
    assert (output_dir / "character_aliases.seed.csv").exists()
