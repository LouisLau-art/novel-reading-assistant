class AliasResolver:
    def __init__(self, alias_map: dict[str, str]) -> None:
        self.alias_map = alias_map

    def resolve(self, name: str) -> str | None:
        return self.alias_map.get(name)
