from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

from app.ingestion.chapter_parser import parse_novel_text

_COMPOUND_SURNAMES = (
    "欧阳|司马|诸葛|上官|夏侯|司徒|司空|公孙|皇甫|东方|独孤|慕容|长孙|宇文|尉迟"
)
_SINGLE_SURNAMES = (
    "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
    "戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳鲍史唐费廉"
    "岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元顾孟平黄和穆萧尹"
    "姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席"
)
_NAME_PATTERN = rf"(?:{_COMPOUND_SURNAMES})[\u4e00-\u9fff]{{1,2}}|[{_SINGLE_SURNAMES}][\u4e00-\u9fff]{{1,2}}"
_ALIAS_NAME_PATTERN = (
    rf"(?:{_COMPOUND_SURNAMES})[\u4e00-\u9fff]{{1,2}}?|[{_SINGLE_SURNAMES}][\u4e00-\u9fff]{{1,2}}?"
)
_ALIAS_SUFFIX_PATTERN = r"(?:的(?:便是|就是)?|者|也)?(?=$|[^\u4e00-\u9fff])"
_EXPLICIT_ALIAS_RE = re.compile(
    rf"(?P<name>{_ALIAS_NAME_PATTERN})"
    r"[，、]?"
    r"(?:表字|草字|字)"
    r"(?:唤作|叫作|名曰|曰|叫|为)?"
    rf"(?P<alias>[\u4e00-\u9fff]{{2,3}}){_ALIAS_SUFFIX_PATTERN}"
)
_INTRO_STYLE_ALIAS_RE = re.compile(
    r"姓(?P<surname>[\u4e00-\u9fff])名(?P<given>[\u4e00-\u9fff]{1,2})"
    r"(?:[^。！？；\n]{0,12}?)"
    r"(?:表字|草字|字)"
    r"(?:唤作|叫作|名曰|曰|叫|为)?"
    rf"(?P<alias>[\u4e00-\u9fff]{{2,3}}){_ALIAS_SUFFIX_PATTERN}"
)
_SELF_INTRO_ALIAS_RE = re.compile(
    r"姓(?P<surname>[\u4e00-\u9fff])名(?P<given>[\u4e00-\u9fff]{1,2})"
    r"[，、]?"
    r"(?:表字|草字|字)"
    r"(?:唤作|叫作|名曰|曰|叫|为)?"
    rf"(?P<alias>[\u4e00-\u9fff]{{2,3}}){_ALIAS_SUFFIX_PATTERN}"
)
_FULL_NAME_RE = re.compile(rf"^(?:{_NAME_PATTERN})$")
_ALIAS_TAIL_RE = re.compile(
    rf"(?:唤作|叫作|名曰|曰|叫|为)?(?P<alias>[\u4e00-\u9fff]{{2,3}}){_ALIAS_SUFFIX_PATTERN}"
)

_STOP_NAMES = {
    "第一章",
    "第二章",
    "第三章",
    "第四章",
    "第五章",
    "开始",
    "继续",
    "后文",
    "出租车",
    "火流星",
    "时候",
    "时间",
    "平章",
    "秦凤",
    "明白",
    "马上",
    "尤其是",
}
_BOUNDARY_CHARS = set(' \t\r\n"“”‘’()（）[]【】《》,，。；：!?！？、')
_NAME_PREV_HINT_CHARS = set("与和向对同随替帮叫唤问请拜见听朝从给把被令命让到跟经由及")
_NAME_NEXT_HINT_CHARS = set(
    "与和向对同道说问答笑叹曰云来去入出上下来到回转交谈见听想请拜叫唤命令写读念看知"
)
_NAME_TITLE_PREV_CHARS = set("官公君臣师帅相令使郎卿丞监史尉将校士生侯伯")
_BAD_TRAILING_NAME_CHARS = set("的一了也呢吗吧啊么着过上下中里和与同向对将把被给于从之者是")
_DISALLOWED_NAME_SUFFIX_CHARS = set("州军路县府面候间章排才千天况人背")
_ALIAS_INVALID_CHARS = set(
    "的一了么呢吧啊从于向上下来去中里和与及并或被把将让给这那哪谁何也便就再又还很太都所是得着其人"
)
_NAME_BODY_STOP_WORDS = {"相公", "官人", "先生", "官家", "学士", "博士", "卿"}
_NAME_BODY_STOP_CHARS = set("的一了也么呢吧啊着过上下中里和与同向对于从之者是其")
_LEADING_CONNECTOR_CHARS = set("和于与同向对跟由及并")
_ALWAYS_NORMALIZE_SUFFIX_CHARS = set("的一了也在从来去回想看听知笑叹说又不就则本有轻冷微")
_CONDITIONAL_NORMALIZE_SUFFIXES = {
    "问": set("道曰"),
    "说": set("道曰"),
    "笑": set("道曰"),
    "叹": set("道曰"),
    "道": set("：，“\"'"),
}
_CONTEXTUAL_TRAILING_NAME_CHARS = set("看知回来去叹笑说问道又不就在从则本有轻冷微")
_SPILLOVER_BIGRAMS = {
    "说道",
    "问道",
    "笑道",
    "叹道",
    "交谈",
    "出来",
    "进去",
    "上去",
    "下来",
    "看见",
    "听见",
}
_SINGLE_SURNAMES_SET = set(_SINGLE_SURNAMES)
_COMPOUND_SURNAMES_LIST = (
    "欧阳",
    "司马",
    "诸葛",
    "上官",
    "夏侯",
    "司徒",
    "司空",
    "公孙",
    "皇甫",
    "东方",
    "独孤",
    "慕容",
    "长孙",
    "宇文",
    "尉迟",
)
_COMPOUND_SURNAMES_SET = set(_COMPOUND_SURNAMES_LIST)


def bootstrap_seed_files(
    source: Path,
    output_dir: Path,
    max_candidates: int = 200,
) -> dict[str, int | str]:
    source_path = Path(source)
    text = source_path.read_text(encoding="utf-8", errors="ignore")
    novel = parse_novel_text(text, title=source_path.stem)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    alias_rows, alias_names = _extract_alias_rows(novel)
    character_rows = _extract_character_rows(novel, alias_names, max_candidates=max_candidates)

    alias_path = output_root / "character_aliases.seed.csv"
    with alias_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["alias", "canonical_name", "alias_type"])
        writer.writeheader()
        writer.writerows(alias_rows)

    character_path = output_root / "character_cards.seed.jsonl"
    character_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in character_rows)
        + ("\n" if character_rows else ""),
        encoding="utf-8",
    )

    history_path = output_root / "history_cards.seed.jsonl"
    history_path.write_text("", encoding="utf-8")

    return {
        "source": str(source_path),
        "output_dir": str(output_root),
        "alias_count": len(alias_rows),
        "character_count": len(character_rows),
        "history_count": 0,
    }


def _extract_alias_rows(novel) -> tuple[list[dict[str, str]], set[str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    names: set[str] = set()

    for chapter in novel.chapters:
        for canonical_name, alias in _iter_alias_pairs(chapter.content):
            if not _is_valid_name(canonical_name) or not _is_valid_alias(alias):
                continue
            pair = (alias, canonical_name)
            if pair in seen:
                continue
            seen.add(pair)
            names.add(canonical_name)
            rows.append(
                {
                    "alias": alias,
                    "canonical_name": canonical_name,
                    "alias_type": "courtesy_name",
                }
            )
    return rows, names


def _extract_character_rows(novel, alias_names: set[str], max_candidates: int) -> list[dict]:
    counts: Counter[str] = Counter()
    first_seen: dict[str, int] = {}

    for chapter in novel.chapters:
        for name in _iter_name_mentions(chapter.content, alias_names):
            counts[name] += 1
            first_seen.setdefault(name, chapter.chapter_idx)

    candidates = [
        name
        for name, _ in counts.most_common()
        if not _should_skip_prefix_variant(name, counts, alias_names)
    ][:max_candidates]
    for name in sorted(alias_names):
        if name not in candidates:
            candidates.append(name)

    rows: list[dict] = []
    for name in candidates[:max_candidates]:
        rows.append(
            {
                "canonical_name": name,
                "first_chapter_idx": first_seen.get(name, 1),
                "summary": "",
                "notes": "auto-generated seed; fill manually",
                "source_frequency": counts.get(name, 0),
            }
        )
    return rows


def _is_valid_name(name: str) -> bool:
    if not (2 <= len(name) <= 4):
        return False
    if not _matches_name_shape(name):
        return False
    if name in _STOP_NAMES:
        return False
    if name[-1] in _BAD_TRAILING_NAME_CHARS or name[-1] in _DISALLOWED_NAME_SUFFIX_CHARS:
        return False

    body = _name_body(name)
    if not body or body in _NAME_BODY_STOP_WORDS:
        return False
    return not any(char in _NAME_BODY_STOP_CHARS for char in body)


def _is_valid_alias(alias: str) -> bool:
    return (
        2 <= len(alias) <= 3
        and alias not in _STOP_NAMES
        and not any(char in _ALIAS_INVALID_CHARS for char in alias)
    )


def _iter_alias_pairs(text: str):
    for sentence in _iter_sentences(text):
        seen: set[tuple[str, str]] = set()
        for match in _INTRO_STYLE_ALIAS_RE.finditer(sentence):
            pair = (f"{match.group('surname')}{match.group('given')}", match.group("alias"))
            if pair not in seen:
                seen.add(pair)
                yield pair
        for match in _SELF_INTRO_ALIAS_RE.finditer(sentence):
            pair = (f"{match.group('surname')}{match.group('given')}", match.group("alias"))
            if pair not in seen:
                seen.add(pair)
                yield pair
        if "姓" in sentence and "名" in sentence:
            continue
        for pair in _iter_marker_alias_pairs(sentence):
            if pair not in seen:
                seen.add(pair)
                yield pair


def _iter_marker_alias_pairs(sentence: str):
    search_start = 0
    while search_start < len(sentence):
        marker_start, marker = _find_next_alias_marker(sentence, search_start)
        if marker_start < 0:
            return
        canonical_name = _find_name_before_marker(sentence, marker_start)
        if canonical_name:
            alias_match = _ALIAS_TAIL_RE.match(sentence[marker_start + len(marker) :])
            if alias_match is not None:
                yield canonical_name, alias_match.group("alias")
        search_start = marker_start + len(marker)


def _iter_marker_alias_pairs(sentence: str):
    for marker in ("表字", "草字"):
        start = 0
        while True:
            marker_idx = sentence.find(marker, start)
            if marker_idx == -1:
                break
            name_span = _best_name_span_before_marker(sentence, marker_idx)
            alias = _extract_alias_after_marker(sentence, marker_idx + len(marker))
            if name_span and alias:
                yield name_span[1], alias
            start = marker_idx + len(marker)

    for marker_idx, char in enumerate(sentence):
        if char != "字":
            continue
        if marker_idx > 0 and sentence[marker_idx - 1] in {"表", "草"}:
            continue
        name_span = _best_name_span_before_marker(sentence, marker_idx)
        alias = _extract_alias_after_marker(sentence, marker_idx + 1)
        if not name_span or not alias:
            continue
        name_start, canonical_name = name_span
        prev_char = sentence[name_start - 1] if name_start > 0 else ""
        if sentence[marker_idx - 1] not in {"，", "、"} and prev_char not in _BOUNDARY_CHARS:
            continue
        yield canonical_name, alias


def _best_name_span_before_marker(text: str, marker_idx: int) -> tuple[int, str] | None:
    end_idx = marker_idx
    while end_idx > 0 and text[end_idx - 1] in {"，", "、", "【", "（", "("}:
        end_idx -= 1

    for name_length in (4, 3, 2):
        start = end_idx - name_length
        if start < 0:
            continue
        candidate = _normalize_alias_name_candidate(text[start:end_idx])
        if _is_valid_name(candidate):
            adjusted_start = end_idx - len(candidate)
            return adjusted_start, candidate
    return None


def _extract_alias_after_marker(text: str, start_idx: int) -> str | None:
    for alias_length in (3, 2):
        end = start_idx + alias_length
        if end > len(text):
            continue
        alias = text[start_idx:end]
        next_char = text[end] if end < len(text) else ""
        if all(_is_cjk(char) for char in alias) and (next_char in _BOUNDARY_CHARS or not next_char):
            return alias
    return None


def _normalize_alias_name_candidate(name: str) -> str:
    if name.endswith(("表", "草", "字")):
        trimmed = name[:-1]
        if _is_valid_name(trimmed):
            return trimmed
    return name


def _iter_sentences(text: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"[\n。！？；]", text) if segment.strip()]


def _find_next_alias_marker(sentence: str, start: int) -> tuple[int, str]:
    best_index = -1
    best_marker = ""
    for marker in ("表字", "草字", "字"):
        index = sentence.find(marker, start)
        if index == -1:
            continue
        if best_index == -1 or index < best_index or (index == best_index and len(marker) > len(best_marker)):
            best_index = index
            best_marker = marker
    return best_index, best_marker


def _find_name_before_marker(sentence: str, marker_start: int) -> str | None:
    candidate_ends = [marker_start]
    if marker_start > 0 and sentence[marker_start - 1] in "，、":
        candidate_ends.append(marker_start - 1)

    best_name: str | None = None
    best_score = -10
    for end in candidate_ends:
        for length in (4, 3, 2):
            start = end - length
            if start < 0:
                continue
            candidate = sentence[start:end]
            if _FULL_NAME_RE.fullmatch(candidate) is None:
                continue
            if _is_valid_name(candidate):
                score = len(candidate)
                if candidate[-1] in _CONTEXTUAL_TRAILING_NAME_CHARS:
                    score -= 5
                if candidate[-1] + sentence[marker_start : marker_start + 2] in _SPILLOVER_BIGRAMS:
                    score -= 4
                if score > best_score:
                    best_score = score
                    best_name = candidate
    return best_name


def _iter_name_mentions(text: str, alias_names: set[str]):
    for sentence in _iter_sentences(text):
        for name in _iter_sentence_name_mentions(sentence, alias_names):
            yield name


def _iter_sentence_name_mentions(sentence: str, alias_names: set[str]):
    index = 0
    while index < len(sentence):
        candidates = _candidate_names_at(sentence, index)
        if not candidates:
            index += 1
            continue

        scored = [
            (
                _score_name_candidate(
                    sentence,
                    index,
                    candidate,
                    alias_names,
                    has_longer_candidate=any(
                        len(other) > len(candidate)
                        and _is_valid_name(other)
                        and not _looks_like_spillover(sentence, index, other)
                        for other in candidates
                    ),
                ),
                candidate,
            )
            for candidate in candidates
        ]
        best_score, best_candidate = max(scored, key=lambda item: (item[0], len(item[1])))
        if best_score >= 3 or (len(best_candidate) >= 3 and best_score >= 2):
            normalized = _normalize_name_candidate(sentence, index, best_candidate)
            if _is_valid_name(normalized):
                yield normalized
            index += len(best_candidate)
            continue

        index += 1


def _candidate_names_at(text: str, index: int) -> list[str]:
    candidates: list[str] = []
    for compound_surname in _COMPOUND_SURNAMES_LIST:
        if not text.startswith(compound_surname, index):
            continue
        start = index + len(compound_surname)
        for given_length in (2, 1):
            end = start + given_length
            if end <= len(text) and all(_is_cjk(char) for char in text[start:end]):
                candidates.append(text[index:end])
        return candidates

    if text[index] not in _SINGLE_SURNAMES_SET:
        return candidates

    for given_length in (2, 1):
        end = index + 1 + given_length
        if end <= len(text) and all(_is_cjk(char) for char in text[index + 1 : end]):
            candidates.append(text[index:end])
    return candidates


def _score_name_candidate(
    text: str,
    start: int,
    candidate: str,
    alias_names: set[str],
    *,
    has_longer_candidate: bool,
) -> int:
    if not _is_valid_name(candidate):
        return -10

    end = start + len(candidate)
    prev_char = text[start - 1] if start > 0 else ""
    next_char = text[end] if end < len(text) else ""
    next_next_char = text[end + 1] if end + 1 < len(text) else ""
    score = 0

    if candidate in alias_names:
        score += 3
    if prev_char in _BOUNDARY_CHARS or not prev_char:
        score += 1
    if next_char in _BOUNDARY_CHARS or not next_char:
        score += 1
    if prev_char in _NAME_PREV_HINT_CHARS:
        score += 1
    if prev_char in _NAME_TITLE_PREV_CHARS:
        score += 2
    if len(candidate) >= 3:
        score += 1
    if not has_longer_candidate and next_char in _NAME_NEXT_HINT_CHARS:
        score += 2
    if (
        len(candidate) == 2
        and has_longer_candidate
        and next_char in _NAME_NEXT_HINT_CHARS
        and (next_next_char in _NAME_NEXT_HINT_CHARS or next_next_char in _BOUNDARY_CHARS)
    ):
        score += 3
    if candidate[-1] in _BAD_TRAILING_NAME_CHARS:
        score -= 3
    if (
        len(candidate) >= 3
        and candidate[-1] in _CONTEXTUAL_TRAILING_NAME_CHARS
        and (next_char in _NAME_NEXT_HINT_CHARS or next_char in _BOUNDARY_CHARS)
    ):
        score -= 4
    if candidate[-1] + next_char in _SPILLOVER_BIGRAMS:
        score -= 4
    return score


def _normalize_name_candidate(text: str, start: int, candidate: str) -> str:
    if candidate[0] in _LEADING_CONNECTOR_CHARS and _is_valid_name(candidate[1:]):
        return candidate[1:]
    if len(candidate) <= 2:
        return candidate

    end = start + len(candidate)
    next_char = text[end] if end < len(text) else ""
    suffix = candidate[-1]
    if suffix in _ALWAYS_NORMALIZE_SUFFIX_CHARS:
        return candidate[:-1]
    if suffix in _CONDITIONAL_NORMALIZE_SUFFIXES and next_char in _CONDITIONAL_NORMALIZE_SUFFIXES[suffix]:
        return candidate[:-1]
    return candidate


def _name_body(name: str) -> str:
    if name[:2] in _COMPOUND_SURNAMES_SET:
        return name[2:]
    return name[1:]


def _is_cjk(value: str) -> bool:
    return bool(value) and "\u4e00" <= value <= "\u9fff"


def _matches_name_shape(name: str) -> bool:
    if not all(_is_cjk(char) for char in name):
        return False
    if name[:2] in _COMPOUND_SURNAMES_SET:
        return 3 <= len(name) <= 4
    return name[0] in _SINGLE_SURNAMES_SET and 2 <= len(name) <= 3


def _looks_like_spillover(text: str, start: int, candidate: str) -> bool:
    end = start + len(candidate)
    next_char = text[end] if end < len(text) else ""
    return candidate[-1] + next_char in _SPILLOVER_BIGRAMS


def _should_skip_prefix_variant(name: str, counts: Counter[str], alias_names: set[str]) -> bool:
    if name in alias_names or len(name) != 2:
        return False

    for other_name, other_count in counts.items():
        if len(other_name) != 3:
            continue
        if other_name.startswith(name) and other_count >= counts[name] * 2:
            return True
    return False
