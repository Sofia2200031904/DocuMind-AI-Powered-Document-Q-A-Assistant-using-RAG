"""Validate and parse bytes, then split each page without losing provenance."""
import hashlib
import io
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from uuid import uuid4

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import Settings
from app.models.documents import Chunk, DocumentMetadata


def chunk_pages(pages: list[str], document_id: str, filename: str,
                chunk_size: int = 800, chunk_overlap: int = 100,
                is_pdf: bool = False) -> list[Chunk]:
    """Character-based recursive chunks; PDF page numbers are one-based."""
    if chunk_size < 2 or not 0 <= chunk_overlap < chunk_size:
        raise ValueError('Invalid chunk size/overlap')
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap,
        separators=['\n\n', '\n', '. ', ' ', ''],
    )
    result = []
    for number, text in enumerate(pages, start=1):
        text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\x00', '')
        text = re.sub(r'[^\S\n]+', ' ', text).strip()
        for content in splitter.split_text(text):
            result.append(Chunk(content=content, document_id=document_id,
                                document_name=filename, source=filename,
                                page=number if is_pdf else None, chunk_id=str(uuid4())))
    return result


class DocumentService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def parse(self, filename: str, data: bytes) -> tuple[DocumentMetadata, list[Chunk]]:
        filename = PurePosixPath(filename.replace('\\', '/')).name
        filename = re.sub(r'[^\w. -]', '_', filename)[:160]
        extension = PurePosixPath(filename).suffix.lower()
        if extension not in {'.pdf', '.txt'}:
            raise ValueError('Only PDF and TXT documents are supported')
        if not data or len(data) > self.settings.max_upload_mb * 1024 * 1024:
            raise ValueError('Document is empty or exceeds the upload size limit')
        if extension == '.txt':
            try:
                pages = [data.decode('utf-8-sig')]
            except UnicodeDecodeError as exc:
                raise ValueError('TXT documents must use UTF-8 encoding') from exc
        else:
            try:
                reader = PdfReader(io.BytesIO(data), strict=True)
                if reader.is_encrypted:
                    raise ValueError('Encrypted PDFs are not supported')
                pages = [page.extract_text() or '' for page in reader.pages]
            except Exception as exc:
                raise ValueError('Cannot read PDF; supply an unencrypted text PDF') from exc
        doc_id = str(uuid4())
        chunks = chunk_pages(pages, doc_id, filename, self.settings.chunk_size,
                             self.settings.chunk_overlap, extension == '.pdf')
        if not chunks:
            raise ValueError('No extractable text; scanned PDFs require OCR (not implemented)')
        metadata = DocumentMetadata(
            document_id=doc_id, document_name=filename, document_type=extension[1:],
            pages=len(pages), uploaded_at=datetime.now(timezone.utc).isoformat(),
            sha256=hashlib.sha256(data).hexdigest(), chunks_created=len(chunks),
        )
        return metadata, chunks
