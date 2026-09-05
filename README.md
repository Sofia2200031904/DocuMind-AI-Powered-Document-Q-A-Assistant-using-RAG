# DocuMind — Phase 1

Document ingestion and semantic retrieval using local Sentence Transformers and
persistent FAISS. **Phase 1 only:** this repository does not yet generate answers,
expose HTTP routes, or contain a frontend. All four sample documents are fictional.

Keyword search misses paraphrases. Dense embeddings place related text near each
other numerically, allowing a question to retrieve passages without identical words.
Retrieval finds candidate evidence; it does not prove that the evidence answers a question.

```text
PDF/TXT bytes -> validation -> text per page -> recursive character chunks
                                                   |
                                       metadata + UUIDs
                                                   |
                                     Sentence Transformers (CPU)
                                                   |
                                      normalized float32 vectors
                                                   |
                                        FAISS IndexFlatIP
                                                   ^
question -> same embedding model -> normalized vector
                                                   |
                            top-k -> cosine threshold -> text + metadata + score
```

## Run on Windows PowerShell

Run from the repository root. Python 3.11+ is required; Python 3.13 was selected for
the development environment. First installation requires internet for packages
and the embedding model. No API key, paid service, or Ollama is needed in Phase 1.

```powershell
py -3.13 -m venv .venv313
.\.venv313\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
$env:HF_HOME = "$PWD/.model-cache"
Set-Location backend
..\.venv313\Scripts\python.exe -m app.cli ingest data/sample_docs
..\.venv313\Scripts\python.exe -m app.cli documents
..\.venv313\Scripts\python.exe -m app.cli query "How many days of paid annual leave do employees receive?"
..\.venv313\Scripts\python.exe -m pytest
```

If pip bootstrapping fails and uv is available (as on this workstation):

```powershell
uv --cache-dir .uv-cache venv --python 3.13 .venv313
uv --cache-dir .uv-cache pip install --python .venv313/Scripts/python.exe -r backend/requirements.txt
```

To inspect raw rankings even when scores fall below the configured threshold:

```powershell
# From backend; diagnostic override only.
..\.venv313\Scripts\python.exe -m app.cli query "How many days of paid annual leave do employees receive?" --top-k 3 --threshold -1
```

To index another file, pass its local path to `ingest`. Paths are a trusted CLI input;
the parser accepts bytes and never derives an output path from an uploaded filename.
PDF must contain extractable text; OCR and encrypted PDFs are unsupported. TXT must
be UTF-8. Size is limited to 20 MiB by default. CLI failures return exit code 1.

## Configuration and persistence

`.env` is loaded from the repository root regardless of your current directory.
See `.env.example`. Chunk sizes and overlap are measured in **characters**, not
tokens. Recursive splitting prefers paragraphs, lines, sentences, then words.
Overlap is a target, not a guarantee across natural boundaries. Pages never mix.
TXT page numbers are null; section is `Unknown` because there is no reliable
section parser. The embedding service rejects texts exceeding the model's token
limit rather than silently truncating them; lower CHUNK_SIZE if necessary.

FAISS uses exact inner-product search over normalized vectors: this equals cosine
similarity. Larger scores are better, with a theoretical range of -1 to 1.
The 0.65 threshold is an initial configuration, **not a calibrated confidence**.
Empty results mean no candidate passed the threshold; answer refusal comes later.

The index stores vectors in `.faiss` files and chunk text/document records in JSON.
A process lock prevents concurrent writes from losing updates. An atomic CURRENT
pointer publishes a completed snapshot. Failed writes leave the prior snapshot
readable. Old snapshots are retained, so disk use grows; compaction is future work.
Metadata stores the model identity and rejects incompatible reuse. Changing model
or embedding dimensions requires a fresh VECTOR_STORE_PATH and reingestion.
Model names are recorded, but upstream model revisions are not pinned yet.
Identical filename + content is skipped on reingestion; changed content is appended
as a new document version. There is no delete/update operation in Phase 1.

Only read trusted locally generated FAISS files. Documents and metadata are stored
unencrypted locally. This is a production-oriented foundation, not a completed or
internet-ready production service. Authentication, API limits, audit, deployment,
and operational hardening remain for subsequent phases.

## Learning guide and checks

See [docs/phase-1.md](docs/phase-1.md) for the full tree, responsibilities,
dependencies, architecture rationale, and interview explanations for every file.
Tests use deterministic embedding doubles with real FAISS and require no model
download or API key. A real-model CLI run is a separate integration check.

Verified September 5, 2026: **13 tests passed**. The actual MiniLM model indexed all
four samples. The leave-policy query retrieved employee_handbook.txt first at
cosine similarity **0.665349**, above the default 0.65 threshold. Full observed
rankings and test details are recorded in the learning guide.

## Next phase

Phase 2 adds a genuine LangChain LCEL retrieval/context/prompt/model/parser chain,
grounded prompt and programmatic citations, then demonstrates three questions.
Implementation waits for user confirmation. Provider abstraction, tools, memory,
context budgeting, audit, APIs, React, evaluation, and CI follow the requested phases.

## Technical references

- [Sentence Transformers encode API](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html)
- [FAISS indexes and cosine similarity](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)
- [FAISS persistence](https://github.com/facebookresearch/faiss/wiki/Index-IO%2C-cloning-and-hyper-parameter-tuning)
