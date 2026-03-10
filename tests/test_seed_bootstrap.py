from pathlib import Path

from app.bootstrap.seed import bootstrap_seed_files


def test_bootstrap_seed_files_generate_alias_and_character_templates(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "韩冈，字玉昆，刚刚醒来。\n"
        "张载与韩冈交谈。\n"
        "第二章 继续\n"
        "韩冈又见王韶。\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    stats = bootstrap_seed_files(source=source, output_dir=output_dir, max_candidates=10)

    assert stats["character_count"] >= 2
    alias_text = (output_dir / "character_aliases.seed.csv").read_text(encoding="utf-8")
    character_text = (output_dir / "character_cards.seed.jsonl").read_text(encoding="utf-8")
    history_text = (output_dir / "history_cards.seed.jsonl").read_text(encoding="utf-8")

    assert "玉昆,韩冈,courtesy_name" in alias_text
    assert '"canonical_name": "韩冈"' in character_text
    assert history_text == ""


def test_bootstrap_seed_files_extracts_intro_style_aliases(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "旧主姓韩名冈，有个表字唤作玉昆。\n"
        "不过张载表字子厚，是出自于厚德载物一词。\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    bootstrap_seed_files(source=source, output_dir=output_dir, max_candidates=10)

    alias_text = (output_dir / "character_aliases.seed.csv").read_text(encoding="utf-8")

    assert "玉昆,韩冈,courtesy_name" in alias_text
    assert "子厚,张载,courtesy_name" in alias_text


def test_bootstrap_seed_files_filters_common_context_noise(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "所谓养娘，贺方从字面上去理解是养女的意思。\n"
        "韩冈的长兄继承家业。\n"
        "被韩冈一提，路明一下愤怒起来。\n"
        "几年前，韩家三子日夜用功苦读的时候。\n"
        "旧主姓韩名冈，有个表字唤作玉昆。\n"
        "不过张载表字子厚，是出自于厚德载物一词。\n"
        "韩冈道：“久仰王安石。”\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    bootstrap_seed_files(source=source, output_dir=output_dir, max_candidates=20)

    alias_text = (output_dir / "character_aliases.seed.csv").read_text(encoding="utf-8")
    character_text = (output_dir / "character_cards.seed.jsonl").read_text(encoding="utf-8")

    assert "面上去,贺方从,courtesy_name" not in alias_text
    assert "玉昆,韩冈,courtesy_name" in alias_text
    assert "子厚,张载,courtesy_name" in alias_text

    assert '"canonical_name": "韩冈"' in character_text
    assert '"canonical_name": "王安石"' in character_text
    assert '"canonical_name": "韩冈的"' not in character_text
    assert '"canonical_name": "韩冈一"' not in character_text
    assert '"canonical_name": "韩冈道"' not in character_text
    assert '"canonical_name": "时候"' not in character_text


def test_bootstrap_seed_filters_false_alias_matches(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "贺方从字面上去理解是养女的意思。\n"
        "韩冈，字玉昆，刚刚醒来。\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    bootstrap_seed_files(source=source, output_dir=output_dir, max_candidates=10)

    alias_text = (output_dir / "character_aliases.seed.csv").read_text(encoding="utf-8")

    assert "面上去,贺方从,courtesy_name" not in alias_text
    assert "玉昆,韩冈,courtesy_name" in alias_text


def test_bootstrap_seed_supports_self_intro_alias_pattern(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "韩冈微笑着自我介绍：姓韩名冈，草字玉昆的便是。\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    bootstrap_seed_files(source=source, output_dir=output_dir, max_candidates=10)

    alias_text = (output_dir / "character_aliases.seed.csv").read_text(encoding="utf-8")

    assert "玉昆,韩冈,courtesy_name" in alias_text


def test_bootstrap_seed_does_not_duplicate_intro_name_with_name_marker(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "姓韩名冈，草字玉昆的便是。\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    bootstrap_seed_files(source=source, output_dir=output_dir, max_candidates=10)

    alias_text = (output_dir / "character_aliases.seed.csv").read_text(encoding="utf-8")

    assert "玉昆,韩冈,courtesy_name" in alias_text
    assert "玉昆,韩名冈,courtesy_name" not in alias_text


def test_bootstrap_seed_filters_common_word_name_noise(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "韩冈的长兄继承家业。\n"
        "几年前苦读的时候，王安石入京。\n"
        "韩冈说道，张载与韩冈交谈。\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    bootstrap_seed_files(source=source, output_dir=output_dir, max_candidates=10)

    character_text = (output_dir / "character_cards.seed.jsonl").read_text(encoding="utf-8")

    assert '"canonical_name": "韩冈的"' not in character_text
    assert '"canonical_name": "时候"' not in character_text
    assert '"canonical_name": "韩冈"' in character_text
    assert '"canonical_name": "王安石"' in character_text


def test_bootstrap_seed_prefers_full_three_character_names(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "吕嘉问独据一桌。\n"
        "韩冈问道。\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    bootstrap_seed_files(source=source, output_dir=output_dir, max_candidates=10)

    character_text = (output_dir / "character_cards.seed.jsonl").read_text(encoding="utf-8")

    assert '"canonical_name": "吕嘉问"' in character_text
    assert '"canonical_name": "吕嘉"' not in character_text
    assert '"canonical_name": "韩冈"' in character_text


def test_bootstrap_seed_strips_leading_connectors_from_names(tmp_path: Path):
    source = tmp_path / "novel.txt"
    source.write_text(
        "第一章 开始\n"
        "李留哥和韩冈一脸严肃地站在门口。\n"
        "众人对于韩冈也都十分看重。\n"
        "韩冈说道。\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "seed"

    bootstrap_seed_files(source=source, output_dir=output_dir, max_candidates=10)

    character_text = (output_dir / "character_cards.seed.jsonl").read_text(encoding="utf-8")

    assert '"canonical_name": "韩冈"' in character_text
    assert '"canonical_name": "和韩冈"' not in character_text
    assert '"canonical_name": "于韩冈"' not in character_text
