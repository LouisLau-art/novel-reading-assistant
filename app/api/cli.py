from __future__ import annotations

import argparse
from pathlib import Path

from app.bootstrap.seed import bootstrap_seed_files
from app.config import Settings
from app.ingestion.pipeline import ingest_txt_novel
from app.knowledge.cards import load_character_cards, load_history_cards
from app.llm.volcengine import VolcengineChatClient
from app.retrieval.alias_resolver import load_alias_map
from app.retrieval.vector_index import LocalVectorIndex
from app.service import ReadingAssistant


def build_request(question: str, chapter_idx: int) -> dict[str, int | str]:
    return {"question": question, "chapter_idx": chapter_idx}


def ingest_source(
    source: Path,
    index_root: Path,
    collection_name: str | None = None,
) -> dict[str, int | str]:
    source_path = Path(source)
    collection = collection_name or source_path.stem
    payload = ingest_txt_novel(source_path)

    index = LocalVectorIndex(index_root)
    index.replace_many(collection, payload["chunks"])

    return {
        "collection_name": collection,
        "book_title": payload["book_title"],
        "chapter_count": len(payload["chapters"]),
        "chunk_count": len(payload["chunks"]),
    }


def answer_question(
    question: str,
    chapter_idx: int,
    index_root: Path,
    collection_name: str,
    alias_map: dict[str, str] | None = None,
    character_cards: dict[str, dict] | None = None,
    history_cards: list[dict] | None = None,
    llm_client: object | None = None,
    n_results: int = 5,
) -> str:
    resolver = ReadingAssistant(alias_map or {}).resolver
    canonical_name = resolver.resolve(question) or question
    query_text = question if canonical_name == question else f"{question} {canonical_name}"

    index = LocalVectorIndex(index_root)
    hits = index.query(
        collection_name,
        query_text,
        n_results=n_results,
        where={"chapter_order": {"$lte": chapter_idx}},
    )
    if not hits:
        hits = index.query(
            collection_name,
            query_text,
            n_results=n_results,
            where={"chapter_idx": {"$lte": chapter_idx}},
        )
    novel_docs = [
        {
            "text": item.get("document", ""),
            "chapter_idx": item.get("metadata", {}).get("chapter_idx", 0),
            "chapter_order": item.get("metadata", {}).get("chapter_order", 0),
            "chapter_title": item.get("metadata", {}).get("chapter_title", "未知章节"),
        }
        for item in hits
    ]
    assistant = ReadingAssistant(alias_map or {}, llm_client=llm_client)
    return assistant.answer(
        question=question,
        current_chapter_idx=chapter_idx,
        novel_docs=novel_docs,
        character_cards=character_cards or {},
        history_cards=history_cards or [],
    )


def build_llm_client(model_override: str | None = None) -> VolcengineChatClient:
    settings = Settings.from_env()
    model = model_override or settings.llm_model
    if not settings.llm_api_key:
        raise RuntimeError("ARK_API_KEY is required when --use-llm is enabled")
    if not model:
        raise RuntimeError("ARK_MODEL or --llm-model is required when --use-llm is enabled")
    return VolcengineChatClient(
        api_key=settings.llm_api_key,
        model=model,
        base_url=settings.llm_base_url,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("--source", required=True)
    ingest_parser.add_argument("--index-root", required=True)
    ingest_parser.add_argument("--collection-name")

    bootstrap_parser = subparsers.add_parser("bootstrap-seed")
    bootstrap_parser.add_argument("--source", required=True)
    bootstrap_parser.add_argument("--output-dir", required=True)
    bootstrap_parser.add_argument("--max-candidates", type=int, default=200)

    ask_parser = subparsers.add_parser("ask")
    ask_parser.add_argument("--question", required=True)
    ask_parser.add_argument("--chapter-idx", required=True, type=int)
    ask_parser.add_argument("--index-root", required=True)
    ask_parser.add_argument("--collection-name", required=True)
    ask_parser.add_argument("--alias-file")
    ask_parser.add_argument("--character-cards-file")
    ask_parser.add_argument("--history-cards-file")
    ask_parser.add_argument("--use-llm", action="store_true")
    ask_parser.add_argument("--llm-model")

    args = parser.parse_args()
    if args.command == "ingest":
        print(
            ingest_source(
                source=Path(args.source),
                index_root=Path(args.index_root),
                collection_name=args.collection_name,
            )
        )
        return

    if args.command == "bootstrap-seed":
        print(
            bootstrap_seed_files(
                source=Path(args.source),
                output_dir=Path(args.output_dir),
                max_candidates=args.max_candidates,
            )
        )
        return

    print(
        answer_question(
            question=args.question,
            chapter_idx=args.chapter_idx,
            index_root=Path(args.index_root),
            collection_name=args.collection_name,
            alias_map=load_alias_map(Path(args.alias_file)) if args.alias_file else None,
            character_cards=(
                load_character_cards(Path(args.character_cards_file))
                if args.character_cards_file
                else None
            ),
            history_cards=(
                load_history_cards(Path(args.history_cards_file))
                if args.history_cards_file
                else None
            ),
            llm_client=build_llm_client(args.llm_model) if args.use_llm else None,
        )
    )


if __name__ == "__main__":
    main()
