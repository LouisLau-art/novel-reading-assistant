from __future__ import annotations

import csv
from pathlib import Path


class AliasResolver:
    def __init__(self, alias_map: dict[str, str]) -> None:
        self.alias_map = alias_map

    def resolve(self, name: str) -> str | None:
        if name in self.alias_map:
            return self.alias_map[name]

        for alias in sorted(self.alias_map, key=len, reverse=True):
            if alias and alias in name:
                return self.alias_map[alias]
        return None


def load_alias_map(path: Path) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            alias = (row.get("alias") or "").strip()
            canonical_name = (row.get("canonical_name") or "").strip()
            if not alias or not canonical_name:
                continue
            alias_map[alias] = canonical_name
            alias_map.setdefault(canonical_name, canonical_name)
    return alias_map
