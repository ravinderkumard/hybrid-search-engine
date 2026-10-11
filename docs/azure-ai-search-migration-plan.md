# Azure AI Search Migration Plan

Replace OpenSearch (BM25) + FAISS (dense) + in-app RRF + Cohere Rerank with **Azure AI Search**.

**Status:** Plan only — no code changed yet
**Branch:** `feature/cloud-deployment-plan`
**Last updated:** 2026-10-11 (Phase 0 detailed after the branch review)

## Decisions

| Topic | Decision |
|---|---|
| Old backend | **Replace completely.** The OpenSearch and FAISS code is removed in the cutover phase (Phase 6), after Azure is proven. |
| Embeddings | **Azure OpenAI** `text-embedding-3-small` (1536 dims). Queries are vectorized server-side by an index *vectorizer*. |
| Reranking | **Azure semantic ranker**, replacing Cohere. |
| Governance | **PostgreSQL stays the source of truth** for metadata and active/inactive state. |
| Document key | **The Postgres integer `id`** (as a string). `arxiv_id` is stored as a separate field. |
| Execution approach | **Local first.** Everything that doesn't need Azure is built and tested first, against interfaces with in-memory fakes. Azure is only needed from Phase 4. |
| Azure resources | Not created yet (Phase 4). |

---

## Target architecture

**Today**

```text
query ─┬─> OpenSearch BM25 ───────────────┐
       └─> MiniLM embed ─> FAISS HNSW ────┴─> RRF (app) ─> Postgres governance ─> Cohere rerank
```

**After**

```text
query ─> Azure AI Search (single call) ───────────────────────────> Postgres governance ─> response
           ├─ BM25 over title/content
           ├─ HNSW vector search (query vectorized by Azure OpenAI vectorizer)
           ├─ RRF fusion (built in)
           └─ Semantic ranker on top 50
```

---

## Execution order

| Phase | What | Needs Azure? | Cost |
|---|---|---|---|
| 0 | Prepare branch and evaluation baseline | No | $0 |
| 1 | Local foundations: config, dependencies, interfaces, fakes, test setup | No | $0 |
| 2 | Index schema and ingestion code (tested with fakes) | No | $0 |
| 3 | Query path and API code (tested with fakes) | No | $0 |
| 4 | Azure setup (Stages 4.1–4.7) | **Yes** | about $0 on the Free tier |
| 5 | Integration on Azure: create the index, ingest, run live search | **Yes** | Free tier for the sample; Basic for the full dataset |
| 6 | Cutover and cleanup: remove OpenSearch, FAISS and Cohere | No | $0 |
| 7 | Verify and tune against the baseline | **Yes** | Basic tier |
| 8 | Deploy | **Yes** | Ongoing |

- **Phases 0–3 need no Azure account.** Phase 4 can also run in parallel with Phases 1–3 if you prefer.
- **Why fakes are needed:** Azure AI Search has no official local emulator, so local development and tests use the in-memory implementations described next.
- **Mapping from the previous version of this plan:**
  - old Phase 1 (Azure setup) → **Phase 4**
  - old Phases 2–4 (code) → **Phases 2–3**
  - running that code against Azure → **Phase 5**
  - old Phase 5 deletions → **Phase 6**
  - old Phase 6 (verify) → **Phase 7**
  - old Phase 7 (deploy) → **Phase 8**

---

## Local-first design

All Azure-specific code sits behind three small interfaces. Every other part of the app depends only on these interfaces, so it can be built and tested without Azure.

```python
# app/search/interfaces.py
class SearchHit(BaseModel):
    doc_id: str                  # Postgres id
    arxiv_id: str | None
    search_score: float          # fused (RRF) score
    reranker_score: float | None # semantic ranker, 0–4

class SearchBackend(Protocol):
    async def search(self, query: str, top_k: int,
                     strategy: str = "HYBRID") -> list[SearchHit]: ...  # BM25 | DENSE | HYBRID (agent routing)
    async def health(self) -> bool: ...
    async def close(self) -> None: ...

class IndexWriter(Protocol):
    def create_or_update_index(self) -> None: ...
    def upload(self, docs: list[dict]) -> int: ...
    def set_active(self, doc_ids: list[str], active: bool) -> None: ...
    def delete(self, doc_ids: list[str]) -> None: ...
    def count(self) -> int: ...

class EmbeddingProvider(Protocol):
    dimensions: int
    def embed(self, texts: list[str]) -> list[list[float]]: ...
```

| Interface | Fake (local, Phases 1–3) | Azure (Phase 5 onward) |
|---|---|---|
| `SearchBackend` | `InMemorySearchBackend`: token-overlap scoring, plus a pseudo reranker score in the 0–4 range | `AzureSearchBackend` |
| `IndexWriter` | `InMemoryIndexWriter` | `AzureIndexWriter` |
| `EmbeddingProvider` | `FakeEmbeddingProvider`: deterministic hash-based vectors of the configured size | `AzureOpenAIEmbeddingProvider` |

- **Selection:** a `SEARCH_BACKEND=fake|azure` setting, read by `app/search/factory.py`.
- **Production guard:** the app refuses to start with `fake` when `APP_ENV=production`.

---

## Phase 0 — Prepare branch and baseline 🟢 Local

**Goal:** a clean migration branch that contains the agentic-RAG work and the evaluation dataset, plus a trustworthy baseline measurement of the **current** pipeline (OpenSearch + FAISS + RRF + Cohere) to compare Azure against later.

**Findings from the branch review (2026-10-11):**

| Finding | Impact |
|---|---|
| `feature/cloud-deployment-plan` has no commits of its own. It points at the same commit as `feature/open-search_elastic-search` (`d0e2b28`). | The migration branch can simply be fast-forwarded. |
| `feature/agentic-rag` = `open-search_elastic-search` **+ 4 commits**. It only adds files; nothing underneath changes. | The merge is a clean fast-forward with no conflicts. |
| `data/evaluation_dataset.json` (81 queries, ids are arXiv ids) exists **only** on `feature/agentic-rag`. | The current branch can't run any evaluation. |
| `evaluation/evaluate.py` measures an in-memory `rank_bm25` retriever, **not** the live pipeline. It also tokenizes case-sensitively and only prints its results. | It isn't usable as a baseline, so a new harness is needed. |
| `evaluation/metrics.py` (precision@k, recall@k, reciprocal rank) is correct. | Reuse it. |
| All 41 relevant docs in the evaluation set exist in the 7,198-doc `documents.json`, within its first 48 records. No query has an empty relevant list. | The data supports a valid baseline. |
| Ingestion (`scripts/ingest_arxiv.py`) reads `datasets/arxiv.json` from **MinIO**, not `documents.json`, with `limit=1000`. | Confirm the indexed corpus contains the 41 relevant docs before measuring (Stage 0.4). |
| Postgres keeps the integer `id` and the arXiv id in `arxiv_id`. The search response returns only the integer id. | The harness needs `arxiv_id` in results to score against the evaluation set. |
| Local `main` is 6 commits behind `origin/main` (README updates). `b5c9d23` (design PNGs) is on `main` only. | Housekeeping; it doesn't block the migration. |

> **Before running git steps from Claude:** deleting files is disabled in this folder by default, and git needs it for its lock files. Grant delete permission for the project folder first, or run the git commands yourself.

---

### Stage 0.1 — Tidy the working tree

1. **Ignore local clutter.** Add to `.gitignore`:
   ```gitignore
   .DS_Store
   extracted_100mb.json
   evaluation/results/*.tmp
   ```
2. **Stop tracking the macOS files:** `git rm --cached .DS_Store app/.DS_Store`
3. **Decide on `data/documents.json`.** The working copy has 7,198 docs (about 10 MB); the committed version has 5.

   | Option | Pros | Cons |
   |---|---|---|
   | **A (recommended).** Commit the 7,198-doc file. | Evaluation is reproducible from git alone; the evaluation set's relevant docs are inside it | Adds about 10 MB to the repo |
   | B. Restore the 5-doc sample (`git restore data/documents.json`) and keep the full set in a git-ignored file | Repo stays small | The baseline depends on a file that isn't in git |
4. **Commit the plan document:** `docs/azure-ai-search-migration-plan.md`

**Check:** `git status` shows a clean tree, apart from the intentionally ignored files.

---

### Stage 0.2 — Bring the agentic-RAG work into the migration branch

```bash
git checkout feature/cloud-deployment-plan
git merge --ff-only feature/agentic-rag     # fast-forward: 4 commits, no conflicts
```

**This brings in:**
- the Retrieval Strategy Agent;
- `/agentic-search`;
- `ModelLoader`;
- ADR 001;
- `data/evaluation_dataset.json`;
- `langchain_openai` and `langgraph` in `requirements.txt`.

**Known issues that come with it.** These are recorded here, *not* fixed in Phase 0. They are fixed in a separate task.

- **`/agentic-search` isn't usable yet:**
  - it ignores the request and always asks about `"Explain LoginService API"`;
  - it returns `null` (it only `print`s the decision);
  - it never calls the search engine;
  - it creates a new LLM client per request;
  - it calls the LLM synchronously inside an async handler;
  - its handler function reuses the name `search`.
- `app/agents/retrieval/schema.py` duplicates `retrieval_schema.py`. `agent.py`, `parser.py` and `prompt.txt` are empty.
- `RetrievalParser` fails if the LLM wraps its JSON in a markdown code block.
- `pyyaml` (used by `config_loader.py`) isn't pinned in `requirements.txt`.
- **Link to the migration:** the agent's `BM25 / DENSE / HYBRID` strategies map to Azure text-only, vector-only and hybrid + semantic queries. Phase 3 gives `SearchBackend.search()` a `strategy` argument so the agent survives the migration.

**Check:** `git log --oneline -5` shows `37e5064` at the top, and `data/evaluation_dataset.json` exists.

---

### Stage 0.3 — Sync `main` (housekeeping)

```bash
git fetch origin
git log --oneline main..origin/main    # review the 6 incoming commits (README updates)
git checkout main && git pull --ff-only && git checkout feature/cloud-deployment-plan
```

Optionally run `git merge main` into the migration branch to pick up `b5c9d23` (the design PNGs). That's not required for the migration.

**Check:** `git status` on `main` reports "up to date with origin/main".

---

### Stage 0.4 — Bring up the current stack and confirm what is indexed

1. **Start the stack:** `docker compose up -d` (Postgres, OpenSearch, Redis, MinIO, API).
2. **Ingest the arXiv data** if the stores are empty (`ingestion-worker`, which runs `scripts.ingest_arxiv`).
3. **Confirm all three stores agree:**
   ```bash
   # Postgres
   docker exec -it <postgres-container> psql -U postgres -d hybrid_search -c "select count(*) from documents where is_active;"
   # OpenSearch
   curl -s localhost:9200/hybrid-search-documents/_count
   # FAISS
   python -c "import faiss; print(faiss.read_index('data/faiss.index').ntotal)"
   ```
4. **Confirm all 41 relevant arXiv ids are present** in Postgres `documents.arxiv_id` (a short query or script).

**Check:** the counts match each other (expect about 1,000 with the current `limit`); 41 of 41 relevant ids are present; `GET /health` reports healthy.

---

### Stage 0.5 — Build the evaluation harness for the real pipeline

1. **Small backward-compatible code change:** add `arxiv_id` to `DocumentMetadataService.enrich_results()`, so results can be matched to the evaluation set.
2. **New file `evaluation/evaluate_engine.py`:**
   - **Input:** `data/evaluation_dataset.json`.
   - **Process:** run each query through `SearchEngine.search()` in-process (a `--mode api` option calls `POST /search` instead). Map results to `arxiv_id` and score them with `evaluation/metrics.py`.
   - **Metrics:** precision@5, recall@5, MRR, plus hit-rate@5.
   - **Breakdowns:** overall and by `query_type` (keyword 37, semantic 36, typo 4, multi-intent 2, ambiguous 1, long-context 1).
   - **Latency:** p50, p95 and max, in ms.
   - **Output:** JSON in `evaluation/results/` with:
     - metadata (git commit, backend name, timestamp, indexed doc count, `top_k`);
     - aggregate metrics;
     - per-query rows (query, type, expected ids, returned ids, hit/miss, latency).
   - **CLI:** `python -m evaluation.evaluate_engine --top-k 5 --label baseline_opensearch_faiss`
3. **Unit tests** for `metrics.py` (known inputs → known outputs).
4. **Leave alone:**
   - `evaluate.py` stays as the "BM25-only reference". It is deleted in Phase 6 along with `rank_bm25`.
   - `evaluation.py` is a scratch file; delete it in Phase 6.

**Check:** a dry run on 3 queries writes a well-formed JSON file.

---

### Stage 0.6 — Record the baseline

1. **Run the harness** against the current stack:
   ```bash
   python -m evaluation.evaluate_engine --top-k 5 --label baseline_opensearch_faiss
   ```
2. **Also save the old BM25-only numbers** for reference: run `python -m evaluation.evaluate` and save its output to `evaluation/results/reference_rank_bm25.json`.
3. **Summarize** the headline numbers in a short `evaluation/results/README.md`: overall P@5, R@5, MRR, p95 latency, and the weakest query types.
4. **Commit** the harness, results and README.

---

### Phase 0 sign-off

- [ ] Working tree clean; `.gitignore` updated; `documents.json` decision made and committed (0.1)
- [ ] `feature/cloud-deployment-plan` fast-forwarded to include `feature/agentic-rag` (0.2)
- [ ] `main` synced with `origin/main` (0.3)
- [ ] Current stack healthy; Postgres, OpenSearch and FAISS counts match; 41 of 41 relevant docs indexed (0.4)
- [ ] `evaluate_engine.py` built, with `arxiv_id` in results and metrics unit tests passing (0.5)
- [ ] `baseline_opensearch_faiss.json` and `reference_rank_bm25.json` committed, with a summary (0.6)

**Exit criteria:** every box above is ticked. Phase 7 compares Azure against `baseline_opensearch_faiss.json`.

---

## Phase 1 — Local foundations 🟢 Local

1. **Dependencies.** Add `azure-search-documents`, `azure-identity` and `openai` to `requirements.txt`, then `pip install`. No Azure account is needed. Old dependencies stay until Phase 6.
2. **Config** (`app/core/config.py`). Add:
   - `SEARCH_BACKEND` (default `fake` until Phase 5)
   - `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX`, `AZURE_SEARCH_API_KEY`
   - `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_API_KEY`
   - `EMBEDDING_DIMENSIONS`, `SEMANTIC_CONFIG_NAME`, `MIN_RERANKER_SCORE`

   All Azure values are optional, so the app starts without them. A clear error is raised only when `SEARCH_BACKEND=azure` and a required value is missing.
3. **`.env.example`.** Commit it with every key and empty values.
4. **Interfaces and fakes.** Create `app/search/interfaces.py`, `app/search/fakes.py` and `app/search/factory.py`, as described in *Local-first design*.
5. **Test setup.** Create a `tests/unit/` folder run by `pytest`. The existing root `test_*.py` files are manual scripts and stay as they are for now. Add a `pytest.ini` with an `azure` marker for integration tests, which are skipped unless Azure environment variables are set.

6. **Connectivity script.** Write `scripts/check_azure_connectivity.py` now. It isn't run until Stage 4.6.

**Exit criteria:** `pytest tests/unit` passes; the API starts with `SEARCH_BACKEND=fake`.

---

## Phase 2 — Index schema and ingestion code 🟢 Local

### Index design

Index name: `hybrid-search-documents`

| Field | Type | Attributes / notes |
|---|---|---|
| `id` | `Edm.String` | **Key.** The Postgres `documents.id`, as a string. |
| `arxiv_id` | `Edm.String` | filterable, retrievable — used by the evaluation set |
| `title` | `Edm.String` | searchable, retrievable |
| `content` | `Edm.String` | searchable |
| `category` | `Edm.String` | filterable, facetable |
| `source` | `Edm.String` | filterable |
| `is_active` | `Edm.Boolean` | filterable — inactive docs are excluded inside the search query |
| `published_at` | `Edm.DateTimeOffset` | filterable, sortable |
| `content_vector` | `Collection(Edm.Single)`, 1536 dims | HNSW profile + Azure OpenAI vectorizer; not retrievable, to save space |

**Additional configuration**

- **Semantic configuration** `default`: title field = `title`; content fields = `content`.
- **HNSW:** cosine metric, `m=4`, `efConstruction=400`, `efSearch=128` (matches the current `FAISS_EF_SEARCH`).
- **Vectorizer:** Azure OpenAI, pointing to the embedding deployment, using the Search service's managed identity.
- **Optional storage savings:** scalar quantization, or 512-dimension embeddings.

> **Key characters.** Azure keys allow only letters, digits, `-`, `_` and `=`. The Postgres integer id is always valid. If you ever key on `arxiv_id` instead (for example `0704.0001`), it must be base64url-encoded because of the dot.

### Code

| File | Purpose |
|---|---|
| `app/search/azure/index_schema.py` | `build_index(settings) -> SearchIndex`. A pure function: SDK models are built offline, so it's unit-testable. |
| `app/search/azure/index_writer.py` | `AzureIndexWriter`: create/update the index, upload in batches of up to 1,000, set `is_active` by merge, delete, count |
| `app/search/azure/embeddings.py` | `AzureOpenAIEmbeddingProvider`: batches of about 100; `tenacity` retries on 429/503 |
| `app/services/document_ingestion_service.py` | Postgres upsert (unchanged) → `EmbeddingProvider` → `IndexWriter`, both taken from the factory |
| `scripts/create_azure_index.py` | Create or rebuild the index (uses the factory, so it runs against the fake locally) |
| `scripts/index_documents_azure.py` | Bulk-index `DATA_PATH`; supports `--rebuild` and `--dry-run` |

### Local tests

- **Schema:** the key field, the field list, vector dims equal to `EMBEDDING_DIMENSIONS`, the semantic config name, and the vectorizer deployment name.
- **Ingestion with fakes:**
  - N docs produce N uploads with correctly sized vectors;
  - `is_active` mapping is correct;
  - batches split at the 1,000 boundary;
  - a mocked 429 is retried.

**Exit criteria:** the ingestion pipeline runs end to end against the fakes, and the tests are green.

---

## Phase 3 — Query path and API code 🟢 Local

### Query

```python
results = await search_client.search(
    search_text=query,
    vector_queries=[VectorizableTextQuery(
        text=query,
        k_nearest_neighbors=50,
        fields="content_vector",
    )],
    query_type="semantic",
    semantic_configuration_name="default",
    filter="is_active eq true",
    top=top_k,
    select=["id", "arxiv_id", "title"],
)
```

### Scoring changes

| Before | After |
|---|---|
| `bm25_score`, `bm25_rank`, `dense_similarity`, `dense_rank`, app-side RRF `final_score` | `search_score` (`@search.score`, the fused RRF score, about 0.01–0.03) and `reranker_score` (`@search.reranker_score`, 0–4) |
| `MIN_BM25_SCORE`, `MIN_DENSE_SIMILARITY`, `MAX_DENSE_DISTANCE`, `bm25_only` / `no_strong_match` modes | A single `MIN_RERANKER_SCORE` threshold (start around 1.5–2.0; tune in Phase 7). Results below it give the "No strong match" response. |

### Code

| File | Change |
|---|---|
| `app/search/azure/search_backend.py` | `AzureSearchBackend`: runs the query above and maps raw results to `SearchHit`. The `strategy` argument chooses the query shape: `BM25` → text only; `DENSE` → vector only; `HYBRID` (default) → text + vector + semantic. This keeps the Retrieval Strategy Agent usable. |
| `app/engine/search_engine.py` | `backend.search` → `MIN_RERANKER_SCORE` filter → Postgres enrichment → response. Stops calling `HybridSearchService` and Cohere; the files are deleted in Phase 6. |
| `main.py` | `/health` reports `search_backend` and `postgres_metadata`; the shutdown hook calls `backend.close()`; descriptions updated; `/agentic-search` unchanged |
| `app/services/metrics.py` | Add `search_backend_latency` and a reranker-score histogram; simplify mode labels |
| `README.md` | Document the new response fields. **API contract change** for any frontend. |

### Local tests

- **Result mapping:** canned Azure-shaped result dicts (`@search.score`, `@search.reranker_score`) map correctly to `SearchHit`, with no network calls.
- **`SearchEngine` with the fake backend and mocked metadata:**
  - below-threshold results produce "No strong match";
  - inactive docs are dropped;
  - empty results are handled.
- **API:** FastAPI `TestClient` tests for `/search` (validation, `top_k` limits) and `/health`.
- **Harness smoke run:** run `evaluation/evaluate_engine.py` against the fake backend. This only proves the harness works; the scores mean nothing.

**Exit criteria:** the full app runs locally with `SEARCH_BACKEND=fake` (Postgres and Redis from docker compose); all unit tests pass.

---

## Phase 4 — Azure setup 🔵 Azure

Phase 4 is split into seven stages. It needs no code from Phases 1–3, so it can also run in parallel with them. Each stage ends with a check, so a problem shows up where it starts instead of during indexing.

**Naming used below.** Replace these with your own values. Search and OpenAI resource names must be globally unique, lowercase, and may contain hyphens.

```bash
export SUB="<subscription-id>"
export LOC="<region>"                 # chosen in Stage 4.2
export RG="rg-hybrid-search"
export AOAI="aoai-hybrid-search-<suffix>"
export SRCH="srch-hybrid-search-<suffix>"
export EMB_DEPLOY="text-embedding-3-small"
```

---

### Stage 4.1 — Prerequisites and access

1. **Azure account.** You need a subscription where you are **Owner**, or **Contributor + User Access Administrator**. Role assignments in Stage 4.5 require that.
2. **Azure CLI.** Install it (`brew install azure-cli` on macOS), then sign in and select the subscription:
   ```bash
   az login
   az account set --subscription "$SUB"
   az account show --query "{name:name, id:id}" -o table
   ```
3. **Register resource providers.** This only needs doing once per subscription.
   ```bash
   az provider register --namespace Microsoft.Search
   az provider register --namespace Microsoft.CognitiveServices
   ```
4. **Azure OpenAI access.** Check that your subscription can create Azure OpenAI resources. Some subscription types (for example some free or student offers) restrict it.

**Check:** `az account show` prints the right subscription, and `az provider show -n Microsoft.Search --query registrationState` returns `Registered`.

---

### Stage 4.2 — Decide region, tier and budget

1. **Region.** Pick **one** region that has both:
   - Azure AI Search with the semantic ranker, and
   - Azure OpenAI with `text-embedding-3-small`.

   Confirm both in Microsoft's region and model-availability tables before choosing. Also check that `text-embedding-3-small` isn't listed for retirement; if it is, use its successor and update `EMBEDDING_DIMENSIONS`. Keeping both services in one region avoids cross-region latency and data-transfer cost.
2. **Search tier.**

   | Tier | Use for | Limits |
   |---|---|---|
   | Free | Building against the 5-doc sample | 50 MB storage, 3 indexes, one Free service per subscription. Can't be scaled up later; you would create a new service. |
   | Basic | The full arXiv dataset, and evaluation | Billed monthly whether used or not |

   **Recommendation:** use Free for the sample in Phase 5, then create a Basic service for the full dataset (Phase 5, step 5) and Phase 7.
3. **Resource group.** Tags make cost tracking easier.
   ```bash
   az group create -n "$RG" -l "$LOC" --tags project=hybrid-search env=dev
   ```
4. **Budget alert.** In the portal, go to Cost Management → Budgets and create a monthly budget on `$RG`, with email alerts at 50%, 80% and 100%.

**Check:** the resource group exists in the chosen region, and the budget alert is active.

---

### Stage 4.3 — Azure OpenAI and the embedding deployment

1. **Create the resource.** The custom domain is required for Entra ID (keyless) authentication.
   ```bash
   az cognitiveservices account create \
     -n "$AOAI" -g "$RG" -l "$LOC" \
     --kind OpenAI --sku S0 \
     --custom-domain "$AOAI"
   ```
2. **Deploy the embedding model.** `--sku-capacity` is in thousands of tokens per minute. Start small and raise it if bulk indexing hits 429 errors.
   ```bash
   az cognitiveservices account deployment create \
     -n "$AOAI" -g "$RG" \
     --deployment-name "$EMB_DEPLOY" \
     --model-name text-embedding-3-small --model-version "1" \
     --model-format OpenAI \
     --sku-name Standard --sku-capacity 120
   ```
3. **Record the endpoint:**
   ```bash
   az cognitiveservices account show -n "$AOAI" -g "$RG" --query properties.endpoint -o tsv
   ```

**Check:** one embeddings call returns a vector of length **1536**.
```bash
AOAI_KEY=$(az cognitiveservices account keys list -n "$AOAI" -g "$RG" --query key1 -o tsv)
curl -s "https://$AOAI.openai.azure.com/openai/deployments/$EMB_DEPLOY/embeddings?api-version=2024-10-21" \
  -H "api-key: $AOAI_KEY" -H "Content-Type: application/json" \
  -d '{"input":"hybrid search test"}' | python3 -c "import json,sys; print(len(json.load(sys.stdin)['data'][0]['embedding']))"
```

---

### Stage 4.4 — Azure AI Search service

1. **Create the service.** This command turns on the semantic ranker's free plan, a system-assigned managed identity, and both key and Entra ID authentication.
   ```bash
   az search service create \
     -n "$SRCH" -g "$RG" -l "$LOC" \
     --sku free \
     --semantic-search free \
     --identity-type SystemAssigned \
     --auth-options aadOrApiKey \
     --aad-auth-failure-mode http401WithBearerChallenge
   ```
   - Use `--sku basic` for the full-dataset service (Phase 5, step 5).
   - `--semantic-search standard` is pay-as-you-go and needs Basic or higher.
2. **Record the endpoint:** `https://$SRCH.search.windows.net`

**Check:** service statistics return successfully, and the semantic ranker shows `free`.
```bash
SRCH_KEY=$(az search admin-key show --service-name "$SRCH" -g "$RG" --query primaryKey -o tsv)
curl -s "https://$SRCH.search.windows.net/servicestats?api-version=2024-07-01" -H "api-key: $SRCH_KEY" | head -c 300; echo
az search service show -n "$SRCH" -g "$RG" --query "{tier:sku.name, semantic:semanticSearch, identity:identity.type}" -o table
```

---

### Stage 4.5 — Identity and permissions (RBAC)

There are two separate permission paths.

**A. Search service → Azure OpenAI.** The index vectorizer calls embeddings at query time, so the Search service's identity needs access to Azure OpenAI.
```bash
SRCH_MI=$(az search service show -n "$SRCH" -g "$RG" --query identity.principalId -o tsv)
AOAI_ID=$(az cognitiveservices account show -n "$AOAI" -g "$RG" --query id -o tsv)
az role assignment create \
  --assignee-object-id "$SRCH_MI" --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" --scope "$AOAI_ID"
```

**B. You (local development) → both services.** This is only needed if the app will use `DefaultAzureCredential` instead of keys. It's recommended, because the same code then works with managed identity in Phase 8.
```bash
ME=$(az ad signed-in-user show --query id -o tsv)
SRCH_ID=$(az search service show -n "$SRCH" -g "$RG" --query id -o tsv)
az role assignment create --assignee "$ME" --role "Search Service Contributor"     --scope "$SRCH_ID"  # create/update index
az role assignment create --assignee "$ME" --role "Search Index Data Contributor"  --scope "$SRCH_ID"  # upload/query docs
az role assignment create --assignee "$ME" --role "Cognitive Services OpenAI User" --scope "$AOAI_ID"  # embeddings at ingestion
```

**Check:**
- `az role assignment list --scope "$AOAI_ID" -o table` shows the Search identity.
- `az role assignment list --scope "$SRCH_ID" -o table` shows your user.

Role assignments can take a few minutes to take effect.

---

### Stage 4.6 — Fill in local configuration

Phase 1 already added the settings, `.env.example` and the SDKs. This stage only fills in the real values.

1. **Fill in `.env`** (already git-ignored):
   ```dotenv
   SEARCH_BACKEND=azure
   AZURE_SEARCH_ENDPOINT=https://<srch-name>.search.windows.net
   AZURE_SEARCH_INDEX=hybrid-search-documents
   AZURE_SEARCH_API_KEY=            # leave empty to use Entra ID (DefaultAzureCredential)
   AZURE_OPENAI_ENDPOINT=https://<aoai-name>.openai.azure.com/
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
   AZURE_OPENAI_API_VERSION=2024-10-21
   AZURE_OPENAI_API_KEY=            # leave empty to use Entra ID
   ```
2. **Keep secrets out of git.** Run `git check-ignore .env`; it should print `.env`. Never paste keys into code, docs or chat.

**Check:** `scripts/check_azure_connectivity.py` does three things using only `.env`:
- lists indexes on the Search service (expect an empty list);
- embeds one string (expect 1536 dimensions);
- prints which auth method was used (key or Entra ID).

---

### Stage 4.7 — Phase 4 sign-off

- [ ] Subscription selected and resource providers registered (4.1)
- [ ] Region confirmed for both services; resource group created; budget alert set (4.2)
- [ ] Azure OpenAI resource created and the embedding deployment returns 1536-dim vectors (4.3)
- [ ] Search service created, semantic ranker on the free plan, managed identity on (4.4)
- [ ] Search identity has **Cognitive Services OpenAI User** on Azure OpenAI; your user has data-plane roles if using Entra ID (4.5)
- [ ] `.env` filled in and the connectivity script passes (4.6)
- [ ] Endpoints, region and tier written into the **Decisions** table at the top of this document

**Exit criteria:** every box above is ticked. Phase 5 can then create the index without any further portal work.

**Rollback:** `az group delete -n "$RG"` removes everything created in Phase 4.

---

## Phase 5 — Integration on Azure 🔵 Azure

1. **Create the index:** run `python scripts/create_azure_index.py` with `SEARCH_BACKEND=azure`. Confirm the index appears in the portal with the expected fields.
2. **Index the 5-doc sample** (Free tier): run `scripts/index_documents_azure.py --rebuild`. The index count should match Postgres; spot-check the documents in Search Explorer.
3. **Live API smoke tests** with `SEARCH_BACKEND=azure`:
   - exact-keyword query
   - paraphrase / synonym query
   - deactivated document must not appear
   - empty query → 400
   - nonsense query → "No strong match"
4. **Integration tests:** run `pytest -m azure` (real calls, small fixtures).
5. **Full dataset:**
   - Create a **Basic** search service (Stage 4.4 with `--sku basic`) and point `.env` at it.
   - Run `create_azure_index.py`, then index all 7,198 docs.
   - Raise the embedding deployment's capacity if you hit 429 errors.

**Exit criteria:** `/search` returns enriched, semantically reranked results from Azure for the full dataset.

---

## Phase 6 — Cutover and cleanup 🟢 Local

Do this only after Phase 5 passes. Until then, the old stack stays runnable for comparison.

**Delete**

- **OpenSearch:** `app/services/bm25_service.py`, `app/services/opensearch_index_service.py`, `app/core/opensearch_client.py`, `app/core/opensearch_sync_client.py`
- **FAISS and local embeddings:** `app/services/faiss_service.py`, `app/services/vector_service.py`, `app/core/vector_store.py`, `app/services/embedding_service.py`
- **Fusion and rerank:** `app/services/hybrid_service.py`, `app/services/CohereReranker.py`
- **Scripts:** `retrieval/bm25_retriever.py` (and the old `evaluation/evaluate.py`, which depends on it), `init_opensearch.py`, `scripts/build_faiss_index.py`, `scripts/build_faiss_flat_index.py`, `scripts/index_documents_opensearch.py`
- **Old manual tests:** `test_opensearch_bm25.py`, `test_opensearch_connection.py`, `test_opensearch_indexing.py`, `test_faiss_dense.py`, `test_hnsw_vs_flat.py`, `test_hybrid_search.py`, `test_hybrid_search_engine.py`
- **Data:** `data/faiss.index`, `data/faiss_flat.index`, `data/faiss_docstore.json`

**Update**

- `requirements.txt`: remove `opensearch-py`, `faiss-cpu`, `rank-bm25`, `cohere`, `sentence-transformers`.
- `docker-compose.yml`: remove the `opensearch`, `search_init` and dashboards services and the `opensearch-data` volume; update `ingestion-worker` dependencies and environment.
- `app/core/config.py` and `.env`: remove the `OPENSEARCH_*`, `FAISS_*`, `COHERE_API_KEY` and BM25/dense threshold settings; default `SEARCH_BACKEND=azure`.
- **Redis:** the query-embedding cache is no longer needed. Either repurpose Redis as a short-TTL search-response cache or remove it.
- **Docs:** `README.md`, `Design.md` and `docs/app-flow.md` get the new architecture and rationale.
- **Fakes:** keep them for tests only.

**Exit criteria:** searching the codebase for `opensearch|faiss|cohere` finds nothing outside docs and git history; `pytest` passes; `docker compose up` starts without OpenSearch.

---

## Phase 7 — Verify and tune 🔵 Azure

1. **Evaluate.** Run `evaluation/evaluate_engine.py` against Azure and compare with `baseline_opensearch_faiss.json` (precision@5, recall@5, MRR, latency).
2. **Tune:**
   - `k_nearest_neighbors`
   - `MIN_RERANKER_SCORE`
   - `efSearch`
   - the title weight, through a scoring profile
3. **Load test.** Run `load_test.js` and watch p95 latency, which the semantic ranker increases.

**Exit criteria:** relevance at least matches the baseline; p95 latency is acceptable; results are saved in `evaluation/results/`.

---

## Phase 8 — Deploy 🔵 Azure

| Component | Azure service |
|---|---|
| FastAPI API, ingestion worker | Azure Container Apps (images in Azure Container Registry) |
| PostgreSQL | Azure Database for PostgreSQL Flexible Server |
| Redis (if kept) | Azure Managed Redis |
| MinIO datasets | Azure Blob Storage (or keep MinIO as a container) |
| Prometheus / Grafana | Azure Monitor managed Prometheus + Azure Managed Grafana |
| Secrets | Key Vault + managed identity (no keys in `.env` in the cloud) |

---

## Trade-offs accepted

- **Less explainability:** separate BM25 and dense scores and the custom fallback modes go away.
- **Cost:** semantic ranker requests, Azure OpenAI embedding calls, and the Basic tier (billed monthly regardless of usage).
- **Lock-in:** the search layer becomes Azure-specific. The interfaces make a future swap easier.
- **Learning value:** the in-house RRF/HNSW work is replaced by managed features. The git history keeps the original implementation.

## Effort estimate

| Phase | Estimate |
|---|---|
| 0 Prepare and baseline | Half a day |
| 1 Local foundations | Half a day |
| 2 Index and ingestion code | Half a day to one day |
| 3 Query and API code | Half a day to one day |
| 4 Azure setup | Half a day to one day |
| 5 Integration | Half a day |
| 6 Cutover | Half a day |
| 7 Verify and tune | Half a day or more |
| 8 Deploy | One day |

## References

- [Azure AI Search naming rules (document keys)](https://learn.microsoft.com/en-us/rest/api/searchservice/naming-rules)
- [Enable or disable semantic ranker](https://learn.microsoft.com/en-us/azure/search/semantic-how-to-enable-disable)
- [Semantic ranking in Azure AI Search](https://learn.microsoft.com/azure/search/semantic-ranking)
- [Azure AI Search pricing](https://azure.microsoft.com/pricing/details/search)
