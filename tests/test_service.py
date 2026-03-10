from app.service import ReadingAssistant


def test_reading_assistant_answers_without_future_docs():
    assistant = ReadingAssistant({"玉昆": "韩冈", "韩冈": "韩冈"})
    answer = assistant.answer(
        question="玉昆",
        current_chapter_idx=10,
        novel_docs=[
            {"chapter_idx": 8, "chapter_title": "第八章", "text": "韩冈在第八章现身。"},
            {"chapter_idx": 20, "chapter_title": "第二十章", "text": "韩冈后文有大变化。"},
        ],
        character_cards={
            "韩冈": {"first_chapter_idx": 1, "summary": "韩冈，截至第十章前的重要人物。"}
        },
        history_cards=[
            {"keywords": ["韩冈"], "summary": "这里涉及北宋政局与新法讨论。"}
        ],
    )
    assert "第二十章" not in answer
    assert "韩冈，截至第十章前的重要人物。" in answer
