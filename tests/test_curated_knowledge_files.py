from pathlib import Path

from app.knowledge.cards import load_character_cards, load_history_cards
from app.retrieval.alias_resolver import load_alias_map


def test_curated_knowledge_files_exist_and_load():
    root = Path("/root/novel-reading-assistant/data/curated/zaizhitianxia")
    alias_file = root / "character_aliases.curated.csv"
    character_cards_file = root / "character_cards.curated.jsonl"
    history_cards_file = root / "history_cards.curated.jsonl"

    assert alias_file.exists()
    assert character_cards_file.exists()
    assert history_cards_file.exists()

    alias_map = load_alias_map(alias_file)
    character_cards = load_character_cards(character_cards_file)
    history_cards = load_history_cards(history_cards_file)

    assert alias_map["玉昆"] == "韩冈"
    assert alias_map["子厚"] == "张载"
    assert "韩冈" in character_cards
    assert character_cards["韩冈"]["summary"]
    assert any("表字" in card.get("keywords", []) for card in history_cards)
