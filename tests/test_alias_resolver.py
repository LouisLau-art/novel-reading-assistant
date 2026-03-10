from app.retrieval.alias_resolver import AliasResolver


def test_alias_resolver_maps_courtesy_name_to_canonical():
    resolver = AliasResolver({"玉昆": "韩冈", "韩冈": "韩冈"})
    assert resolver.resolve("玉昆") == "韩冈"
