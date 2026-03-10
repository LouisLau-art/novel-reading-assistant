# Novel Reading Assistant

Local spoiler-safe reading assistant for long Chinese novels.

## MVP Scope

- chapter-aware text parsing
- alias resolution
- spoiler-safe filtering by chapter index
- structured answer formatting

## Run Tests

```bash
pytest tests -v
```

## Ingest A TXT Novel

```bash
python -m app.api.cli ingest \
  --source "/path/to/novel.txt" \
  --index-root ./data/indexes \
  --collection-name zaizhitianxia
```

## Ask A Spoiler-Safe Question

```bash
python -m app.api.cli ask \
  --question "玉昆是谁" \
  --chapter-idx 120 \
  --index-root ./data/indexes \
  --collection-name zaizhitianxia
```

## Ask With Alias Expansion

Create a CSV file shaped like this:

```csv
alias,canonical_name,alias_type
玉昆,韩冈,courtesy_name
```

Then query with the alias file:

```bash
python -m app.api.cli ask \
  --question "玉昆是谁" \
  --chapter-idx 120 \
  --index-root ./data/indexes \
  --collection-name zaizhitianxia \
  --alias-file ./examples/character_aliases.example.csv
```

## Ask With Character And History Cards

Character cards use JSONL, one record per line:

```json
{"canonical_name":"韩冈","first_chapter_idx":1,"summary":"韩冈，截至第一章前的重要人物。"}
```

History cards also use JSONL:

```json
{"keywords":["韩冈","新法"],"min_chapter_idx":1,"summary":"这里涉及北宋政局与新法讨论。"}
```

You can pass both files to `ask`:

```bash
python -m app.api.cli ask \
  --question "玉昆是谁" \
  --chapter-idx 120 \
  --index-root ./data/indexes \
  --collection-name zaizhitianxia \
  --alias-file ./examples/character_aliases.example.csv \
  --character-cards-file ./examples/character_cards.example.jsonl \
  --history-cards-file ./examples/history_cards.example.jsonl
```

## Enable Volcengine LLM

Set environment variables locally:

```bash
export ARK_API_KEY="replace-with-a-new-key"
export ARK_MODEL="doubao-seed-1-8-251228"
```

Optional override:

```bash
export ARK_BASE_URL="https://ark.cn-beijing.volces.com/api/v3"
```

Then enable LLM for the final answer generation step:

```bash
python -m app.api.cli ask \
  --question "玉昆是谁" \
  --chapter-idx 120 \
  --index-root ./data/indexes \
  --collection-name zaizhitianxia \
  --alias-file ./examples/character_aliases.example.csv \
  --character-cards-file ./examples/character_cards.example.jsonl \
  --history-cards-file ./examples/history_cards.example.jsonl \
  --use-llm
```

The anti-spoiler filter still runs locally before the model call. The LLM only sees already-filtered evidence.
