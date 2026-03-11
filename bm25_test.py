import math
from app.retrieval.vector_index import _candidate_terms

def _compute_idf(corpus_documents: list[str], query_terms: list[str]) -> tuple[dict[str, float], float]:
    N = len(corpus_documents)
    if N == 0:
        return {}, 0.0
        
    idf = {}
    doc_terms_list = [_candidate_terms(doc) for doc in corpus_documents]
    avgdl = sum(len(dt) for dt in doc_terms_list) / N
    
    for q_term in query_terms:
        n_qi = sum(1 for dt in doc_terms_list if q_term in dt)
        # using standard okapi bm25 idf, but avoiding negative
        idf[q_term] = math.log(1.0 + (N - n_qi + 0.5) / (n_qi + 0.5))
            
    return idf, avgdl

def _score(query_text: str, document: str, idf: dict[str, float], avgdl: float) -> float:
    k1 = 1.2
    b = 0.75
    score = 0.0
    query_terms = _candidate_terms(query_text)
    doc_terms = _candidate_terms(document)
    doc_len = len(doc_terms)
    
    if doc_len == 0 or avgdl == 0:
        return 0.0

    for q_term in query_terms:
        if q_term in doc_terms:
            tf = document.count(q_term)
            score += idf.get(q_term, 0.0) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
            
    return score

docs = [
    "韩冈在第八章现身",
    "韩冈后文有大变化"
]
query = "韩冈"
query_terms = _candidate_terms(query)
idf, avgdl = _compute_idf(docs, query_terms)

for doc in docs:
    s = _score(query, doc, idf, avgdl)
    print(f"Doc: {doc}, Score: {s}")

