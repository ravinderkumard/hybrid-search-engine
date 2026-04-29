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

# Recruiter Value

Ideal for roles in:

## AI Engineer

## Search Engineer

## Applied NLP Engineer

## RAG Engineer

## Full-stack AI Product Builder

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

## Built a production-grade Hybrid Search Engine combining BM25, SentenceTransformers, FAISS, and Reciprocal Rank Fusion with FastAPI backend and modular React frontend, demonstrating end-to-end search architecture from retrieval theory to productized MVP.

