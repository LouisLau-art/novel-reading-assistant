from app.answering.compose import compose_answer


def test_compose_answer_contains_required_sections():
    text = compose_answer(
        person_summary="韩冈，截至第十章前的重要人物。",
        scene_summary="这段对话在讨论政局。",
        history_summary="涉及王安石变法背景。",
        chapter_idx=10,
    )
    assert "人物/术语解释" in text
    assert "小说内解释" in text
    assert "历史背景解释" in text
