from bm25_test import _score, _compute_idf, _candidate_terms

docs = ["韩冈，表字玉昆，刚刚醒来。"]
query = "玉昆是谁"
query_terms = _candidate_terms(query)
idf, avgdl = _compute_idf(docs, query_terms)

for doc in docs:
    s = _score(query, doc, idf, avgdl)
    print(f"Doc: {doc}, Score: {s}")

