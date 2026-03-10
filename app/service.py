from __future__ import annotations

from app.answering.compose import compose_answer
from app.retrieval.alias_resolver import AliasResolver
from app.retrieval.retrieve import filter_by_progress


class ReadingAssistant:
    def __init__(self, alias_map: dict[str, str], llm_client: object | None = None) -> None:
        self.resolver = AliasResolver(alias_map)
        self.llm_client = llm_client

    def answer(
        self,
        question: str,
        current_chapter_idx: int,
        novel_docs: list[dict],
        character_cards: dict[str, dict],
        history_cards: list[dict],
    ) -> str:
        canonical_name = self.resolver.resolve(question) or question
        filtered_docs = filter_by_progress(novel_docs, current_chapter_idx)

        person_summary = self._person_summary(
            question,
            canonical_name,
            character_cards,
            current_chapter_idx,
        )
        scene_summary = self._scene_summary(question, canonical_name, filtered_docs)
        history_summary = self._history_summary(
            question,
            canonical_name,
            history_cards,
            current_chapter_idx,
        )

        if self.llm_client is not None:
            prompt = self._build_llm_prompt(
                question=question,
                chapter_idx=current_chapter_idx,
                person_summary=person_summary,
                scene_summary=scene_summary,
                history_summary=history_summary,
            )
            return str(self.llm_client.chat(prompt))

        return compose_answer(
            person_summary=person_summary,
            scene_summary=scene_summary,
            history_summary=history_summary,
            chapter_idx=current_chapter_idx,
        )

    def _person_summary(
        self,
        question: str,
        canonical_name: str,
        character_cards: dict[str, dict],
        current_chapter_idx: int,
    ) -> str:
        card = character_cards.get(canonical_name)
        if not card:
            if canonical_name == question and _looks_like_term_question(question):
                return "这次问题更像术语或背景解释，优先参考正文和历史背景卡。"
            if canonical_name != question:
                return (
                    f"已识别“{_question_subject(question)}”对应人物为“{canonical_name}”，"
                    "当前没有人物卡。"
                )
            return f"未找到 {canonical_name} 的人物卡。"
        if int(card.get("first_chapter_idx", 0)) > current_chapter_idx:
            return f"{canonical_name} 在你当前进度前尚未正式出场。"
        return str(card.get("summary", f"已识别人物 {canonical_name}。"))

    def _scene_summary(
        self,
        question: str,
        canonical_name: str,
        filtered_docs: list[dict],
    ) -> str:
        for doc in filtered_docs:
            text = str(doc.get("text", ""))
            if question in text or canonical_name in text:
                return f"{doc.get('chapter_title', '未知章节')}：{text}"
        if filtered_docs:
            fallback = filtered_docs[0]
            return f"{fallback.get('chapter_title', '未知章节')}：{fallback.get('text', '')}"
        return "在已读章节中没有找到直接对应的正文片段。"

    def _history_summary(
        self,
        question: str,
        canonical_name: str,
        history_cards: list[dict],
        current_chapter_idx: int,
    ) -> str:
        lowered_question = question.lower()
        lowered_canonical_name = canonical_name.lower()
        for card in history_cards:
            min_chapter_idx = int(card.get("min_chapter_idx", 0))
            if min_chapter_idx > current_chapter_idx:
                continue
            keywords = [
                str(item).strip().lower()
                for item in card.get("keywords", [])
                if str(item).strip()
            ]
            if any(
                keyword == lowered_canonical_name or keyword in lowered_question
                for keyword in keywords
            ):
                return str(card.get("summary", ""))
        return "当前没有匹配到明确的历史背景卡。"

    def _build_llm_prompt(
        self,
        question: str,
        chapter_idx: int,
        person_summary: str,
        scene_summary: str,
        history_summary: str,
    ) -> str:
        return (
            "你是一个防剧透的中文小说阅读助手。\n"
            f"用户问题：{question}\n"
            f"回答范围：只能基于用户读到的第 {chapter_idx} 章之前。\n\n"
            "请只根据下面材料作答，不要补充材料之外的信息，不要剧透。\n\n"
            f"人物/术语解释：\n{person_summary}\n\n"
            f"小说内解释：\n{scene_summary}\n\n"
            f"历史背景解释：\n{history_summary}\n"
        )


def _question_subject(question: str) -> str:
    subject = question.strip().rstrip("？?")
    for suffix in ("是谁", "是什么", "指谁", "指什么", "是哪个人"):
        if subject.endswith(suffix):
            return subject[: -len(suffix)] or subject
    return subject


def _looks_like_term_question(question: str) -> bool:
    normalized = question.strip().rstrip("？?").lower()
    return normalized.endswith(("是什么意思", "是什么", "指什么", "什么意思", "啥意思"))
