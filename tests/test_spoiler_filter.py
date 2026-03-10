from app.retrieval.retrieve import filter_by_progress


def test_filter_by_progress_removes_future_chunks():
    docs = [
        {"text": "已读内容", "chapter_idx": 10},
        {"text": "未来内容", "chapter_idx": 20},
    ]
    result = filter_by_progress(docs, current_chapter_idx=12)
    assert [d["text"] for d in result] == ["已读内容"]


def test_filter_by_progress_prefers_global_chapter_order_when_available():
    docs = [
        {"text": "第一卷第一章", "chapter_idx": 1, "chapter_order": 1},
        {"text": "第二卷第一章", "chapter_idx": 1, "chapter_order": 2},
    ]

    result = filter_by_progress(docs, current_chapter_idx=1)

    assert [d["text"] for d in result] == ["第一卷第一章"]
