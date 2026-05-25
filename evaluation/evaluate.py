import json

from retrieval.bm25_retriever import BM25Retriever

from evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank
)

with open("data/documents.json", "r") as f:
    documents = json.load(f)

with open("data/evaluation_dataset.json", "r") as f:
    evaluation_data = json.load(f)

retriever = BM25Retriever(documents)

precision_scores = []
recall_scores = []
mrr_scores = []

for item in evaluation_data:
    query = item["query"]
    relevant_docs = item["relevant_docs"]

    retrieved_docs = retriever.retrieve(query, top_k=5)

    precision_scores.append(
        precision_at_k(retrieved_docs, relevant_docs, k=5)
    )

    recall_scores.append(
        recall_at_k(retrieved_docs, relevant_docs, k=5)
    )

    mrr_scores.append(
        reciprocal_rank(retrieved_docs, relevant_docs)
    )

results = {
    "avg_precision@5": sum(precision_scores) / len(precision_scores),
    "avg_recall@5": sum(recall_scores) / len(recall_scores),
    "mrr": sum(mrr_scores) / len(mrr_scores)
}

print(results)