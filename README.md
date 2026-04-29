# Hybrid Search Engine

## Production-Grade BM25 + Dense Retrieval + RRF Full-Stack Search Platform

---

# Overview

Hybrid Search Engine is a recruiter-grade, production-oriented full-stack application designed to solve a fundamental information retrieval problem:

## Traditional search systems often fail because:

### Keyword-only search (BM25)

* Strong lexical precision
* Weak semantic understanding
* Misses synonyms/paraphrases

### Semantic-only search (Dense Retrieval)

* Strong semantic recall
* Weak exact-match constraints
* Can overgeneralize

---

# Solution

This project combines:

## BM25 + SentenceTransformers + FAISS + Reciprocal Rank Fusion (RRF)

This architecture balances:

### Precision + Recall + Explainability

---

# Project Goals

## Primary Objectives:

* Build a hybrid retrieval system from scratch
* Demonstrate sparse + dense retrieval engineering
* Productize retrieval via FastAPI
* Build a modular React frontend
* Prepare for enterprise scaling (Phase 5)

---

# Tech Stack

## Backend

* Python
* FastAPI
* rank_bm25
* SentenceTransformers
* FAISS
* Pydantic

## Frontend

* React
* TypeScript
* Vite
* Tailwind / Custom UI Components

## Search Logic

* BM25 Sparse Retrieval
* Dense Embedding Retrieval
* Reciprocal Rank Fusion (RRF)

---

# Architecture

```txt
User Query
   ↓
React Frontend
   ↓
FastAPI API Layer
   ↓
SearchEngine
   ↓
BM25 + Dense Retrieval
   ↓
RRF Fusion
   ↓
Ranked Results
```

---

# Development Journey

# Phase 1 — Foundation

## Built:

* Project structure
* Config system
* Dummy dataset
* Modular services
* Logging

---

# Phase 2 — Hybrid Retrieval Core

## Implemented:

### BM25:

Sparse lexical retrieval

### Dense:

SentenceTransformers + FAISS

### Fusion:

Reciprocal Rank Fusion (RRF)

---

# Phase 2.5 — Production Hardening

## Added:

* Candidate filtering
* Score validation
* Ranking stabilization
* Explainability diagnostics
* Null safety

---

# Phase 3 — Backend Productization

## FastAPI Endpoints:

```txt
/search
/health
/docs
```

## Features:

* Request validation
* Search orchestration
* Dependency injection
* API documentation

---

# Phase 4 — Frontend Productization

## Built:

* React modular architecture
* Search controls
* Top-K configuration
* Search mode selectors
* Results analytics dashboard
* Tabular result display

---

# Current Features

## Search:

* Hybrid search
* BM25 search
* Dense search
* Adjustable Top-K

## UX:

* Enterprise-style dashboard
* Search metrics
* Explainable ranking
* Results table

---

# Folder Structure

```txt
hybrid-search-engine/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── engine/
│   ├── schemas/
│   └── services/


├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── services/
│       ├── types/
│       └── config/
```

---

# Local Setup

## Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

---

# Why This Project Matters

This project demonstrates:

## Technical Skills:

* Information Retrieval
* NLP Engineering
* Search Relevance
* Full-stack Development
* API Architecture
* Retrieval Explainability

---

# Current Limitations

* In-memory BM25
* Flat FAISS index
* Small dataset
* No distributed search infra
* No reranker

---

# Future Roadmap (Phase 5+)

## Planned:

* Elasticsearch / OpenSearch
* FAISS HNSW / Qdrant
* Cross-encoder reranking
* Query expansion
* RAG integration
* Docker deployment
* Cloud deployment

---

# Resume Bullet

Built a production-grade Hybrid Search Engine combining BM25, SentenceTransformers, FAISS, and Reciprocal Rank Fusion with FastAPI backend and modular React frontend, demonstrating end-to-end search architecture from retrieval theory to productized MVP.

# Scaling Hybrid Search to 1M+ Documents — Problems vs Solutions Matrix
| Problem Area            |                          What Breaks at 1M+ Docs | Why It Happens                                                    | Business / User Impact                         | Required Solution                                     | Why This Fix Works                                              |
| ----------------------- | -----------------------------------------------: | ----------------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------- |
| Sparse Retrieval (BM25) | Python `rank_bm25` becomes slow and memory-heavy | In-memory token scoring and non-distributed processing            | Slow queries, high RAM, poor concurrency       | OpenSearch / Elasticsearch                            | Distributed inverted index enables sub-second sparse retrieval  |
| Dense Retrieval         |        `FAISS IndexFlatL2` becomes too expensive | Exact nearest-neighbor search compares against all vectors (O(N)) | High latency, poor scalability                 | HNSW / IVF / Qdrant / Weaviate                        | ANN reduces retrieval complexity while preserving strong recall |
| Embedding Generation    |     Full corpus re-embedding becomes impractical | One-shot batch encoding doesn’t scale operationally               | Slow updates, stale corpus, expensive rebuilds | Incremental batch pipeline (Celery/Kafka/Airflow)     | Async ingestion supports continuous indexing                    |
| Document Storage        |  Flat files / in-memory docs become unmanageable | No metadata governance or structured persistence                  | Hard filtering, updates, analytics             | PostgreSQL / document store                           | Enables metadata lookup, filtering, governance                  |
| Query Latency           |    Hybrid retrieval pipeline slows significantly | Sparse + dense + fusion over large pools                          | Poor UX, API timeouts                          | Candidate pool optimization + caching                 | Smaller optimized retrieval paths reduce latency                |
| Ranking Quality         |          More documents increase false positives | Larger corpus = more noisy candidates                             | Reduced relevance quality                      | Cross-encoder reranking                               | Deep pairwise relevance improves precision                      |
| Retrieval Depth         |               Small `top_k` misses relevant docs | Sparse and dense candidate pools too narrow                       | Lower recall                                   | Multi-stage retrieval (Top 500 → RRF → Top 50 rerank) | Improves recall before precision refinement                     |
| Infrastructure          |               Single FastAPI process bottlenecks | CPU/GPU concurrency limitations                                   | Downtime under load                            | Gunicorn/Uvicorn workers + NGINX                      | Horizontal request scaling                                      |
| Repeat Queries          |                      Duplicate computation waste | Same queries repeatedly encoded/retrieved                         | Higher cost, slower responses                  | Redis caching                                         | Speeds repeated queries significantly                           |
| Monitoring              |                   No visibility into bottlenecks | Prototype systems lack observability                              | Hard debugging, hidden failures                | Prometheus + Grafana + logs                           | Enables production-grade reliability                            |
| Memory Footprint        |             Vector + sparse indexes grow rapidly | 1M embeddings + metadata are large                                | High infra costs                               | Compression (PQ, float16, chunking)                   | Reduces storage and memory                                      |
| Large Documents         |            Full-document retrieval quality drops | Large docs dilute semantic meaning                                | Poor relevance                                 | Chunking (300–800 tokens)                             | Improves retrieval granularity                                  |
| Incremental Updates     |             Reindexing entire corpus is too slow | Monolithic indexing approach                                      | Operational friction                           | Event-driven indexing pipeline                        | Supports continuous growth                                      |
| Security / Multi-Tenant |                  Access control becomes critical | More users + enterprise use cases                                 | Data leakage risk                              | Auth + ACL + tenant isolation                         | Enterprise-safe deployment                                      |
| Explainability          |           Hybrid scoring becomes harder to debug | Larger retrieval complexity                                       | Harder trust/debugging                         | Score logging + observability dashboard               | Preserves transparency                                          |




## Phase wise breakdown of scaling solutions:
|Step|	Deliverable|	Risk Level|	Priority|
|---|---|---|---|
|1	|requirements + .env + config|	Low|	Critical|
|2	|OpenSearch client|	Medium|	Critical|
|3	|Index service|	Medium|	Critical|
|4	|Ingestion pipeline|	Medium|	Critical|
|5	|BM25 replacement|	High|	Critical|
|6	|Search engine integration|	High|	Critical|
|7	|Testing|	Medium|	High|