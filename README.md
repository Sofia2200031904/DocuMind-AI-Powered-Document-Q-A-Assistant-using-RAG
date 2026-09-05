# 🧠 DocuMind

DocuMind is a document-grounded Q&A assistant. Upload PDF or TXT files, ask natural-language questions, and receive answers supported by retrieved document evidence and source citations.

[Live Frontend](https://docu-mind-ai-powered-document-q-a-assistant-using-pa5z83l48.vercel.app/) · [Backend Health](https://documind-ai-powered-document-q-a-rnfd.onrender.com/health) · [GitHub](https://github.com/Sofia2200031904/DocuMind-AI-Powered-Document-Q-A-Assistant-using-RAG) · [License](#license)

> The frontend is deployed on Vercel and the FastAPI backend is deployed on Render. The backend root URL may show `404 Not Found`; use the `/health` link to verify that the API is running.

## 📸 Screenshots

Add screenshots to `docs/images/` and embed them here:

```markdown
![DocuMind chat interface](docs/images/chat.png)
```

## 🎯 Overview

DocuMind turns documents into a searchable knowledge base. It validates uploads, extracts text, preserves page metadata, creates semantic embeddings, retrieves relevant chunks, and generates a grounded response.

## ✨ Features

### What you can ask

DocuMind supports document questions and general conversation. Generated answers require a working model provider; the deployed OpenAI configuration currently needs API credits before these answers can be tested successfully.

| Capability | Example message |
|---|---|
| Document summary | `Give me a summary of the document` |
| Find information in an uploaded file | `List the certificates mentioned in this document` |
| Explain a term in context | `What does this word mean in the document?` |
| Follow up on an answer | `Explain the second point in simpler words` |
| General knowledge | `What is machine learning?` |

Document answers can include source references. General answers are instructed to identify themselves as general knowledge. Missing document evidence can produce a refusal. Answer accuracy is not guaranteed; check important claims against the original document.

### Built-in messages that do not call the AI API

The following exact phrases receive preset friendly responses without consuming API credits, provided the backend starts successfully:

| Messages | Response type |
|---|---|
| `hi`, `hello`, `hey`, `good morning`, `good afternoon`, `good evening` | Greeting and invitation to upload a document |
| `thanks`, `thank you`, `thx` | Friendly acknowledgement |
| `how are you`, `how are you doing`, `who are you`, `tell me about yourself`, `about yourself` | DocuMind introduction |
| `what can you do`, `help`, `what do you do` | Description of document assistance capabilities |

Capitalization and trailing `!`, `?`, `.`, or `,` are ignored. These are exact phrase matches, not a general offline chatbot. For example, `How are you, can you tell me about yourself?` is a combined question and still uses the AI API.

### Current limitations

- OpenAI requests currently fail with `429 insufficient_quota` when the account has no API credits. Creating another key does not fix the credit balance.
- Follow-ups receive only the most recent six conversation messages. Retrieval still searches the current question, so vague references may miss relevant evidence.
- Chat history is stored in the browser. Separate conversations and document isolation are not implemented; the New chat button currently clears the visible question and answer only.
- A visual document preview is not implemented.
- Uploaded files/index data on the current Render setup can be lost after a redeploy; upload the document again if needed.

### Other implemented features

- PDF and UTF-8 TXT upload with validation
- Semantic retrieval using Sentence Transformers and FAISS
- Grounded answers through a LangChain LCEL pipeline
- Source document and page citations
- Refusal when evidence does not support an answer
- Purple, notebook-style web interface
- Browser chat history with clickable previous questions
- CLI, FastAPI, Docker, Render, and Vercel configuration

## 🏗️ Architecture

```text
React Frontend → FastAPI API → Document service → Embeddings → FAISS
                                             ↓
                                      Retriever → Prompt → Ollama → Answer + sources
```

## 🔄 How RAG Works

1. Upload bytes are validated and parsed.
2. Text is split into overlapping chunks with provenance metadata.
3. Chunks are embedded and stored in a persistent FAISS index.
4. The question is embedded using the same model.
5. Similar chunks above the confidence threshold are retrieved.
6. The language model answers only from those chunks.
7. Application-owned metadata is attached as citations.

## 🛠️ Tech Stack

Python 3.13 · FastAPI · LangChain LCEL · Ollama · Sentence Transformers · FAISS · React · Vite · Docker · Render · Vercel

## 📁 Project Structure

```text
backend/app/       CLI, API, models, and RAG services
backend/tests/     Automated tests
backend/data/      Sample documents and local vector storage
frontend/          React/Vite web application
docs/              Phase documentation and learning notes
render.yaml        Render deployment configuration
```

## ⚙️ Installation

From the repository root:

```powershell
py -3.13 -m venv .venv313
.\.venv313\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm install
```

## 🔐 Environment Variables

Copy `.env.example` to `.env` and configure:

```text
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_PATH=backend/data/vector_store
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434
```

Never commit `.env`, API keys, or private credentials.

## 🚀 Running the Application

Start Ollama and the model:

```powershell
ollama serve
ollama pull llama3.1
```

Start the backend in PowerShell window 1:

```powershell
& ".\.venv313\Scripts\python.exe" -m uvicorn app.api:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Start the frontend in PowerShell window 2:

```powershell
cd frontend
$env:VITE_API_URL="http://127.0.0.1:8000"
node ".\node_modules\vite\bin\vite.js"
```

Open `http://localhost:5173`. API documentation is available at `http://127.0.0.1:8000/docs`.

## ☁️ Deployment

### Render backend

Create a Render Web Service connected to this repository. Use `backend` as the root directory, `pip install -r requirements.txt` as the build command, and:

```text
uvicorn app.api:app --host 0.0.0.0 --port $PORT
```

Add the variables from `.env.example`. The included `render.yaml` can also be used as a Blueprint. Local Ollama is not normally reachable from Render; configure a hosted LLM provider before public deployment.

### Vercel frontend

Import the repository into Vercel, set the root directory to `frontend`, build command to `npm run build`, and output directory to `dist`. Add:

```text
VITE_API_URL=https://your-render-service.onrender.com
```

Then deploy and test upload and Q&A against the Render URL.

### Current deployment links

- Frontend: https://docu-mind-ai-powered-document-q-a-assistant-using-pa5z83l48.vercel.app/
- Backend API health check: https://documind-ai-powered-document-q-a-rnfd.onrender.com/health
- Backend API documentation: https://documind-ai-powered-document-q-a-rnfd.onrender.com/docs

The deployed backend requires a funded OpenAI API key for answer generation. If the OpenAI account has no credits, uploads may succeed but questions return a `429 insufficient_quota` error.

## 💬 Example Usage

Upload a document, then ask:

```text
What are the main responsibilities described in this document?
Which policy applies to annual leave?
Summarize the document in five bullet points.
```

Questions unrelated to the uploaded evidence are refused instead of answered from outside knowledge.

## 🧠 GenAI Concepts

DocuMind demonstrates embeddings, vector similarity, chunking, metadata provenance, retrieval-augmented generation, prompt grounding, structured output parsing, citation validation, and confidence thresholds.

## 🛡️ Governance & Guardrails

- The model receives only retrieved document evidence.
- Evidence is treated as untrusted data, not instructions.
- Invalid or invented citation IDs are rejected.
- Unsupported questions return a refusal.
- Upload size, file type, encoding, and PDF encryption are validated.
- Documents and indexes are stored locally unless replaced with production storage.

## 📊 Evaluation

A 10–15 question evaluation harness is planned. No scores are claimed until it is implemented and run. Planned metrics are Retrieval Recall@K, Citation Accuracy, Answer Faithfulness, Refusal Accuracy, and Response Latency.

## 🧪 Testing

From `backend`:

```powershell
..\.venv313\Scripts\python.exe -m pytest
```

The test suite covers chunking, RAG grounding, retrieval, persistence, validation, model compatibility, and failed snapshot safety.

## 🔄 CI/CD

Render and Vercel deployment configuration is included. Automatic deployment can be enabled after connecting the GitHub repository. A CI workflow is planned.

## 🗺️ Development Roadmap

- [x] Document ingestion and semantic retrieval
- [x] Grounded local RAG answers
- [x] FastAPI API and web interface
- [x] Vercel and Render deployment configuration
- [ ] Hosted LLM provider abstraction
- [ ] Tool/function calling
- [ ] Conversation memory
- [ ] Token-budget-aware context management
- [ ] Audit logging
- [ ] Evaluation harness
- [ ] CI/CD workflow
- [ ] Authentication and multi-user workspaces
- [ ] Production database and object storage

## 🚀 Future Improvements

Streaming answers, persistent server-side chat history, document deletion and versioning, OCR, hybrid keyword/vector search, reranking, evaluation dashboards, rate limits, audit logs, and observability.

## 📚 Learning Resources

- [LangChain documentation](https://docs.langchain.com/)
- [FAISS documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)

## 🎬 Project Url
[https://docu-mind-ai-powered-document-q-a-assistant-using-pa5z83l48.vercel.app/](https://docu-mind-ai-powered-document-q-a-assistant-using-pa5z83l48.vercel.app/)



