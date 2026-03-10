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
