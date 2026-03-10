[![Tests](https://img.shields.io/github/actions/workflow/status/LouisLau-art/novel-reading-assistant/tests.yml?branch=main&label=tests)](https://github.com/LouisLau-art/novel-reading-assistant/actions/workflows/tests.yml)
[![License](https://img.shields.io/github/license/LouisLau-art/novel-reading-assistant)](./LICENSE)

# Novel Reading Assistant

Spoiler-safe local reading assistant for long novels, built for the very practical problem of reading huge Chinese web novels with too many recurring names, courtesy names, titles, and historical references.

The project already supports:

- full-book local ingestion
- chapter-aware retrieval with hard spoiler gating
- alias resolution for names, courtesy names, nicknames, and titles
- curated `character cards` and `history cards`
- optional final-answer generation through Volcengine Ark models

The current example dataset is based on 《宰执天下》, but the pipeline is generic.

## Why This Exists

Standard RAG is not enough for long serialized novels.

If you only upload a huge TXT or EPUB into a knowledge base, two things break fast:

- spoiler control: retrieval happily pulls later chapters
- entity resolution: the same person is mentioned by name, courtesy name, office title, or nickname

This repository treats both as first-class constraints:

1. **Spoilers are blocked before generation**
   - retrieval is filtered by the current reading progress
2. **Aliases are resolved before retrieval and answer generation**
   - `玉昆 -> 韩冈`
   - `横渠先生 -> 张载`
   - `黄大瘤 -> 黄德用`

## How It Works

```text
full novel text
-> parse volumes and chapters
-> chunk by chapter with metadata
-> build local index
-> ask(question, current_chapter_idx)
-> alias resolution
-> chapter-aware retrieval
-> curated character/history cards
-> spoiler-safe answer
-> optional LLM phrasing
```

## Repository Layout

```text
app/
  api/                 CLI entrypoints
  answering/           answer formatting
  bootstrap/           seed extraction for aliases and character templates
  ingestion/           chapter parsing and chunking
  knowledge/           character/history card loaders
  llm/                 Volcengine Ark client
  progress/            reading-state helpers
  retrieval/           alias resolution, filtering, local index
  storage/             SQLite metadata store

data/
  curated/             high-confidence manually curated data kept in git
  indexes/             local generated indexes, ignored by git

docs/
  skills-playbook.md   recommended skills for maintaining this project

tests/
  regression and behavior tests
```

## Quick Start

### 1. Clone

```bash
git clone git@github.com:LouisLau-art/novel-reading-assistant.git
cd novel-reading-assistant
```

### 2. Run Tests

```bash
pytest tests -v
```

### 3. Ingest a Full TXT Novel

```bash
python -m app.api.cli ingest \
  --source "/path/to/novel.txt" \
  --index-root ./data/indexes \
  --collection-name zaizhitianxia
```

This builds a local chapter-aware index from the full novel text.

### 4. Ask a Spoiler-Safe Question

```bash
python -m app.api.cli ask \
  --question "玉昆是谁" \
  --chapter-idx 120 \
  --index-root ./data/indexes \
  --collection-name zaizhitianxia
```

The answer is constrained to chapters `<= 120`.

## Recommended Workflow

This repository works best as a layered workflow rather than a single “upload file and pray” knowledge base.

### Step 1: Ingest the full book

Use `ingest` on the whole TXT. This gives you global coverage immediately.

### Step 2: Bootstrap candidate aliases and cards

```bash
python -m app.api.cli bootstrap-seed \
  --source "/path/to/novel.txt" \
  --output-dir ./data/bootstrap/zaizhitianxia
```

This generates noisy but useful first-pass files such as:

- `character_aliases.seed.csv`
- `character_cards.seed.jsonl`

These are drafts, not trusted ground truth.

### Step 3: Build a curated layer

The real quality jump comes from the curated files:

- `data/curated/<book>/character_aliases.curated.csv`
- `data/curated/<book>/character_cards.curated.jsonl`
- `data/curated/<book>/history_cards.curated.jsonl`

These files are the high-confidence layer that should be kept in git.

### Step 4: Ask with curated knowledge

```bash
python -m app.api.cli ask \
  --question "横渠先生是谁" \
  --chapter-idx 6 \
  --index-root ./data/indexes \
  --collection-name zaizhitianxia \
  --alias-file ./data/curated/zaizhitianxia/character_aliases.curated.csv \
  --character-cards-file ./data/curated/zaizhitianxia/character_cards.curated.jsonl \
  --history-cards-file ./data/curated/zaizhitianxia/history_cards.curated.jsonl
```

## File Formats

### Alias CSV

```csv
alias,canonical_name,alias_type
玉昆,韩冈,courtesy_name
横渠先生,张载,honorific
黄大瘤,黄德用,nickname
```

### Character Cards JSONL

```json
{"canonical_name":"韩冈","first_chapter_idx":1,"summary":"韩冈是故事前期的核心视角人物。","notes":"curated from chapters 1-3","evidence_chapters":[1,2,3]}
```

### History Cards JSONL

```json
{"keywords":["表字","玉昆"],"min_chapter_idx":2,"summary":"表字是古人成年后的正式社交称呼。","notes":"curated from chapter 2","evidence_chapters":[2]}
```

## Optional Volcengine Ark Integration

Retrieval and spoiler filtering stay local. The LLM is only used for the final phrasing step.

Set local environment variables:

```bash
export ARK_API_KEY="replace-with-a-new-key"
export ARK_MODEL="doubao-seed-1-8-251228"
export ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
```

Then ask with `--use-llm`:

```bash
python -m app.api.cli ask \
  --question "王安石是谁" \
  --chapter-idx 10 \
  --index-root ./data/indexes \
  --collection-name zaizhitianxia \
  --character-cards-file ./data/curated/zaizhitianxia/character_cards.curated.jsonl \
  --history-cards-file ./data/curated/zaizhitianxia/history_cards.curated.jsonl \
  --use-llm
```

## What Is Already Solved

- full novel ingestion from TXT
- spoiler-safe filtering by chapter order
- alias expansion inside natural questions
- curated early-stage character and history knowledge
- regression coverage for common failure modes

## What Is Not Finished Yet

- automatic WeRead progress sync
- richer multi-stage character cards by reading phase
- better retrieval than the current local lightweight scorer
- larger curated coverage for later chapters

## Why This Feels Slow, and What Scales

There are two different jobs here:

1. **Candidate generation**
   - This can be heavily parallelized.
   - Using many concurrent model calls or workers can dramatically speed up seed extraction, chunk labeling, or draft card generation.
2. **Trusted curated knowledge**
   - This is slower because it needs verification.
   - For spoiler-safe reading assistants, the expensive part is not raw throughput. It is avoiding wrong aliases, mixed identities, and accidental future leakage.

So yes, massive parallel LLM extraction can speed up the draft stage a lot. It does **not** remove the need for a curated verification layer if you want reliable no-spoiler answers.

## License

MIT. See [LICENSE](./LICENSE).
