# 🧠 DocuMind-AI-Powered-Document-Q-A-Assistant-using-RAG


DocuMind is a document-grounded Q&A assistant. Upload PDF or TXT files, ask natural-language questions, and receive answers supported by retrieved document evidence and source citations.

[Demo](#-demo-video) · [GitHub](https://github.com/Sofia2200031904/DocuMind-AI-Powered-Document-Q-A-Assistant-using-RAG) · [License](#license)

## 📸 Screenshots

Add screenshots to `docs/images/` and embed them here:

```markdown
![DocuMind chat interface](docs/images/chat.png)
```

## 🎯 Overview

DocuMind turns documents into a searchable knowledge base. It validates uploads, extracts text, preserves page metadata, creates semantic embeddings, retrieves relevant chunks, and generates a grounded response.

## ✨ Features

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
Frontend (Vercel) → FastAPI API (Render) → Document service → Embeddings → FAISS
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

Evaluation should measure retrieval recall, answer faithfulness, citation correctness, refusal accuracy, latency, and cost using a representative question/evidence set.

## 🧪 Testing

From `backend`:

```powershell
..\.venv313\Scripts\python.exe -m pytest
```

The test suite covers chunking, RAG grounding, retrieval, persistence, validation, model compatibility, and failed snapshot safety.

## 🔄 CI/CD

Pushes to GitHub can trigger Render backend deployment and Vercel frontend deployment. Configure the frontend variable `VITE_API_URL` to the deployed Render API URL.

## 🗺️ Development Roadmap

- [x] Document ingestion and semantic retrieval
- [x] Grounded local RAG answers
- [x] FastAPI API and web interface
- [x] Vercel and Render deployment configuration
- [ ] Hosted LLM provider abstraction
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

## 🎬 Demo Video

Record a short walkthrough showing:

1. Starting the backend and frontend.
2. Uploading a sample PDF/TXT file.
3. Asking a document question.
4. Showing the grounded answer and citations.
5. Clicking a previous question in chat history.

Upload the video to YouTube or LinkedIn and replace the Demo link at the top with the public URL. For a GitHub-hosted demo, add an MP4 or GIF under `docs/demo/` and embed it using a linked thumbnail.



