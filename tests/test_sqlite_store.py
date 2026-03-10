from app.storage.sqlite_store import SQLiteStore


def test_store_creates_core_tables(tmp_path):
    store = SQLiteStore(tmp_path / "assistant.db")
    tables = store.list_tables()
    assert "reading_state" in tables
    assert "character_aliases" in tables
    assert "character_cards" in tables
