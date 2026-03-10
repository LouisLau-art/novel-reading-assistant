from app.retrieval.retrieve import filter_by_progress


def test_filter_by_progress_removes_future_chunks():
    docs = [
        {"text": "已读内容", "chapter_idx": 10},
        {"text": "未来内容", "chapter_idx": 20},
    ]
    result = filter_by_progress(docs, current_chapter_idx=12)
    assert [d["text"] for d in result] == ["已读内容"]
