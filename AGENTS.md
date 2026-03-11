# Repository Guidelines

## Project Structure & Module Organization

- `app/`: core Python code.
  - `api/`: CLI entrypoints (`ingest`, `ask`, `bootstrap-seed`)
  - `ingestion/`: chapter parsing and chunking
  - `retrieval/`: alias resolution, spoiler gating, local index
  - `knowledge/`: character/history card loaders
  - `llm/`: Volcengine Ark client
- `tests/`: pytest suite for retrieval, CLI flow, config, and regressions.
- `data/curated/`: trusted checked-in CSV/JSONL knowledge files.
- `data/bootstrap/`: generated seed drafts; useful, but noisier than curated data.
- `data/indexes/`: local generated indexes; do not commit.
- `docs/`: maintainer notes such as `skills-playbook.md`.

## Build, Test, and Development Commands

- `pytest tests -v`: run the full test suite.
- `python -m app.api.cli ingest --source "/path/to/book.txt" --index-root ./data/indexes --collection-name mybook`: build a local index.
- `python -m app.api.cli bootstrap-seed --source "/path/to/book.txt" --output-dir ./data/bootstrap/mybook`: generate alias/card drafts.
- `python -m app.api.cli ask --question "玉昆是谁" --chapter-idx 120 --index-root ./data/indexes --collection-name mybook`: run a spoiler-safe query.

## Coding Style & Naming Conventions

- Use Python 3.12+ with 4-space indentation.
- Prefer small typed functions and straightforward control flow.
- Use `snake_case` for functions, modules, and test names; `PascalCase` for classes.
- Keep data files explicit: `*.curated.csv`, `*.curated.jsonl`, `*.seed.csv`, `*.seed.jsonl`.
- Avoid hard-coded absolute paths; derive paths from the project root or test temp dirs.

## Testing Guidelines

- Framework: `pytest`.
- Add or update tests for every behavior change, especially retrieval, alias mapping, and spoiler filtering.
- Test files follow `tests/test_<area>.py`; test names should describe behavior, e.g. `test_answer_question_prefers_subject_term_over_generic_question_suffix`.
- Keep CI-safe tests portable: no `/root/...`, no local-only permissions assumptions.

## Commit & Pull Request Guidelines

- Follow the existing commit style: `<type>: <imperative summary>`, for example `feat: expand early novel curated knowledge` or `fix: rebuild collections and improve alias prompting`.
- Keep PRs focused. Include:
  - what changed
  - why it changed
  - test evidence (`pytest tests -v`)
  - sample CLI output if behavior changed

## Security & Configuration Tips

- Keep secrets in `.env`; never commit `ARK_API_KEY`.
- Commit curated knowledge, but not generated local indexes.
- Treat spoiler protection as a hard retrieval constraint, not an LLM instruction.
