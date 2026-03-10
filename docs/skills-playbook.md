# Novel Reading Assistant Skills Playbook

This project benefits most from a small, repeatable skill set. Use these skills proactively instead of reaching for them ad hoc.

## Core Workflow

- `test-driven-development`
  - Use before changing retrieval, spoiler gating, alias resolution, ingestion, or answer composition.
  - Add the smallest failing test first, then patch code or curated data.
- `systematic-debugging`
  - Use when a result is wrong, missing, or unexpectedly spoilers.
  - Check whether the failure came from parsing, alias resolution, progress filtering, retrieval, or final LLM phrasing.
- `brainstorming`
  - Use before adding a new capability such as WeRead sync, progressive character cards, or multi-stage retrieval.
  - Keep the design small and explicit before implementation.

## Knowledge and RAG

- `rag-implementation`
  - Use when changing chunking, retrieval flow, mixed knowledge sources, or answer grounding.
  - This is the default skill for novel chunks, character cards, and history cards.
- `embedding-strategies`
  - Use when revisiting chunk size, embedding models, reranking, or hybrid retrieval.
  - Reach for this only after alias mapping and spoiler gating are already correct.
- `context7`
  - Use when checking current documentation for LangChain, Chroma, Volcengine Ark, MCP servers, or other libraries.
  - Prefer official docs through Context7 before web search.

## Architecture and External Repos

- `senior-architect`
  - Use for data model changes, staged rollout decisions, or any question about where a feature should live.
  - Especially useful when deciding between rule-based logic and agent orchestration.
- `gh-cli`
  - Use when evaluating outside repositories, comparing MCP servers, or checking implementation details in third-party code.

## Project-Specific Guidance

- Keep `seed` data and `curated` data separate.
- Treat spoiler protection as a hard retrieval constraint, not an LLM instruction.
- Prefer adding a small curated card over making the LLM guess.
- When a bug involves missing context, inspect the original novel text before editing summaries.
