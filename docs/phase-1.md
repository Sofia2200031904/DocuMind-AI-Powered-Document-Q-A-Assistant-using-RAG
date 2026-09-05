# Phase 1 walkthrough

## Project tree

```text
.
├── .env.example
├── .gitignore
├── README.md
├── docs/
│   └── phase-1.md
└── backend/
    ├── requirements.txt
    ├── pytest.ini
    ├── app/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── cli.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── documents.py
    │   ├── schemas/
    │   │   └── __init__.py
    │   └── services/
    │       ├── __init__.py
    │       ├── document_service.py
    │       ├── embedding_service.py
    │       ├── vector_store.py
    │       └── retrieval_service.py
    ├── tests/
    │   ├── test_chunking.py
    │   └── test_retrieval.py
    └── data/
        ├── sample_docs/
        │   ├── employee_handbook.txt
        │   ├── university_policy.txt
        │   ├── api_documentation.txt
        │   └── engineering_guidelines.txt
        └── vector_store/                 # generated and Git-ignored
```

The virtual environment and package/model caches are generated and Git-ignored.

## File-by-file explanation

Each entry covers purpose, responsibility, dependencies, collaboration, GenAI
concept, architectural reason, and a sentence you can use in an interview.

### app/config.py

Owns configuration and rejects invalid sizes, overlap, top-k, and score thresholds.
Uses pathlib, Pydantic validation and pydantic-settings for environment loading.
The CLI constructs Settings and passes it into document/retrieval services.
This makes retrieval parameters explicit instead of burying them in model calls.
Central validation avoids inconsistent behavior across future API and CLI clients.
Interview: “I made chunking and retrieval behavior configurable and validated
settings before processing documents.”

### app/models/documents.py

Owns typed Chunk, DocumentMetadata, and RetrievalResult records. Uses Pydantic.
The parser creates records; vector storage serializes them; retrieval returns them.
It demonstrates provenance: evidence must retain its original source throughout RAG.
Shared records prevent loosely structured dictionaries from drifting between layers.
Interview: “Each vector maps to typed source metadata so citations can be generated
from retrieved records rather than invented by an LLM.”

### app/services/document_service.py

Owns filename cleanup, size/type validation, UTF-8/PDF extraction, normalization,
and the separately testable chunk_pages function. Uses pypdf for PDF extraction,
LangChain's RecursiveCharacterTextSplitter, standard-library hashing/time/UUIDs,
Settings, and domain records. CLI supplies bytes and receives document plus chunks.
Demonstrates ingestion, overlap, and source preservation. Parsing stays independent
of embedding inference and storage, making failures and future OCR extensions local.
Interview: “I split per page and attach document and chunk IDs before embedding,
so retrieval never loses the provenance of the original evidence.”

### app/services/embedding_service.py

Owns an EmbeddingProvider Protocol, Sentence Transformer implementation, and factory.
Uses typing, NumPy, Sentence Transformers and Settings. CLI obtains the provider;
ingestion and retrieval use only its embed interface and identity. Demonstrates
local dense embeddings, normalized vectors, and matching query/document spaces.
The model loads only when needed, not when importing the module. Rejects silent
token truncation. Provider-specific code is isolated for later replacement.
Interview: “I isolated embedding generation behind a protocol so the retriever
does not depend on a specific embedding vendor.”

### app/services/vector_store.py

Owns FAISS IndexFlatIP, normalization, snapshot persistence, duplicate detection,
metadata loading, and similarity search. Uses FAISS, NumPy, filelock, JSON, pathlib,
os and UUIDs plus domain records. CLI adds vectors; RetrievalService searches them.
Demonstrates cosine nearest-neighbor retrieval and a vector-to-source mapping.
JSON avoids pickle deserialization; snapshot publication keeps metadata and vectors
together. A process lock prevents overlapping writers from overwriting each other.
Interview: “I persisted vector and metadata snapshots and atomically switched the
active pointer, so an interrupted write leaves the previous index usable.”

### app/services/retrieval_service.py

Owns question validation, question embedding, top-k defaults, and threshold
selection. Depends on the provider protocol, VectorStore, Settings and result model.
CLI delegates retrieval here; the later LCEL chain will reuse it. Demonstrates
semantic retrieval and evidence filtering independent of prompting. This keeps
retrieval logic out of routes and allows deterministic tests.
Interview: “I separated retrieval from generation and exposed both source metadata
and cosine scores rather than hiding them inside a chat endpoint.”

### app/cli.py

Owns command parsing and composition of services for ingest, query and documents.
Uses argparse, pathlib, logging, JSON and the application services. It bounds reads
before parsing, prints machine-readable results, and returns a failure exit code.
Demonstrates the complete retrieval portion of RAG without needing an LLM or UI.
This makes the foundation independently runnable and debug-friendly.
Interview: “I validated ingestion and retrieval through a CLI before integrating
generation, which made it easier to isolate retrieval quality problems.”

### app/__init__.py, models/__init__.py, services/__init__.py, schemas/__init__.py

These four package markers have no external dependencies or business logic.
They define importable application, domain, service, and future API-schema boundaries.
Schemas is intentionally empty until the API phase. They demonstrate separation
of concerns rather than a model algorithm. Interview: “I kept domain records,
services, and transport schemas in separate packages.”

### tests/test_chunking.py

Owns offline parsing and chunking checks, including a generated PDF, empty and
invalid input, UTF-8 failure, size limits, overlap, and metadata. Uses pytest,
pypdf, io and the actual document service. It tests preprocessing independently
of an embedding download. Architecture benefit: an extraction regression cannot
hide behind plausible retrieval results. Interview: “I tested source preservation
and malformed inputs before connecting generation.”

### tests/test_retrieval.py

Owns real-FAISS tests with a deterministic embedding double. Uses pytest, NumPy,
configuration and ingestion/retrieval/storage services. Checks ranking, top-k,
thresholds, empty stores, duplicates, reloads, model/dimension mismatch and failed
snapshot publication. Demonstrates that retrieval and persistence can be tested
without paid models. It does not measure real-model semantic accuracy.
Interview: “I used deterministic embeddings to test retrieval mechanics offline,
then separately checked the actual embedding model through the CLI.”

### backend/pytest.ini

Owns test discovery and application import path. Used by pytest, no Python imports.
Makes offline service tests reproducible from backend. No direct GenAI algorithm.
Interview: “I made the service test command independent of API credentials.”

### backend/requirements.txt

Owns Phase 1 dependency declarations: Pydantic settings, LangChain text splitting,
Sentence Transformers, FAISS, NumPy, PDF parsing, file locking, and pytest.
The installer reads it; app modules consume these libraries. Bounded major versions
reduce accidental breaking upgrades, but this is not an exact dependency lock.
Interview: “I kept the initial environment scoped to the ingestion and retrieval
components; generation and API dependencies arrive in later phases.”

### backend/data/sample_docs/employee_handbook.txt

Synthetic leave and remote-work policy; no dependencies. CLI indexes it for policy
retrieval checks. Demonstrates document-grounded evidence without confidential data.
Interview: “I used fictional HR policies to verify source retrieval safely.”

### backend/data/sample_docs/university_policy.txt

Synthetic library and registration policies; no dependencies. Provides a second
domain to distinguish relevant from irrelevant candidates. Interview: “I included
multiple domains so semantic retrieval had to choose between different sources.”

### backend/data/sample_docs/api_documentation.txt

Synthetic rate-limit and pagination rules; no dependencies. Exercises technical
facts and numbers. Interview: “My corpus included API documentation to test
retrieval beyond ordinary prose.”

### backend/data/sample_docs/engineering_guidelines.txt

Synthetic review and incident-response policies; no dependencies. Adds a related
but distinct workplace document. Interview: “I included similar workplace sources
to expose ambiguous retrieval, not just obviously unrelated documents.”

### .env.example

Owns documented nonsecret configuration examples, consumed by Settings after copying
to .env. Makes model and retrieval settings visible and reproducible. No imports.
Interview: “I kept model selection and retrieval tuning outside source code.”

### .gitignore

Owns Git exclusions for secrets, generated indexes, caches and environments. No
imports. Keeps local document content and large generated artifacts out of history.
Interview: “I tracked source and synthetic fixtures, not local vector stores or keys.”

### README.md

Owns setup commands, scope, architecture, operational limits and references.
No runtime dependencies; guides users into CLI and tests. Explains retrieval versus
generation honestly. Interview: “I documented what was actually implemented and
the boundaries that still needed production hardening.”

### docs/phase-1.md

This learning guide owns the tree and rationale for every source file, fixture,
configuration and document. No runtime imports. It complements the concise README
with interview preparation. Interview: “I can explain each service's responsibility
and how data moves through the system instead of treating RAG as a black box.”

## Data flow and concepts

1. The CLI reads at most the upload limit plus one byte; the parser validates bytes.
2. PDF text is extracted per original page. TXT produces one logical text unit.
3. Recursive splitting preserves source fields and assigns unique chunk IDs.
4. Sentence Transformers maps each chunk into a dense vector locally on CPU.
5. Unit normalization makes FAISS inner product equivalent to cosine similarity.
6. FAISS stores vectors; JSON records preserve text and source information.
7. A question uses the same model; FAISS finds the highest-scoring vectors.
8. Retrieval returns only candidates above the configured threshold with original
   text, source metadata and scores. No answer is generated in this phase.

An embedding is a numerical representation of meaning, not stored knowledge in
human-readable form. Chunking balances focused retrieval against lost context.
Overlap can preserve information near boundaries. top-k limits candidate count.
A threshold removes weak matches but cannot establish factual entailment. The next
phase must use retrieved evidence to constrain generation and build citations.

## Interview narrative

“I built the retrieval foundation of DocuMind with a validated PDF/TXT ingestion
pipeline. I preserve page-level provenance during recursive chunking, embed chunks
locally using Sentence Transformers, and use normalized FAISS inner-product search
for cosine ranking. I store metadata separately as JSON and publish snapshots
atomically. The embedding protocol keeps vendors out of retrieval logic. I tested
mechanics offline with deterministic vectors and exercised the real model separately.
The similarity threshold filters candidates; it is not a claim of answer correctness.”

## Phase 2 boundary

After confirmation: LCEL composition, context formatting, grounded prompt template,
output parsing, citations derived from selected metadata, and three demonstrated
questions. The full provider abstraction is Phase 3. Tools, memory, audit, API,
frontend, broad evaluation and CI are intentionally still pending.

## Observed verification — September 5, 2026

Environment: Python 3.13.7, sentence-transformers 5.7.0, faiss-cpu 1.15.0,
LangChain text splitters 1.1.2. Model: sentence-transformers/all-MiniLM-L6-v2.

The actual CLI indexed all four TXT samples, producing four chunks/vectors.
The short samples each fit in one chunk; long-document overlap is covered in tests.
Query ran from the persisted store with HF_HUB_OFFLINE=1 after the initial model download.

Question: `How many days of paid annual leave do employees receive?`

Raw top-three results using `--top-k 3 --threshold -1`:

| Rank | Source | Cosine score | Retrieved text excerpt |
| --- | --- | --- | --- |
| 1 | employee_handbook.txt | 0.6653492451 | Employees receive 20 days of paid annual leave per calendar year. |
| 2 | university_policy.txt | 0.1681992859 | Students may borrow up to eight books for 21 days. |
| 3 | api_documentation.txt | 0.1164481938 | The Harbor API allows 120 requests per minute per access token. |

Each result includes actual document/chunk UUIDs, full chunk text, source, page=null,
and section=Unknown. The configured 0.65 threshold retains only the first match.
Scores may change with model/library revisions. These are observed retrieval scores,
not evaluation accuracy or generated answers.

Offline pytest result: **13 passed in 17.49s**. The initial sandboxed attempt passed
nine parsing tests but could not create temporary directories for four retrieval
tests. Rerunning with temporary-directory access passed all tests. Test coverage
includes actual PDF extraction, metadata/overlap, malformed inputs, FAISS ranking,
persistence, threshold filtering, model mismatch, and interrupted snapshot writes.
