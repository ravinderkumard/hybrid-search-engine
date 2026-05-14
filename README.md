# Hybrid Search Engine

A production-oriented hybrid retrieval system combining sparse lexical search, dense vector retrieval, reranking, and metadata governance using an asynchronous distributed backend architecture.

---

# Overview

This project implements a scalable hybrid search pipeline inspired by modern retrieval systems used in large-scale AI/search platforms.

The system combines:

* **BM25 sparse retrieval** using OpenSearch
* **Dense semantic retrieval** using FAISS + HNSW
* **Hybrid ranking fusion** using Reciprocal Rank Fusion (RRF)
* **Neural reranking** using Cohere Rerank API
* **PostgreSQL metadata governance**
* **Asynchronous retrieval orchestration**
* **Distributed containerized deployment**
* **Observability and metrics instrumentation**

The architecture is designed to balance:

* lexical precision
* semantic recall
* retrieval latency
* scalability
* operational visibility

---

# High-Level Architecture

```text
                        ┌───────────────────┐
                        │     Client/API    │
                        └─────────┬─────────┘
                                  │
                                  ▼
                      ┌─────────────────────┐
                      │  FastAPI Gateway    │
                      │  Async Search API   │
                      └─────────┬───────────┘
                                │
                                ▼
                 ┌────────────────────────────┐
                 │   HybridSearchService      │
                 │  Async Retrieval Pipeline  │
                 └─────────┬──────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
┌──────────────────┐              ┌────────────────────┐
│ OpenSearch BM25  │              │ Embedding Service  │
│ Sparse Retrieval │              │ SentenceTransformer│
└────────┬─────────┘              └─────────┬──────────┘
         │                                   │
         │                                   ▼
         │                    ┌────────────────────────┐
         │                    │ FAISS + HNSW ANN Index │
         │                    │ Dense Vector Retrieval │
         │                    └──────────┬─────────────┘
         │                               │
         └──────────────┬────────────────┘
                        ▼
           ┌─────────────────────────┐
           │ Reciprocal Rank Fusion  │
           │        (RRF)            │
           └──────────┬──────────────┘
                      │
                      ▼
           ┌─────────────────────────┐
           │ Cohere Neural Reranker  │
           └──────────┬──────────────┘
                      │
                      ▼
           ┌─────────────────────────┐
           │ PostgreSQL Metadata DB  │
           │ Governance + Enrichment │
           └──────────┬──────────────┘
                      │
                      ▼
               Final Ranked Results
```

---

# Core Components

## 1. FastAPI Async API Layer

Provides:

* asynchronous search endpoints
* request validation
* health checks
* Prometheus metrics
* structured logging
* dependency injection

### Key Features

* async request handling
* timeout-aware retrieval
* request-level tracing
* scalable API orchestration

---

## 2. OpenSearch BM25 Retrieval

Implements sparse lexical retrieval using OpenSearch BM25 ranking.

### Responsibilities

* keyword relevance
* lexical precision
* scalable inverted indexing
* distributed sparse retrieval

### Why BM25

* strong exact-match precision
* efficient ranking
* production-proven retrieval algorithm

---

## 3. Dense Semantic Retrieval (FAISS + HNSW)

Uses SentenceTransformers embeddings with FAISS Approximate Nearest Neighbor search.

### Features

* semantic similarity search
* vector indexing
* HNSW ANN acceleration
* low-latency dense retrieval

### Embedding Model

```text
sentence-transformers/all-MiniLM-L6-v2
```

---

## 4. Hybrid Retrieval Fusion (RRF)

Combines sparse and dense retrieval outputs using:

### Reciprocal Rank Fusion (RRF)

This improves:

* recall quality
* ranking robustness
* semantic + lexical balance

The system merges:

* BM25 rankings
* dense vector rankings

into a unified ranked result set.

---

## 5. Neural Reranking

Uses Cohere Rerank API for final ranking refinement.

### Responsibilities

* contextual relevance scoring
* semantic reranking
* improving top-k quality

### Pipeline

1. Hybrid retrieval
2. Candidate fusion
3. Neural reranking
4. Final response generation

---

## 6. PostgreSQL Metadata Governance

PostgreSQL acts as the metadata source of truth.

### Responsibilities

* document enrichment
* active/inactive filtering
* metadata consistency
* governance layer

This separates:

* retrieval indexing
  from
* authoritative metadata management

---

# Asynchronous Retrieval Architecture

The system uses asynchronous orchestration for improved scalability and latency reduction.

## Concurrent Retrieval Flow

The following operations execute concurrently:

* BM25 OpenSearch retrieval
* embedding generation

After embeddings complete:

* dense vector retrieval executes

CPU-bound workloads:

* SentenceTransformer inference
* FAISS ANN search

are offloaded using:

```python
asyncio.to_thread()
```

This prevents event-loop blocking while maintaining high concurrency.

---

# Infrastructure Stack

## Backend Services

| Component          | Purpose             |
| ------------------ | ------------------- |
| FastAPI            | API Gateway         |
| Gunicorn + Uvicorn | ASGI Server         |
| OpenSearch         | Sparse Retrieval    |
| FAISS              | Dense Vector Search |
| PostgreSQL         | Metadata Governance |
| MinIO              | Object Storage      |
| Cohere API         | Neural Reranking    |

---

## Observability Stack

| Component          | Purpose                 |
| ------------------ | ----------------------- |
| Prometheus         | Metrics Collection      |
| Grafana            | Visualization Dashboard |
| Structured Logging | Request Tracing         |

---

## Containerization & Orchestration

The system is fully containerized using Docker Compose.

Infrastructure includes:

* multiple FastAPI replicas
* reverse proxy load balancing
* health checks
* startup dependency sequencing
* distributed service networking

---

# Key Engineering Achievements

## Async Distributed Retrieval Pipeline

Implemented a fully asynchronous retrieval orchestration layer using:

* asyncio
* async OpenSearch client
* thread offloading for CPU-bound workloads

---

## Hybrid Sparse + Dense Retrieval

Built a hybrid ranking system combining:

* BM25 lexical relevance
* semantic vector similarity
* reciprocal rank fusion

---

## ANN Search Optimization

Integrated:

* FAISS HNSW indexing
* approximate nearest neighbor retrieval
* low-latency semantic search

---

## Production-Oriented Architecture

Implemented:

* health checks
* observability
* structured logging
* metrics instrumentation
* containerized deployment
* dependency orchestration

---

## Metadata Governance Layer

Separated:

* retrieval indexing
  from
* authoritative metadata management

using PostgreSQL enrichment.

---

# Technologies Used

## Backend

* Python
* FastAPI
* Gunicorn
* Uvicorn

## Retrieval & ML

* OpenSearch
* FAISS
* HNSW
* SentenceTransformers
* Cohere Rerank API

## Database & Storage

* PostgreSQL
* MinIO

## Infrastructure

* Docker
* Docker Compose
* Nginx

## Observability

* Prometheus
* Grafana

---

# Future Improvements

Planned enhancements:

* Redis query caching
* async PostgreSQL support
* CI/CD pipelines
* Kubernetes deployment
* retrieval benchmarking
* load testing
* retrieval evaluation metrics
* OpenTelemetry tracing
* adaptive retrieval strategies
* self-optimizing reranking pipelines

---

# Project Goals

This project was designed to explore:

* retrieval infrastructure engineering
* hybrid search architectures
* asynchronous backend systems
* scalable semantic search
* production-oriented AI infrastructure
* distributed systems orchestration

while building a backend system that mirrors real-world retrieval pipelines used in modern AI/search platforms.
