#!/usr/bin/env python3
"""
High-concurrency LLM Batch Extractor
Supports person extraction, history extraction, and refinement.
"""

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

import aiohttp

from app.config import Settings
from app.ingestion.chapter_parser import parse_novel_text


async def fetch_completion(
    session: aiohttp.ClientSession,
    prompt: str,
    settings: Settings,
    semaphore: asyncio.Semaphore,
    max_retries: int = 3,
) -> str:
    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.llm_model_fast or settings.llm_model,
        "messages": [{"role": "user", "content": prompt}],
    }

    for attempt in range(max_retries):
        try:
            async with semaphore:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2**attempt)
    return ""


def load_chapters(source: Path, start_chapter: int, end_chapter: int):
    # Check if source is the raw text file or the ingested index
    if source.suffix == ".txt":
        text = source.read_text(encoding="utf-8", errors="ignore")
        novel = parse_novel_text(text, title=source.stem)

        chapters = []
        for i, ch in enumerate(novel.chapters):
            global_idx = i + 1
            if start_chapter <= global_idx <= end_chapter:
                chapters.append(
                    {
                        "global_idx": global_idx,
                        "chapter_idx": ch.chapter_idx,
                        "title": ch.title or f"第{ch.chapter_idx}章",
                        "content": ch.content[:2000],
                    }
                )
        return chapters
    else:
        # Load from ingested index file
        with open(source, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        # Group chunks by chapter
        chapter_content = {}
        for chunk in index_data:
            chapter_idx = chunk["metadata"]["chapter_idx"]
            if start_chapter <= chapter_idx <= end_chapter:
                if chapter_idx not in chapter_content:
                    chapter_content[chapter_idx] = {
                        "global_idx": chapter_idx,
                        "chapter_idx": chapter_idx,
                        "title": chunk["metadata"]["chapter_title"],
                        "content": "",
                    }
                chapter_content[chapter_idx]["content"] += chunk["document"]

        # Take first 2000 characters of each chapter
        chapters = []
        for idx in sorted(chapter_content.keys()):
            chapter = chapter_content[idx]
            chapter["content"] = chapter["content"][:2000]
            chapters.append(chapter)

        return chapters


async def process_chapter_person(
    session: aiohttp.ClientSession,
    chapter: dict,
    settings: Settings,
    semaphore: asyncio.Semaphore,
    output_file: Path,
    progress_file: Path,
):
    prompt = (
        "从以下小说片段中提取人物姓名和简介，必须输出严格的JSON数组格式，例如：\n"
        '[{"name": "姓名", "chapter": '
        + str(chapter["global_idx"])
        + ', "description": "描述", "aliases": ["别名1"]}]\n'
        "如果没有人物，请输出空数组 []。\n"
        "内容片段：\n" + chapter["content"]
    )

    try:
        response_text = await fetch_completion(session, prompt, settings, semaphore)
        match = re.search(r"\[[\s\S]*\]", response_text)
        cards = []
        if match:
            data = json.loads(match.group())
            if isinstance(data, list):
                for item in data:
                    name = item.get("name", "").strip()
                    if name:
                        cards.append(
                            {
                                "canonical_name": name,
                                "first_chapter_idx": item.get(
                                    "chapter", chapter["global_idx"]
                                ),
                                "summary": item.get("description", ""),
                                "aliases": item.get("aliases", []),
                                "notes": f"seed-extracted from chapter {chapter['global_idx']}",
                                "evidence_chapters": [chapter["global_idx"]],
                            }
                        )

        if cards:
            with open(output_file, "a", encoding="utf-8") as f:
                for card in cards:
                    f.write(json.dumps(card, ensure_ascii=False) + "\n")

        with open(progress_file, "a", encoding="utf-8") as f:
            f.write(f"{chapter['global_idx']}\n")

        return len(cards), None
    except Exception as e:
        return 0, f"Chapter {chapter['global_idx']} failed: {str(e)}"


async def process_chapter_history(
    session: aiohttp.ClientSession,
    chapter: dict,
    settings: Settings,
    semaphore: asyncio.Semaphore,
    output_file: Path,
    progress_file: Path,
):
    prompt = (
        "从以下小说片段中提取历史背景、专有名词、官职、地名等，必须输出严格的JSON数组格式，例如：\n"
        '[{"keywords": ["关键词1", "关键词2"], "chapter": '
        + str(chapter["global_idx"])
        + ', "description": "解释"}]\n'
        "如果没有合适的，请输出空数组 []。\n"
        "内容片段：\n" + chapter["content"]
    )

    try:
        response_text = await fetch_completion(session, prompt, settings, semaphore)
        match = re.search(r"\[[\s\S]*\]", response_text)
        cards = []
        if match:
            data = json.loads(match.group())
            if isinstance(data, list):
                for item in data:
                    keywords = item.get("keywords", [])
                    if keywords and isinstance(keywords, list):
                        cards.append(
                            {
                                "keywords": keywords,
                                "min_chapter_idx": item.get(
                                    "chapter", chapter["global_idx"]
                                ),
                                "summary": item.get("description", ""),
                                "notes": f"seed-extracted from chapter {chapter['global_idx']}",
                                "evidence_chapters": [chapter["global_idx"]],
                            }
                        )

        if cards:
            with open(output_file, "a", encoding="utf-8") as f:
                for card in cards:
                    f.write(json.dumps(card, ensure_ascii=False) + "\n")

        with open(progress_file, "a", encoding="utf-8") as f:
            f.write(f"{chapter['global_idx']}\n")

        return len(cards), None
    except Exception as e:
        return 0, f"Chapter {chapter['global_idx']} failed: {str(e)}"


async def process_refine_item(
    session: aiohttp.ClientSession,
    item: dict,
    settings: Settings,
    semaphore: asyncio.Semaphore,
    output_file: Path,
    progress_file: Path,
    item_idx: int,
):
    summary = item.get("summary", "")
    if not summary:
        with open(progress_file, "a", encoding="utf-8") as f:
            f.write(f"{item_idx}\n")
        return 0, None

    prompt = (
        "请润色以下人物/历史背景的简介，要求客观、准确、精炼，直接输出润色后的文本，不要包含任何多余的解释或开头语。\n"
        f"原简介：{summary}"
    )

    try:
        refined_summary = await fetch_completion(session, prompt, settings, semaphore)
        item["summary"] = refined_summary.strip()
        item["notes"] = "curated by LLM refinement"

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

        with open(progress_file, "a", encoding="utf-8") as f:
            f.write(f"{item_idx}\n")

        return 1, None
    except Exception as e:
        return 0, f"Item {item_idx} failed: {str(e)}"


async def cmd_extract(args, mode: str):
    settings = Settings.from_env()
    source_path = Path(args.source)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = (
        output_dir / f"{mode}_{args.start_chapter}_{args.end_chapter}.seed.jsonl"
    )
    progress_file = (
        output_dir / f"{mode}_{args.start_chapter}_{args.end_chapter}.progress"
    )

    processed = set()
    if progress_file.exists():
        with open(progress_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    processed.add(int(line))

    print(
        f"Loading chapters {args.start_chapter}-{args.end_chapter} from {source_path}..."
    )
    chapters = load_chapters(source_path, args.start_chapter, args.end_chapter)

    pending_chapters = [ch for ch in chapters if ch["global_idx"] not in processed]

    print(
        f"Total chapters to process: {len(pending_chapters)} "
        f"(Already processed: {len(processed)}, Concurrency: {args.workers})"
    )

    if not pending_chapters:
        print("All chapters already processed!")
        return

    semaphore = asyncio.Semaphore(args.workers)

    start_time = time.time()
    total_extracted = 0
    failed_chapters = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for ch in pending_chapters:
            if mode == "person":
                coro = process_chapter_person(
                    session, ch, settings, semaphore, output_file, progress_file
                )
            else:
                coro = process_chapter_history(
                    session, ch, settings, semaphore, output_file, progress_file
                )
            tasks.append(asyncio.create_task(coro))

        completed = 0
        for task in asyncio.as_completed(tasks):
            count, err = await task
            completed += 1
            if err:
                failed_chapters.append(err)
            else:
                total_extracted += count

            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            sys.stdout.write(
                f"\rProgress: {completed}/{len(pending_chapters)} | "
                f"Extracted: {total_extracted} | Failed: {len(failed_chapters)} | {rate:.1f} it/s"
            )
            sys.stdout.flush()

    print(f"\nCompleted in {time.time() - start_time:.1f}s")
    if failed_chapters:
        print("Failed chapters:")
        for err in failed_chapters:
            print(f"  {err}")

    print(f"Saved to {output_file}")


async def cmd_refine(args):
    settings = Settings.from_env()
    input_file = Path(args.input)
    output_file = Path(args.output)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    progress_file = output_file.with_suffix(".progress")

    processed = set()
    if progress_file.exists():
        with open(progress_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    processed.add(int(line))

    items = []
    with open(input_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.strip():
                items.append((i, json.loads(line)))

    pending_items = [item for item in items if item[0] not in processed]

    print(
        f"Total items to refine: {len(pending_items)} "
        f"(Already processed: {len(processed)}, Concurrency: {args.workers})"
    )

    if not pending_items:
        print("All items already refined!")
        return

    semaphore = asyncio.Semaphore(args.workers)

    start_time = time.time()
    total_refined = 0
    failed_items = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, item in pending_items:
            coro = process_refine_item(
                session, item, settings, semaphore, output_file, progress_file, idx
            )
            tasks.append(asyncio.create_task(coro))

        completed = 0
        for task in asyncio.as_completed(tasks):
            count, err = await task
            completed += 1
            if err:
                failed_items.append(err)
            else:
                total_refined += count

            elapsed = time.time() - start_time
            rate = completed / elapsed if elapsed > 0 else 0
            sys.stdout.write(
                f"\rProgress: {completed}/{len(pending_items)} | "
                f"Refined: {total_refined} | Failed: {len(failed_items)} | {rate:.1f} it/s"
            )
            sys.stdout.flush()

    print(f"\nCompleted in {time.time() - start_time:.1f}s")
    if failed_items:
        print("Failed items:")
        for err in failed_items:
            print(f"  {err}")

    print(f"Saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="High-concurrency LLM Batch Extractor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_person = subparsers.add_parser("person", help="Batch extract character cards")
    p_person.add_argument("--source", required=True, help="Path to novel text")
    p_person.add_argument("--output-dir", required=True, help="Output directory")
    p_person.add_argument("--start-chapter", type=int, default=1)
    p_person.add_argument("--end-chapter", type=int, default=200)
    p_person.add_argument("--workers", type=int, default=50, help="Concurrency limit")

    p_history = subparsers.add_parser("history", help="Batch extract history cards")
    p_history.add_argument("--source", required=True, help="Path to novel text")
    p_history.add_argument("--output-dir", required=True, help="Output directory")
    p_history.add_argument("--start-chapter", type=int, default=1)
    p_history.add_argument("--end-chapter", type=int, default=200)
    p_history.add_argument("--workers", type=int, default=50, help="Concurrency limit")

    # Refine parser
    p_refine = subparsers.add_parser(
        "refine", help="Refine seed results to curated quality"
    )
    p_refine.add_argument("--input", required=True, help="Path to seed JSONL")
    p_refine.add_argument(
        "--output", required=True, help="Path to refined output JSONL"
    )
    p_refine.add_argument("--workers", type=int, default=50, help="Concurrency limit")

    args = parser.parse_args()

    if args.command in ("person", "history"):
        asyncio.run(cmd_extract(args, args.command))
    elif args.command == "refine":
        asyncio.run(cmd_refine(args))


if __name__ == "__main__":
    main()
