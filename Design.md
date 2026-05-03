# Hybrid Search Engine — Solution Architecture Design Document

## From Problem Statement → Architecture Decisions → MVP → Scale Path

---

# 1. Problem Statement

Modern search systems struggle because:

## BM25 Alone:

### Pros:

* Exact keyword precision
* Fast lexical retrieval

### Cons:

* Weak semantic understanding
* Misses synonyms and paraphrases

---

## Dense Search Alone:

### Pros:

* Semantic understanding
* Better intent recall

### Cons:

* Weak exact-term constraints
* Reduced lexical precision

---

# Strategic Design Goal

Build:

# Hybrid Retrieval Architecture

Combining:

## Sparse + Dense + Fusion

---

# 2. Solution Strategy

## Core Principle:

### Retrieval quality improves when lexical precision and semantic recall work together.

---

# Selected Architecture:

## BM25 + SentenceTransformers + FAISS + RRF

---

# Why These Choices?

## BM25:

### Purpose:

Fast lexical retrieval

---

## SentenceTransformers:

### Purpose:

Semantic embeddings

---

## FAISS:

### Purpose:

Vector similarity search

---

## Reciprocal Rank Fusion:

### Purpose:

Stable rank-level hybridization

### Why Not Raw Score Merge?

Because BM25 and cosine/L2 scales differ.

---

# 3. System Architecture

```txt
User Query
   ↓
Query Processing Layer
   ↓
┌──────────────────────┬──────────────────────┐
│ Sparse Retrieval     │ Dense Retrieval      │
│ BM25                 │ SentenceTransformers │
│ rank_bm25            │ FAISS                │
└──────────────────────┴──────────────────────┘
            ↓
 Candidate Merge
            ↓
 Reciprocal Rank Fusion
            ↓
 Final Ranked Results
```

---

# 4. Application Layers

# Backend Layer

## Responsibilities:

* Query intake
* Retrieval orchestration
* Fusion
* Validation
* API responses

---

## Components:

### `bm25_service.py`

Sparse retrieval

### `embedding_service.py`

Embedding generation

### `faiss_service.py`

Dense retrieval

### `hybrid_service.py`

Fusion + ranking

### `search_engine.py`

Unified orchestration

---

# Frontend Layer

## Responsibilities:

* User query entry
* Search mode selection
* Top-K control
* Result analytics
* Tabular results

---

# 5. Key Design Decisions

# Decision A:

## Modular Architecture

### Why:

Scalability + maintainability

---

# Decision B:

## API-first via FastAPI

### Why:

Backend becomes reusable platform

---

# Decision C:

## React + TypeScript

### Why:

Production frontend maturity

---

# Decision D:

## Explainable Ranking

### Why:

Real users need transparency

---

# 6. Production Hardening (Phase 2.5)

## Risks Identified:

* Null scores
* Candidate pollution
* Zero BM25 corruption
* Invalid dense fallback

---

# Fixes:

* Thresholding
* Candidate filtering
* Null-safe rendering
* Ranking integrity
* Explainability metrics

---

# 7. API Design

## Endpoints:

```txt
/search
/health
/docs
```

---

# Request Model:

```json
{
  "query": "best laptop for programming",
  "top_k": 10
}
```

---

# Response Model:

```json
{
  "query": "...",
  "total_results": 10,
  "results": [...]
}
```

---

# 8. Frontend UX Evolution

## Initial:

Card layout

## Upgraded:

Enterprise-style table

---

# Why:

### Better comparison

### Better retrieval observability

### Better scalability for large result sets

---

# 9. Performance Scope (Current)

## Best For:

* Small datasets
* Prototype users
* Portfolio demonstrations
* Search experimentation

---

# Constraints:

* In-memory BM25
* Flat vector search
* Single-machine deployment

---

# 10. Security & Reliability

## Current:

* Input validation
* Type-safe frontend
* API schemas
* Controlled Top-K

---

# Future:

* Auth
* Rate limiting
* Monitoring
* Logging pipelines

---

# 11. Scale Roadmap (Phase 5)

## Planned Evolution:

### Sparse:

rank_bm25 → OpenSearch

### Dense:

FAISS Flat → HNSW / Qdrant

### Fusion:

RRF → RRF + Cross-Encoder

### Infra:

Single machine → Distributed retrieval

---

# 12. Business Value

This system can evolve into:

## Enterprise Search

## Knowledge Search

## Product Search

## RAG Retrieval Layer

## Internal Documentation Search

---

# 13. STAR Positioning

## Situation:

Search quality gap

## Task:

Build hybrid retrieval platform

## Action:

Designed sparse + dense + fusion full-stack system

## Result:

Hybrid Search MVP with scale path

---

# 14. Engineering Maturity Demonstrated

## Shows:

* Search systems thinking
* Retrieval engineering
* API design
* Frontend productization
* Modular architecture
* Production planning

---

# 15. Final Architectural Summary

## Current State:

### Production-ready MVP

## Next State:

### Enterprise-scale retrieval platform

---

## 1M+ Document Scale

### Challenges:

1. **Sparse Retrieval**:
   - BM25 becomes slower and more memory-intensive.
   - Solution: Use OpenSearch for distributed inverted indexing.

2. **Dense Retrieval**:
   - FAISS IndexFlatL2 struggles with large datasets.
   - Solution: Implement HNSW or IVF for approximate nearest neighbor search.

3. **Embedding Generation**:
   - Full corpus re-embedding is impractical.
   - Solution: Use an incremental batch pipeline (e.g., Celery, Kafka).

4. **Document Storage**:
   - Flat files/in-memory docs are unmanageable.
   - Solution: Migrate to PostgreSQL or a document store.

5. **Query Latency**:
   - Hybrid retrieval pipeline slows down.
   - Solution: Optimize candidate pools and implement caching.

6. **Ranking Quality**:
   - More documents lead to false positives.
   - Solution: Introduce cross-encoder reranking.


#### ANN + HNSW for Dense Retrieval
As our Hybrid Search Engine grows from a prototype into a large-scale retrieval platform, dense vector search becomes a major bottleneck. Our original FAISS IndexFlatL2 performs exact nearest-neighbor search, which means every query compares against every document embedding.

**Problem with Exact Dense Search**

At small scale, this works well.
At 1M+ documents, it becomes computationally expensive because:

Challenges:
- Query latency increases significantly
- Memory usage grows linearly
- Poor concurrency under real traffic
- Dense retrieval becomes the primary scaling bottleneck

**Solution: Approximate Nearest Neighbor (ANN) Search**
To scale dense retrieval efficiently, we introduce:

ANN — Approximate Nearest Neighbor Search
- ANN avoids brute-force comparison by intelligently narrowing search space to highly probable candidates.

Why ANN?
- Instead of checking every vector:

ANN searches efficiently through structured approximations

**Key Parameters**
M - Defines how many neighbors each node (document vector) connects to.

Higher M:
- Better recall
- Better graph quality
- More memory

Recommended:
- M = 32


efConstruction - Controls how carefully the graph is built during indexing.

Higher efConstruction:
- Better graph structure
- Better future retrieval quality
- Slower indexing

Recommended:
- efConstruction = 200

efSearch - Controls how deeply the graph is explored during query time.

Higher efSearch:
- Better retrieval accuracy
- Slower search

Recommended:
- efSearch = 128