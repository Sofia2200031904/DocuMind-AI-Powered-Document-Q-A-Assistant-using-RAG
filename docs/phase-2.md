# Phase 2: genuine LCEL answers with citations

Phase 2 adds generation to the existing retrieval foundation. The `query` command
still returns passages. The new `ask` command returns an answer, sources, and a
refused flag. This remains a CLI application; HTTP routes and React come later.

## Data flow

```text
question string
  | RunnableLambda: validate and normalize
  | RunnablePassthrough.assign: RetrievalService -> embeddings -> FAISS -> threshold
  | RunnableBranch
  +-- no evidence -> refusal (no model call)
  +-- evidence
        | RunnableLambda: format JSON context with S1, S2, ... IDs
        | RunnablePassthrough.assign(draft =
        |     ChatPromptTemplate | injected chat model | PydanticOutputParser)
        | RunnableLambda: validate IDs and attach source metadata
        v
    GroundedAnswer(answer, sources, refused)
```

These are actual composed LangChain Runnables, not an LLM invocation described as
a chain. The generation subchain receives the same retrieved state that citation
validation uses. The source mapping is local to each invocation.

## Run on this workstation

From the project root in PowerShell:

```powershell
# Start the downloaded portable runtime; safe to call when already running.
powershell -ExecutionPolicy Bypass -File .\scripts\start-local-model.ps1
$env:HF_HOME = "$PWD\.model-cache"
$env:HF_HUB_OFFLINE = '1'
$env:OLLAMA_MODEL = 'qwen2.5:3b'
cd backend
..\.venv313\Scripts\python.exe -m app.cli ask "How many days of paid annual leave do employees receive?"
```

If PowerShell is already in `backend`, use `cd ..` once before the block above.
`HF_HUB_OFFLINE=1` uses the embedding model cached during Phase 1 and avoids repeated
network checks. The LLM also runs locally. Ollama must stay running while asking
questions. The startup script runs it in the background on loopback only.

Run the real-model demonstration and offline tests from backend:

```powershell
..\.venv313\Scripts\python.exe -m app.demo_phase2
..\.venv313\Scripts\python.exe -m pytest -q
```

The demonstration asks four questions, including an out-of-scope question. It calls
the real embedding model, persisted FAISS store, and local LLM. It has no canned
answers or mock model. It is a smoke test, not the Phase 11 evaluation harness.

## Installation on another machine

Install dependencies from the repository root:

```powershell
uv --cache-dir .uv-cache pip install --python .venv313/Scripts/python.exe -r backend/requirements.txt
```

Install [Ollama for Windows](https://docs.ollama.com/windows) and run
`ollama pull qwen2.5:3b`. The local model used here is
[Qwen2.5 3B](https://ollama.com/library/qwen2.5:3b), approximately 1.9 GB of weights.
Alternatively, extract the official portable Windows AMD64 archive from
[Ollama releases](https://github.com/ollama/ollama/releases) into `.local/ollama/`,
start it with the provided script, and run `.local\ollama\ollama.exe pull qwen2.5:3b`.
The portable setup places model weights in `.local/models/`. Generated runtimes,
model weights, and runtime logs are Git-ignored.

The example configuration retains `OLLAMA_MODEL=llama3.1` from the original brief;
this workstation uses `qwen2.5:3b` for a smaller local download. Set OLLAMA_MODEL to
the model you actually pulled. Changing this setting does not change the RAG chain.
The default LLM HTTP timeout is 120 seconds; slow CPUs may need a larger
LLM_TIMEOUT_SECONDS (up to 600). Model startup can take longer than later queries.

## New files and why they exist

| File | Responsibility and dependencies | Architectural reason / interview explanation |
| --- | --- | --- |
| `app/models/answers.py` | Pydantic schemas for model draft, application citation, and final result. Used by parser, model helper and RAG service. | Separates untrusted model output from trusted source records. “The model selects IDs; my application owns citation metadata.” |
| `app/services/rag_service.py` | LCEL composition using LangChain prompts, runnables and Pydantic parser. Accepts a retriever and model; uses answer/document records. | Keeps orchestration independent of provider setup. “I compose retrieval, prompt formatting, inference, parsing, and citations as observable LangChain steps.” |
| `app/services/local_model.py` | Creates ChatOllama with model, URL, timeout, temperature and JSON schema from Settings. Depends on langchain-ollama and AnswerDraft. | A small Phase 2 composition helper. Full OpenAI/Ollama service abstraction is Phase 3. “Vendor configuration stays outside the RAG chain.” |
| `app/demo_phase2.py` | Composes real services and runs four questions. Uses Settings, embeddings, FAISS, retrieval, local model and RAG. | Reproducible integration smoke test. “I demonstrate the actual chain separately from mocked unit tests.” |
| `tests/test_rag.py` | pytest tests with controlled retriever/model doubles and real LCEL execution. | Verifies prompt delivery, source selection, invalid output, refusal and error behavior offline. “I test mechanics deterministically without confusing mock outputs with semantic evaluation.” |
| `scripts/start-local-model.ps1` | Starts portable Ollama hidden, sets project-local model storage, checks readiness, and writes local runtime logs. Uses native PowerShell process and HTTP commands. | Makes local development repeatable without installing a Windows service. “My development runtime is separate from application logic.” |
| `docs/phase-2.md` | This learning/setup guide; no runtime dependencies. | Documents data flow and limitations so the design can be explained and reproduced. |

Updated files: `cli.py` adds `ask`, composes services, and provides an actionable
LLM-unavailable error; `config.py` owns Ollama settings and timeout validation;
`requirements.txt` explicitly declares LangChain/core/Ollama dependencies;
`.env.example` documents settings; `.gitignore` excludes the local runtime;
`README.md` advertises Phase 2 and links to this guide. Their existing Phase 1
responsibilities remain documented in `phase-1.md`.

## Grounding and citation rules

The prompt requires evidence-only answers and treats document instructions as
untrusted data. An empty retrieval result bypasses generation. The model produces
an AnswerDraft JSON object containing answer, evidence_ids, and refused. The
Pydantic parser rejects unexpected fields or invalid types. Malformed drafts,
missing citations, or IDs outside the retrieved set produce the standard refusal.
Duplicates are removed. Document names, pages, sections, chunk IDs and similarity
scores are copied from retrieved records, never from model-provided metadata.

This independently enforces the retrieval gate and citation provenance. It does
**not** prove that every generated claim follows from its cited passage. A model
can still produce unsupported text despite valid IDs; prompt injection and
entailment evaluation need further hardening. We do not claim perfect hallucination
prevention. Provider/network errors propagate as failures, not evidence refusals.

Retrieval uses the unchanged 0.65 threshold. Relevant questions below that threshold
can be refused; we do not silently lower the threshold to make demonstrations pass.
There is no history or follow-up memory yet. The local model has an 8192-token
context setting and a 1024-token output cap; comprehensive token budgeting and
history trimming belong to Phase 6. Keep Phase 1 chunk/top-k defaults for now.

## Interview narrative

“I implemented a genuine LCEL pipeline that reuses the independently tested
retriever. It branches before generation when no evidence passes the threshold.
For supported requests, it formats context, applies a grounded prompt, calls an
injected chat model and parses a strict schema. The model selects evidence IDs;
I validate them and construct citations from stored metadata. This guarantees
source provenance, while factual entailment remains a separate evaluation concern.”

## Next phase

Phase 3 adds the full OpenAI/Ollama provider abstraction with configuration-based
selection. Phase 2 intentionally does not add tools, memory, audit, API routes or
frontend. Continue only after the user confirms.

References: [ChatOllama integration](https://docs.langchain.com/oss/python/integrations/chat/ollama),
[Ollama structured output](https://docs.ollama.com/capabilities/structured-outputs).
