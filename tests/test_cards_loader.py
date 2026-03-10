from pathlib import Path

from app.knowledge.cards import load_character_cards, load_history_cards


def test_load_character_and_history_cards_from_jsonl(tmp_path: Path):
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

    character_cards = load_character_cards(character_cards_file)
    history_cards = load_history_cards(history_cards_file)

    assert character_cards["韩冈"]["summary"] == "韩冈，截至第一章前的重要人物。"
    assert history_cards[0]["keywords"] == ["韩冈", "新法"]

