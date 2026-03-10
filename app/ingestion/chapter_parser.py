from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(slots=True)
class Chapter:
    chapter_idx: int
    title: str
    content: str


_CHAPTER_RE = re.compile(r"^第(?P<idx>[一二三四五六七八九十百千0-9]+)章[ \t]*(?P<title>.*)$")

_CN_NUM_MAP = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def _cn_to_int(value: str) -> int:
    if value.isdigit():
        return int(value)
    total = 0
    current = 0
    units = {"十": 10, "百": 100, "千": 1000}
    for char in value:
        if char in _CN_NUM_MAP:
            current = _CN_NUM_MAP[char]
            continue
        unit = units.get(char)
        if unit is None:
            continue
        if current == 0:
            current = 1
        total += current * unit
        current = 0
    return total + current


def parse_chapters(text: str) -> list[Chapter]:
    chapters: list[Chapter] = []
    current_title: str | None = None
    current_idx: int | None = None
    buffer: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = _CHAPTER_RE.match(line)
        if match:
            if current_idx is not None:
                chapters.append(
                    Chapter(
                        chapter_idx=current_idx,
                        title=current_title or f"第{current_idx}章",
                        content="\n".join(buffer).strip(),
                    )
                )
            current_idx = _cn_to_int(match.group("idx"))
            title_suffix = match.group("title").strip()
            current_title = line if title_suffix else f"第{current_idx}章"
            buffer = []
            continue
        if current_idx is not None:
            buffer.append(raw_line)

    if current_idx is not None:
        chapters.append(
            Chapter(
                chapter_idx=current_idx,
                title=current_title or f"第{current_idx}章",
                content="\n".join(buffer).strip(),
            )
        )
    return chapters
