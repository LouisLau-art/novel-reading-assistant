#!/usr/bin/env python3
"""简化版批量提取 - 测试用"""

import json
import re
import sys
from pathlib import Path

from app.config import Settings
from app.ingestion.chapter_parser import parse_novel_text
from app.llm.volcengine import VolcengineChatClient


def load_chapters(source: Path, start_chapter: int, end_chapter: int):
    text = source.read_text(encoding="utf-8", errors="ignore")
    novel = parse_novel_text(text, title=source.stem)

    chapters = []
    for ch in novel.chapters:
        if start_chapter <= ch.chapter_idx <= end_chapter:
            chapters.append(
                {
                    "idx": ch.chapter_idx,
                    "title": ch.title or f"第{ch.chapter_idx}章",
                    "content": ch.content[:3000],  # 限制内容长度
                }
            )
    return chapters


def build_prompt(chapters):
    content = "\n\n".join(
        [f"第{ch['idx']}章 {ch['title']}:\n{ch['content'][:1500]}" for ch in chapters]
    )

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


def main():
    settings = Settings.from_env()
    client = VolcengineChatClient(
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
    )

    source = Path(
        "/root/Downloads/宰执天下 (cuslaa) (z-library.sk, 1lib.sk, z-lib.sk).txt"
    )
    chapters = load_chapters(source, 11, 15)
    print(f"加载了 {len(chapters)} 章")

    # 分批处理
    batch_size = 2
    all_results = []

    for i in range(0, len(chapters), batch_size):
        batch = chapters[i : i + batch_size]
        print(f"处理章节 {batch[0]['idx']}-{batch[-1]['idx']}...")

        prompt = build_prompt(batch)

        try:
            response = client.chat(prompt)
            print(f"  响应: {response[:200]}...")

            # 解析JSON
            match = re.search(r"\[[\s\S]*\]", response)
            if match:
                data = json.loads(match.group())
                print(f"  提取到 {len(data)} 个人物")
                all_results.extend(data)
        except Exception as e:
            print(f"  错误: {e}")

    print(f"\n总计提取 {len(all_results)} 个人物")

    # 去重
    seen = {}
    unique = []
    for item in all_results:
        name = item.get("name", "").strip()
        if name and name not in seen:
            seen[name] = True
            unique.append(item)

    print(f"去重后 {len(unique)} 个人物")

    # 保存
    output = Path("/tmp/test_person_simple.jsonl")
    with output.open("w", encoding="utf-8") as f:
        for item in unique:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"保存至: {output}")


if __name__ == "__main__":
    main()
