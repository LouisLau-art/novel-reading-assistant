from pathlib import Path

from app.retrieval.vector_index import LocalVectorIndex


def test_local_vector_index_filters_by_metadata(tmp_path: Path):
    index = LocalVectorIndex(tmp_path / "index")
    index.upsert_many(
        "novel",
        [
            {
                "id": "c1",
                "document": "韩冈在第八章现身",
                "metadata": {"chapter_idx": 8, "source_type": "novel"},
            },
            {
                "id": "c2",
                "document": "韩冈后文有大变化",
                "metadata": {"chapter_idx": 20, "source_type": "novel"},
            },
        ],
    )
    results = index.query(
        "novel",
        "韩冈",
        n_results=5,
        where={"chapter_idx": {"$lte": 10}},
    )
    assert [item["id"] for item in results] == ["c1"]


def test_local_vector_index_matches_chinese_natural_language_query(tmp_path: Path):
    index = LocalVectorIndex(tmp_path / "index")
    index.upsert_many(
        "novel",
        [
            {
                "id": "c1",
                "document": "韩冈，表字玉昆，刚刚醒来。",
                "metadata": {"chapter_idx": 1, "source_type": "novel"},
            }
        ],
    )

    results = index.query(
        "novel",
        "玉昆是谁",
        n_results=1,
        where={"chapter_idx": {"$lte": 1}},
    )

    assert [item["id"] for item in results] == ["c1"]
