# AI Handoff

## Repository and Current State

- Repo path: `/root/novel-reading-assistant`
- Public repo: `https://github.com/LouisLau-art/novel-reading-assistant`
- Default branch: `main`
- CI: green on `main` for Python `3.12` and `3.13`
- Current local status before this handoff doc: clean except untracked [`AGENTS.md`](/root/novel-reading-assistant/AGENTS.md)

## Project Goal

Build a spoiler-safe reading assistant for very long novels.

Core constraints:

1. Retrieval must not leak content after the user’s current chapter.
2. Name resolution must handle aliases, courtesy names, nicknames, and titles.
3. Curated knowledge must stay separate from noisy machine-generated seed files.

The example dataset is for 《宰执天下》.

## What Already Works

- Full TXT ingestion and chapter-aware chunking
- Local index-based retrieval with spoiler gating
- Alias resolution before retrieval
- Curated `character cards` and `history cards`
- Optional Volcengine Ark final-answer generation
- GitHub Actions test workflow

Key files:

- [`app/api/cli.py`](/root/novel-reading-assistant/app/api/cli.py)
- [`app/service.py`](/root/novel-reading-assistant/app/service.py)
- [`app/ingestion/chapter_parser.py`](/root/novel-reading-assistant/app/ingestion/chapter_parser.py)
- [`app/retrieval/vector_index.py`](/root/novel-reading-assistant/app/retrieval/vector_index.py)
- [`data/curated/zaizhitianxia/character_aliases.curated.csv`](/root/novel-reading-assistant/data/curated/zaizhitianxia/character_aliases.curated.csv)
- [`data/curated/zaizhitianxia/character_cards.curated.jsonl`](/root/novel-reading-assistant/data/curated/zaizhitianxia/character_cards.curated.jsonl)
- [`data/curated/zaizhitianxia/history_cards.curated.jsonl`](/root/novel-reading-assistant/data/curated/zaizhitianxia/history_cards.curated.jsonl)

## Current Knowledge Coverage

Curated coverage is still early-stage, roughly the first 10 chapters plus the most common early historical/context entities.

Already curated:

- Early characters such as `韩冈`, `韩云娘`, `李癞子`, `黄德用`, `陈举`, `张载`, `韩琦`, `李元昊`, `赵顼`, `王安石`, `司马光`
- Early context such as `表字`, `衙前`, `押司`, `班头`, `西夏`, `民夫`, `关学`, `飞将庙`, `经略安抚使`, `明经`, `乡兵`, `养娘`, `党项`, `秀才`, `机宜`

## Next Best Work

Highest-value next step:

- Extend curated knowledge for chapters `11-20`

Recommended priorities:

1. Military / frontier人物卡: `王舜臣`, `王厚`, `王韶`, `张守约`
2. More边务历史卡: frontier offices, troop organization, campaign geography
3. Better staged cards: one character, multiple summaries by reading phase

## Local Data and Commands

Source novel files currently used in this workspace:

- `/root/Downloads/宰执天下 (cuslaa) (z-library.sk, 1lib.sk, z-lib.sk).txt`
- `/root/Downloads/宰执天下 (cuslaa) (z-library.sk, 1lib.sk, z-lib.sk).epub`

Useful commands:

```bash
cd /root/novel-reading-assistant
pytest tests -v
python -m app.api.cli ingest --source "/root/Downloads/宰执天下 (cuslaa) (z-library.sk, 1lib.sk, z-lib.sk).txt" --index-root ./data/indexes --collection-name zaizhitianxia
python -m app.api.cli ask --question "横渠先生是谁" --chapter-idx 6 --index-root ./data/indexes --collection-name zaizhitianxia --alias-file ./data/curated/zaizhitianxia/character_aliases.curated.csv --character-cards-file ./data/curated/zaizhitianxia/character_cards.curated.jsonl --history-cards-file ./data/curated/zaizhitianxia/history_cards.curated.jsonl
```

## Important Constraints

- Do not commit `.env` or local indexes under `data/indexes/`.
- Do not hard-code `/root/...` paths in code or tests; recent CI fixes removed those.
- Treat spoiler protection as a retrieval filter, not as an LLM instruction.
- Prefer extending curated files over making the model guess.

## Recent Important Commits

- `ac37f16` test: remove hardcoded local paths
- `a958637` build: restrict setuptools package discovery
- `0f29589` docs: package repository for public release
- `8594f73` feat: expand early novel curated knowledge
- `3daddc8` feat: add curated knowledge cards and skills guide
