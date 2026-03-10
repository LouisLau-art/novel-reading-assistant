from pathlib import Path

from app.knowledge.cards import load_character_cards, load_history_cards
from app.retrieval.alias_resolver import load_alias_map

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_curated_knowledge_files_exist_and_load():
    root = PROJECT_ROOT / "data/curated/zaizhitianxia"
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
    assert alias_map["横渠先生"] == "张载"
    assert alias_map["宋神宗"] == "赵顼"
    assert "韩冈" in character_cards
    assert character_cards["韩冈"]["summary"]
    assert "韩琦" in character_cards
    assert "李元昊" in character_cards
    assert "赵顼" in character_cards
    assert "王安石" in character_cards
    assert "司马光" in character_cards
    assert any("表字" in card.get("keywords", []) for card in history_cards)
    assert any("民夫" in card.get("keywords", []) for card in history_cards)
    assert any("关学" in card.get("keywords", []) for card in history_cards)
    assert any("飞将庙" in card.get("keywords", []) for card in history_cards)
    assert any("养娘" in card.get("keywords", []) for card in history_cards)
    assert any("党项" in card.get("keywords", []) for card in history_cards)
    assert any("秀才" in card.get("keywords", []) for card in history_cards)
    assert any("机宜" in card.get("keywords", []) for card in history_cards)
