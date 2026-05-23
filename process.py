import json
with open("data/documents.json", "r") as f:
    documents = json.load(f)

from retrieval.bm25_retriever import BM25Retriever

retriever = BM25Retriever(documents)

query = "polymer quantum mechanics"

results = retriever.retrieve(query)

print(results)