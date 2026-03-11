#!/usr/bin/env python3
"""
批量LLM分析工具 - 利用高并发API加速章节内容提取

支持功能:
1. 批量提取人物卡片 - 一次分析多章，提取所有出现的人物
2. 批量提取历史背景 - 一次分析多章，提取历史背景和专有名词解释
3. 并发控制 - 可配置并发数，充分利用API的500 QPS能力
"""

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import Settings
from app.ingestion.chapter_parser import parse_novel_text
from app.llm.volcengine import VolcengineChatClient


@dataclass
class ChapterContent:
    chapter_idx: int
    chapter_title: str
    content: str


@dataclass
class PersonCard:
    canonical_name: str
    first_chapter_idx: int
    summary: str
    alias_type: str = "auto_detected"


@dataclass
class HistoryCard:
    keywords: list[str]
    min_chapter_idx: int
    summary: str


class AsyncVolcengineClient:
    """异步Volcengine客户端，支持高并发"""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        concurrency: int = 100,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.concurrency = concurrency
        self._semaphore: asyncio.Semaphore | None = None

    async def chat_async(self, prompt: str) -> str:
        """异步调用API"""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.concurrency)

        async with self._semaphore:
            # 在线程池中执行同步的HTTP请求
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._chat_sync, prompt)

    def _chat_sync(self, prompt: str) -> str:
        """同步调用API"""
        import urllib.request

        client = VolcengineChatClient(
            api_key=self.api_key,
            model=self.model,
            base_url=self.base_url,
        )
        return client.chat(prompt)


class BatchAnalyzer:
    """批量分析器"""

    def __init__(self, client: AsyncVolcengineClient):
        self.client = client

    async def extract_person_cards(
        self,
        chapters: list[ChapterContent],
        batch_size: int = 10,
    ) -> list[PersonCard]:
        """
        批量提取人物卡片
        每batch_size章一起分析，提取本章出现的人物
        """
        all_cards: list[PersonCard] = []
        first_seen: dict[str, int] = {}

        # 分批处理
        for i in range(0, len(chapters), batch_size):
            batch = chapters[i : i + batch_size]
            print(
                f"  处理章节 {batch[0].chapter_idx}-{batch[-1].chapter_idx} ({len(batch)}章)..."
            )

            # 构建提示词
            prompt = self._build_person_extract_prompt(batch)

            try:
                # 并发调用API
                response = await self.client.chat_async(prompt)
                cards = self._parse_person_response(response, batch)

                for card in cards:
                    if card.canonical_name not in first_seen:
                        first_seen[card.canonical_name] = card.first_chapter_idx
                    all_cards.append(card)
            except Exception as e:
                print(
                    f"    警告: 批次 {batch[0].chapter_idx}-{batch[-1].chapter_idx} 处理失败: {e}"
                )

        # 去重，保留首次出现的章节
        seen = set()
        unique_cards = []
        for card in all_cards:
            if card.canonical_name not in seen:
                seen.add(card.canonical_name)
                card.first_chapter_idx = first_seen[card.canonical_name]
                unique_cards.append(card)

        return unique_cards

    async def extract_history_cards(
        self,
        chapters: list[ChapterContent],
        batch_size: int = 10,
    ) -> list[HistoryCard]:
        """批量提取历史背景卡片"""
        all_cards: list[HistoryCard] = []
        min_chapter: dict[str, int] = {}

        for i in range(0, len(chapters), batch_size):
            batch = chapters[i : i + batch_size]
            print(
                f"  处理章节 {batch[0].chapter_idx}-{batch[-1].chapter_idx} ({len(batch)}章)..."
            )

            prompt = self._build_history_extract_prompt(batch)

            try:
                response = await self.client.chat_async(prompt)
                cards = self._parse_history_response(response, batch[0].chapter_idx)

                for card in cards:
                    all_cards.append(card)
                    for kw in card.keywords:
                        if kw not in min_chapter:
                            min_chapter[kw] = card.min_chapter_idx
            except Exception as e:
                print(f"    警告: 批次处理失败: {e}")

        # 去重
        seen_keywords = set()
        unique_cards = []
        for card in all_cards:
            key = tuple(sorted(card.keywords))
            if key not in seen_keywords:
                seen_keywords.add(key)
                card.min_chapter_idx = min(
                    min_chapter.get(kw, 1) for kw in card.keywords
                )
                unique_cards.append(card)

        return unique_cards

    def _build_person_extract_prompt(self, chapters: list[ChapterContent]) -> str:
        """构建人物提取提示词"""
        # 取每章的前2000字作为样本
        samples = []
        for ch in chapters:
            sample = ch.content[:2000]
            samples.append(f"第{ch.chapter_idx}章 {ch.chapter_title}:\n{sample}")

        content = "\n\n".join(samples)

        return f"""你是一个小说分析助手。请从以下《宰执天下》小说片段中提取所有出现的重要人物。

要求：
1. 只提取有具体姓名的人物（2-4个汉字）
2. 对于每个人物，简要说明其身份或特点（20字以内）
3. 标注人物的首次出现章节

请按以下JSON格式输出（只输出JSON，不要其他内容）：
[
  {{"name": "人物姓名", "chapter": 首次出现章节, "description": "人物身份描述"}},
  ...
]

小说内容：
{content}

请提取人物："""

    def _build_history_extract_prompt(self, chapters: list[ChapterContent]) -> str:
        """构建历史背景提取提示词"""
        samples = []
        for ch in chapters:
            sample = ch.content[:2000]
            samples.append(f"第{ch.chapter_idx}章 {ch.chapter_title}:\n{sample}")

        content = "\n\n".join(samples)

        return f"""你是一个小说历史背景分析助手。请从以下《宰执天下》小说片段中提取重要的历史背景和专有名词。

要求：
1. 提取官职、军事组织、地理名称、历史事件等
2. 简要解释其含义（30字以内）
3. 标注首次出现章节

请按以下JSON格式输出（只输出JSON，不要其他内容）：
[
  {{"keywords": ["关键词1", "关键词2"], "chapter": 首次出现章节, "description": "解释说明"}},
  ...
]

小说内容：
{content}

请提取历史背景："""

    def _parse_person_response(
        self, response: str, chapters: list[ChapterContent]
    ) -> list[PersonCard]:
        """解析人物提取响应"""
        cards = []

        # 尝试提取JSON
        try:
            # 查找JSON数组
            match = re.search(r"\[[\s\S]*\]", response)
            if match:
                data = json.loads(match.group())
                for item in data:
                    name = item.get("name", "").strip()
                    if not name or len(name) < 2:
                        continue
                    # 清理名字中的特殊字符
                    name = re.sub(r"[^\u4e00-\u9fff]", "", name)
                    if len(name) < 2:
                        continue

                    chapter = item.get("chapter", chapters[0].chapter_idx)
                    description = item.get("description", "").strip()

                    cards.append(
                        PersonCard(
                            canonical_name=name,
                            first_chapter_idx=chapter,
                            summary=description,
                        )
                    )
        except Exception as e:
            print(f"    解析人物响应失败: {e}")

        return cards

    def _parse_history_response(
        self, response: str, default_chapter: int
    ) -> list[HistoryCard]:
        """解析历史背景提取响应"""
        cards = []

        try:
            match = re.search(r"\[[\s\S]*\]", response)
            if match:
                data = json.loads(match.group())
                for item in data:
                    keywords = item.get("keywords", [])
                    if not keywords:
                        continue
                    # 清理关键词
                    keywords = [
                        re.sub(r"[^\u4e00-\u9fff]", "", kw).strip() for kw in keywords
                    ]
                    keywords = [kw for kw in keywords if kw]

                    if not keywords:
                        continue

                    chapter = item.get("chapter", default_chapter)
                    description = item.get("description", "").strip()

                    cards.append(
                        HistoryCard(
                            keywords=keywords,
                            min_chapter_idx=chapter,
                            summary=description,
                        )
                    )
        except Exception as e:
            print(f"    解析历史背景响应失败: {e}")

        return cards


def load_chapters(
    source: Path, start_chapter: int = 1, end_chapter: int = 100
) -> list[ChapterContent]:
    """加载章节内容"""
    text = source.read_text(encoding="utf-8", errors="ignore")
    novel = parse_novel_text(text, title=source.stem)

    chapters = []
    for ch in novel.chapters:
        if start_chapter <= ch.chapter_idx <= end_chapter:
            chapters.append(
                ChapterContent(
                    chapter_idx=ch.chapter_idx,
                    chapter_title=ch.title or f"第{ch.chapter_idx}章",
                    content=ch.content,
                )
            )

    return chapters


async def run_person_extraction(
    source: Path,
    output: Path,
    start_chapter: int,
    end_chapter: int,
    concurrency: int,
    batch_size: int,
):
    """运行人物提取"""
    print(f"\n{'=' * 60}")
    print("批量提取人物卡片")
    print(f"{'=' * 60}")
    print(f"源文件: {source}")
    print(f"章节范围: {start_chapter}-{end_chapter}")
    print(f"并发数: {concurrency}")
    print(f"批次大小: {batch_size}")

    # 加载配置
    settings = Settings.from_env()

    # 创建客户端
    client = AsyncVolcengineClient(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        concurrency=concurrency,
    )

    # 加载章节
    print(f"\n加载章节 {start_chapter}-{end_chapter}...")
    chapters = load_chapters(source, start_chapter, end_chapter)
    print(f"共加载 {len(chapters)} 章")

    # 分析
    analyzer = BatchAnalyzer(client)
    cards = await analyzer.extract_person_cards(chapters, batch_size=batch_size)

    # 保存
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for card in cards:
            f.write(
                json.dumps(
                    {
                        "canonical_name": card.canonical_name,
                        "first_chapter_idx": card.first_chapter_idx,
                        "summary": card.summary,
                        "notes": f"auto-extracted from chapters {start_chapter}-{end_chapter}",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"\n提取完成! 共 {len(cards)} 个人物")
    print(f"结果保存至: {output}")

    return cards


async def run_history_extraction(
    source: Path,
    output: Path,
    start_chapter: int,
    end_chapter: int,
    concurrency: int,
    batch_size: int,
):
    """运行历史背景提取"""
    print(f"\n{'=' * 60}")
    print("批量提取历史背景卡片")
    print(f"{'=' * 60}")

    settings = Settings.from_env()

    client = AsyncVolcengineClient(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        concurrency=concurrency,
    )

    print(f"\n加载章节 {start_chapter}-{end_chapter}...")
    chapters = load_chapters(source, start_chapter, end_chapter)
    print(f"共加载 {len(chapters)} 章")

    analyzer = BatchAnalyzer(client)
    cards = await analyzer.extract_history_cards(chapters, batch_size=batch_size)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        for card in cards:
            f.write(
                json.dumps(
                    {
                        "keywords": card.keywords,
                        "min_chapter_idx": card.min_chapter_idx,
                        "summary": card.summary,
                        "notes": f"auto-extracted from chapters {start_chapter}-{end_chapter}",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"\n提取完成! 共 {len(cards)} 个历史背景")
    print(f"结果保存至: {output}")

    return cards


def main():
    parser = argparse.ArgumentParser(description="批量LLM分析工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 人物提取子命令
    person_parser = subparsers.add_parser("person", help="提取人物卡片")
    person_parser.add_argument("--source", required=True, help="小说源文件路径")
    person_parser.add_argument("--output", required=True, help="输出JSONL文件路径")
    person_parser.add_argument("--start-chapter", type=int, default=1, help="起始章节")
    person_parser.add_argument("--end-chapter", type=int, default=100, help="结束章节")
    person_parser.add_argument("--concurrency", type=int, default=100, help="并发数")
    person_parser.add_argument("--batch-size", type=int, default=10, help="每批章节数")

    # 历史背景提取子命令
    history_parser = subparsers.add_parser("history", help="提取历史背景卡片")
    history_parser.add_argument("--source", required=True, help="小说源文件路径")
    history_parser.add_argument("--output", required=True, help="输出JSONL文件路径")
    history_parser.add_argument("--start-chapter", type=int, default=1, help="起始章节")
    history_parser.add_argument("--end-chapter", type=int, default=100, help="结束章节")
    history_parser.add_argument("--concurrency", type=int, default=100, help="并发数")
    history_parser.add_argument("--batch-size", type=int, default=10, help="每批章节数")

    args = parser.parse_args()

    if args.command == "person":
        asyncio.run(
            run_person_extraction(
                source=Path(args.source),
                output=Path(args.output),
                start_chapter=args.start_chapter,
                end_chapter=args.end_chapter,
                concurrency=args.concurrency,
                batch_size=args.batch_size,
            )
        )
    elif args.command == "history":
        asyncio.run(
            run_history_extraction(
                source=Path(args.source),
                output=Path(args.output),
                start_chapter=args.start_chapter,
                end_chapter=args.end_chapter,
                concurrency=args.concurrency,
                batch_size=args.batch_size,
            )
        )


if __name__ == "__main__":
    main()
