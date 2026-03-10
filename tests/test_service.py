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


def test_reading_assistant_can_delegate_final_response_to_llm():
    class FakeLLM:
        def __init__(self) -> None:
            self.prompt = ""

        def chat(self, prompt: str) -> str:
            self.prompt = prompt
            return "这是 LLM 生成的回答。"

    llm = FakeLLM()
    assistant = ReadingAssistant({"玉昆": "韩冈", "韩冈": "韩冈"}, llm_client=llm)
    answer = assistant.answer(
        question="玉昆是谁",
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

    assert answer == "这是 LLM 生成的回答。"
    assert "第二十章" not in llm.prompt
    assert "韩冈，截至第十章前的重要人物。" in llm.prompt


def test_reading_assistant_includes_alias_resolution_in_prompt_without_character_card():
    class FakeLLM:
        def __init__(self) -> None:
            self.prompt = ""

        def chat(self, prompt: str) -> str:
            self.prompt = prompt
            return "这是 LLM 生成的回答。"

    llm = FakeLLM()
    assistant = ReadingAssistant({"玉昆": "韩冈", "韩冈": "韩冈"}, llm_client=llm)
    assistant.answer(
        question="玉昆是谁",
        current_chapter_idx=5,
        novel_docs=[
            {"chapter_idx": 2, "chapter_title": "第二章", "text": "旧主姓韩名冈，有个表字唤作玉昆。"},
        ],
        character_cards={},
        history_cards=[],
    )

    assert "玉昆" in llm.prompt
    assert "韩冈" in llm.prompt
    assert "对应人物" in llm.prompt
