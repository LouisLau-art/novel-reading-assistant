from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(slots=True)
class Chapter:
    chapter_idx: int
    global_idx: int
    title: str
    volume_title: str
    content: str


@dataclass(slots=True)
class NovelText:
    title: str
    volume_title: str
    chapters: list[Chapter]


_CHAPTER_RE = re.compile(
    r"^第[ \t]*(?P<idx>[一二三四五六七八九十百千0-9]+)[ \t]*章(?:[ \t]+(?P<title>.*))?$"
)
_VOLUME_RE = re.compile(r"^(?P<volume>.+之卷)(?:[ \t]+(?P<title>.+))?$")

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


def _is_blank(line: str) -> bool:
    return not line.strip()


def _collect_nonblank(lines: list[str], start: int) -> tuple[int | None, str | None]:
    idx = start
    while idx < len(lines):
        line = lines[idx].strip()
        if line:
            return idx, line
        idx += 1
    return None, None


def _parse_volume(line: str, lines: list[str], index: int) -> tuple[str | None, int]:
    stripped = line.strip()
    match = _VOLUME_RE.match(stripped)
    if not match:
        return None, index

    base = match.group("volume")
    title = (match.group("title") or "").strip()
    if title:
        next_idx, next_line = _collect_nonblank(lines, index + 1)
        title_idx, title_line = _collect_nonblank(lines, (next_idx or index) + 1)
        if next_line == base and title_idx is not None and title_line == title:
            return f"{base} {title}".strip(), title_idx
        return f"{base} {title}".strip(), index

    title_idx, title_line = _collect_nonblank(lines, index + 1)
    if title_idx is not None and title_line and not _CHAPTER_RE.match(title_line):
        return f"{base} {title_line}".strip(), title_idx
    return base, index


def _parse_chapter_heading(lines: list[str], index: int) -> tuple[int, str, int] | None:
    stripped = lines[index].strip()
    match = _CHAPTER_RE.match(stripped)
    if not match:
        return None

    chapter_idx = _cn_to_int(match.group("idx"))
    title = (match.group("title") or "").strip()
    if title:
        next_idx, next_line = _collect_nonblank(lines, index + 1)
        title_idx, title_line = _collect_nonblank(lines, (next_idx or index) + 1)
        if (
            next_line == f"第{match.group('idx')}章"
            and title_idx is not None
            and title_line == title
        ):
            return chapter_idx, f"第{match.group('idx')}章 {title}".strip(), title_idx
        return chapter_idx, stripped, index

    next_idx, next_line = _collect_nonblank(lines, index + 1)
    if next_idx is not None and next_line:
        return chapter_idx, f"{stripped} {next_line}".strip(), next_idx
    return chapter_idx, stripped, index


def parse_chapters(text: str, *, default_volume_title: str = "") -> list[Chapter]:
    chapters: list[Chapter] = []
    current_volume_title = default_volume_title
    current_title: str | None = None
    current_idx: int | None = None
    buffer: list[str] = []
    lines = text.splitlines()
    index = 0
    global_counter = 1

    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()
        if not line:
            if current_idx is not None:
                buffer.append(raw_line)
            index += 1
            continue

        volume_title, consumed_idx = _parse_volume(raw_line, lines, index)
        if volume_title is not None:
            current_volume_title = volume_title
            index = consumed_idx + 1
            continue

        chapter_heading = _parse_chapter_heading(lines, index)
        if chapter_heading is not None:
            if current_idx is not None:
                chapters.append(
                    Chapter(
                        chapter_idx=current_idx,
                        global_idx=global_counter,
                        title=current_title or f"第{current_idx}章",
                        volume_title=current_volume_title,
                        content="\n".join(buffer).strip(),
                    )
                )
                global_counter += 1
            current_idx, current_title, consumed_idx = chapter_heading
            buffer = []
            index = consumed_idx + 1
            continue

        if current_idx is not None and line != current_title:
            buffer.append(raw_line)
        index += 1

    if current_idx is not None:
        chapters.append(
            Chapter(
                chapter_idx=current_idx,
                global_idx=global_counter,
                title=current_title or f"第{current_idx}章",
                volume_title=current_volume_title,
                content="\n".join(buffer).strip(),
            )
        )
    return chapters


def parse_novel_text(text: str, title: str = "") -> NovelText:
    chapters = parse_chapters(text)
    volume_title = chapters[0].volume_title if chapters else ""
    return NovelText(title=title, volume_title=volume_title, chapters=chapters)
