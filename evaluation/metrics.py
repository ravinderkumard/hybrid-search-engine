def precision_at_k(retrieved_docs, relevant_docs, k=5):
    retrieved_k = retrieved_docs[:k]

    relevant_retrieved = len(
        set(retrieved_k).intersection(set(relevant_docs))
    )

    return relevant_retrieved / k

def recall_at_k(retrieved_docs, relevant_docs, k=5):
    retrieved_k = retrieved_docs[:k]

    relevant_retrieved = len(
        set(retrieved_k).intersection(set(relevant_docs))
    )

    return relevant_retrieved / len(relevant_docs)

def reciprocal_rank(retrieved_docs, relevant_docs):
    for rank, doc_id in enumerate(retrieved_docs, start=1):
        if doc_id in relevant_docs:
            return 1 / rank

    return 0