from app.progress.state import ReadingStateStore


def test_reading_state_round_trip(tmp_path):
    store = ReadingStateStore(tmp_path / "reading_state.json")
    store.save(book_id="book-1", chapter_idx=88)
    state = store.load()
    assert state["book_id"] == "book-1"
    assert state["chapter_idx"] == 88
