def compose_answer(
    person_summary: str,
    scene_summary: str,
    history_summary: str,
    chapter_idx: int,
) -> str:
    return (
        f"回答范围声明\n仅基于你读到的第 {chapter_idx} 章之前\n\n"
        f"人物/术语解释\n{person_summary}\n\n"
        f"小说内解释\n{scene_summary}\n\n"
        f"历史背景解释\n{history_summary}\n"
    )
