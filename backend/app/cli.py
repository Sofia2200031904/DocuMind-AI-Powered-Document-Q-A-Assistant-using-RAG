"""Index documents, retrieve evidence, or ask the Phase 2 LCEL chain."""
import argparse
import json
import logging
from pathlib import Path

from app.config import Settings
from app.services.document_service import DocumentService
from app.services.embedding_service import create_embeddings
from app.services.retrieval_service import RetrievalService
from app.services.vector_store import VectorStore


def main() -> int:
    parser = argparse.ArgumentParser(description='DocuMind: document retrieval and grounded answers')
    commands = parser.add_subparsers(dest='command', required=True)
    ingest = commands.add_parser('ingest')
    ingest.add_argument('paths', nargs='+', type=Path)
    query = commands.add_parser('query')
    query.add_argument('question')
    query.add_argument('--top-k', type=int)
    query.add_argument('--threshold', type=float)
    ask = commands.add_parser('ask')
    ask.add_argument('question')
    commands.add_parser('documents')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    logging.getLogger('httpx').setLevel(logging.WARNING)
    try:
        settings = Settings()
        identity = f'{settings.embedding_provider}:{settings.embedding_model}'
        store = VectorStore(settings.vector_store_path, identity)
        if args.command == 'documents':
            print(json.dumps([d.model_dump() for d in store.documents()], indent=2))
            return 0
        embeddings = create_embeddings(settings)
        if args.command == 'ingest':
            service = DocumentService(settings)
            files = []
            for path in args.paths:
                files.extend(sorted(p for p in path.iterdir() if p.suffix.lower() in {'.pdf', '.txt'})
                             if path.is_dir() else [path])
            if not files:
                raise ValueError('No PDF/TXT files found')
            for path in files:
                with path.open('rb') as file:
                    data = file.read(settings.max_upload_mb * 1024 * 1024 + 1)
                doc, chunks = service.parse(path.name, data)
                added = store.add(doc, chunks, embeddings.embed([c.content for c in chunks]))
                print(json.dumps(dict(filename=doc.document_name, chunks_created=len(chunks),
                                      status='indexed' if added else 'already_indexed')))
        elif args.command == 'ask':
            from app.services.local_model import create_local_model
            from app.services.rag_service import RAGService
            import httpx
            from ollama import ResponseError
            rag = RAGService(RetrievalService(embeddings, store, settings),
                             create_local_model(settings))
            try:
                print(rag.ask(args.question).model_dump_json(indent=2))
            except (httpx.HTTPError, ConnectionError, ResponseError) as exc:
                raise RuntimeError(
                    'Local LLM unavailable. Start Ollama and run '
                    f'"ollama pull {settings.ollama_model}". Check OLLAMA_BASE_URL '
                    'and LLM_TIMEOUT_SECONDS in .env.'
                ) from exc
        else:
            results = RetrievalService(embeddings, store, settings).retrieve(
                args.question, args.top_k, args.threshold)
            print(json.dumps([r.model_dump() for r in results], indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        logging.error('%s: %s', type(exc).__name__, exc)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
