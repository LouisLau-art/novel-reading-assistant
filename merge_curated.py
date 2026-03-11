#!/usr/bin/env python3
"""
Merge refined seed results into curated knowledge base.
Handles deduplication by canonical_name for person cards and keywords for history cards.
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict


def merge_person_cards(curated_path: Path, new_path: Path, output_path: Path) -> int:
    """Merge person cards, deduplicating by canonical_name."""
    existing_cards = {}
    if curated_path.exists():
        with open(curated_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    card = json.loads(line)
                    canonical_name = card.get("canonical_name")
                    if canonical_name:
                        existing_cards[canonical_name] = card

    new_cards = {}
    with open(new_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                card = json.loads(line)
                canonical_name = card.get("canonical_name")
                if canonical_name:
                    if canonical_name not in new_cards or len(
                        card.get("summary", "")
                    ) > len(new_cards[canonical_name].get("summary", "")):
                        new_cards[canonical_name] = card

    merged_cards = {**existing_cards, **new_cards}

    with open(output_path, "w", encoding="utf-8") as f:
        for card in merged_cards.values():
            f.write(json.dumps(card, ensure_ascii=False) + "\n")

    return len(merged_cards)


def merge_history_cards(curated_path: Path, new_path: Path, output_path: Path) -> int:
    """Merge history cards, deduplicating by keywords tuple."""
    existing_cards = {}
    if curated_path.exists():
        with open(curated_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    card = json.loads(line)
                    keywords = tuple(sorted(card.get("keywords", [])))
                    if keywords:
                        existing_cards[keywords] = card

    new_cards = {}
    with open(new_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                card = json.loads(line)
                keywords = tuple(sorted(card.get("keywords", [])))
                if keywords:
                    if keywords not in new_cards or len(card.get("summary", "")) > len(
                        new_cards[keywords].get("summary", "")
                    ):
                        new_cards[keywords] = card

    merged_cards = {**existing_cards, **new_cards}

    with open(output_path, "w", encoding="utf-8") as f:
        for card in merged_cards.values():
            f.write(json.dumps(card, ensure_ascii=False) + "\n")

    return len(merged_cards)


def main():
    parser = argparse.ArgumentParser(
        description="Merge refined seed results into curated knowledge base"
    )
    parser.add_argument(
        "--curated-dir", required=True, help="Path to curated directory"
    )
    parser.add_argument(
        "--new-dir", required=True, help="Path to new refined files directory"
    )
    parser.add_argument("--start-chapter", type=int, help="Start chapter for range")
    parser.add_argument("--end-chapter", type=int, help="End chapter for range")
    args = parser.parse_args()

    curated_dir = Path(args.curated_dir)
    new_dir = Path(args.new_dir)

    print("=== Merging Person Cards ===")
    person_curated = curated_dir / "character_cards.curated.jsonl"
    # Find all person files in new_dir
    person_files = list(new_dir.glob("person_*.curated.jsonl"))
    if person_files:
        # If multiple files, merge all into one first
        if len(person_files) > 1:
            combined_person = {}
            for file in person_files:
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            card = json.loads(line)
                            canonical_name = card.get("canonical_name")
                            if canonical_name:
                                if canonical_name not in combined_person or len(
                                    card.get("summary", "")
                                ) > len(
                                    combined_person[canonical_name].get("summary", "")
                                ):
                                    combined_person[canonical_name] = card

            # Write combined to a temporary file
            temp_file = new_dir / "combined_person.curated.jsonl"
            with open(temp_file, "w", encoding="utf-8") as f:
                for card in combined_person.values():
                    f.write(json.dumps(card, ensure_ascii=False) + "\n")
            person_count = merge_person_cards(person_curated, temp_file, person_curated)
            temp_file.unlink()
        else:
            person_count = merge_person_cards(
                person_curated, person_files[0], person_curated
            )
        print(f"✓ Merged {person_count} person cards")
    else:
        print("✗ No new person cards found")

    print("\n=== Merging History Cards ===")
    history_curated = curated_dir / "history_cards.curated.jsonl"
    # Find all history files in new_dir
    history_files = list(new_dir.glob("history_*.curated.jsonl"))
    if history_files:
        # If multiple files, merge all into one first
        if len(history_files) > 1:
            combined_history = {}
            for file in history_files:
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            card = json.loads(line)
                            keywords = tuple(sorted(card.get("keywords", [])))
                            if keywords:
                                if keywords not in combined_history or len(
                                    card.get("summary", "")
                                ) > len(combined_history[keywords].get("summary", "")):
                                    combined_history[keywords] = card

            # Write combined to a temporary file
            temp_file = new_dir / "combined_history.curated.jsonl"
            with open(temp_file, "w", encoding="utf-8") as f:
                for card in combined_history.values():
                    f.write(json.dumps(card, ensure_ascii=False) + "\n")
            history_count = merge_history_cards(
                history_curated, temp_file, history_curated
            )
            temp_file.unlink()
        else:
            history_count = merge_history_cards(
                history_curated, history_files[0], history_curated
            )
        print(f"✓ Merged {history_count} history cards")
    else:
        print("✗ No new history cards found")

    print("\n✓ Merge complete")


if __name__ == "__main__":
    main()
