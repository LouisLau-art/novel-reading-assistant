from __future__ import annotations

import argparse


def build_request(question: str, chapter_idx: int) -> dict[str, int | str]:
    return {"question": question, "chapter_idx": chapter_idx}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--chapter-idx", required=True, type=int)
    args = parser.parse_args()
    print(build_request(args.question, args.chapter_idx))


if __name__ == "__main__":
    main()
