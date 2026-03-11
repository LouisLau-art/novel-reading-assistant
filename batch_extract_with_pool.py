#!/usr/bin/env python3
"""High-concurrency LLM Batch Extractor with Model Pool."""

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

import aiohttp
from app.llm.model_pool import create_model_pool_from_env


async def fetch_completion(
    session: aiohttp.ClientSession,
    prompt: str,
    model_pool,
    semaphore: asyncio.Semaphore,
) -> str:
    async with semaphore:
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(None, model_pool.chat, prompt)
            return response
        except Exception as e:
            raise e


def load_chapters(source: Path, start_chapter: int, end_chapter: int):
    if source.suffix == ".txt":
        text = source.read_text(encoding="utf-8", errors="ignore")
        from app.ingestion.chapter_parser import parse_novel_text

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
        with open(source, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        chapter_content = {}
        for chunk in index_data:
            global_idx = chunk["metadata"]["chapter_order"]
            if start_chapter <= global_idx <= end_chapter:
                if global_idx not in chapter_content:
                    chapter_content[global_idx] = {
                        "global_idx": global_idx,
                        "chapter_idx": chunk["metadata"]["chapter_idx"],
                        "title": chunk["metadata"]["chapter_title"],
                        "content": "",
                    }
                chapter_content[global_idx]["content"] += chunk["document"]

        chapters = []
        for idx in sorted(chapter_content.keys()):
            chapter = chapter_content[idx]
            chapter["content"] = chapter["content"][:2000]
            chapters.append(chapter)

        return chapters


async def process_chapter_person(
    session: aiohttp.ClientSession,
    chapter: dict,
    model_pool,
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
        response_text = await fetch_completion(session, prompt, model_pool, semaphore)
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
    model_pool,
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
        response_text = await fetch_completion(session, prompt, model_pool, semaphore)
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


async def cmd_extract(args, mode: str):
    model_pool = create_model_pool_from_env()
    print(f"Model Pool Initialized: {len(model_pool.models)} models available")

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
        f"Total chapters to process: {len(pending_chapters)} (Already processed: {len(processed)})"
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
                    session, ch, model_pool, semaphore, output_file, progress_file
                )
            else:
                coro = process_chapter_history(
                    session, ch, model_pool, semaphore, output_file, progress_file
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
        for err in failed_chapters[:10]:
            print(f"  {err}")
        if len(failed_chapters) > 10:
            print(f"  ... and {len(failed_chapters) - 10} more")

    print(f"Saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="High-concurrency LLM Batch Extractor with Model Pool"
    )
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

    args = parser.parse_args()

    if args.command in ("person", "history"):
        asyncio.run(cmd_extract(args, args.command))


if __name__ == "__main__":
    main()
