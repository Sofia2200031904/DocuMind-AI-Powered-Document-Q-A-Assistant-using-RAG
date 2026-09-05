import io
import pytest
from pypdf import PdfWriter
from app.config import Settings
from app.services.document_service import DocumentService, chunk_pages


def test_empty_and_short():
    assert chunk_pages(['   '], 'id', 'a.txt') == []
    result = chunk_pages(['hello'], 'id', 'a.txt')
    assert len(result) == 1
    assert result[0].content == 'hello'
    assert result[0].page is None


def test_overlap_and_metadata():
    text = ''.join(chr(0x4E00 + i) for i in range(240))
    chunks = chunk_pages([text, 'second page'], 'doc', 'a.pdf', 80, 15, True)
    assert all(len(c.content) <= 80 for c in chunks)
    assert chunks[0].content[-15:] == chunks[1].content[:15]
    assert all(c.document_id == 'doc' and c.section == 'Unknown' for c in chunks)
    assert all(c.document_name == c.source == 'a.pdf' for c in chunks)
    assert chunks[-1].page == 2
    assert len({c.chunk_id for c in chunks}) == len(chunks)


@pytest.mark.parametrize('name,data', [('a.csv', b'text'), ('a.txt', b''),
                                      ('a.txt', b'\xff'), ('a.pdf', b'broken')])
def test_invalid_documents(name, data):
    with pytest.raises(ValueError):
        DocumentService(Settings()).parse(name, data)


def test_sanitized_filename_and_size():
    service = DocumentService(Settings(max_upload_mb=1))
    doc, _ = service.parse('../../policy.txt', b'Policy text')
    assert doc.document_name == 'policy.txt'
    with pytest.raises(ValueError):
        service.parse('large.txt', b'a' * (1024 * 1024 + 1))


def test_pdf_extraction():
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
        DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 700 Td (Annual leave is 20 days.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    doc, chunks = DocumentService(Settings()).parse('policy.pdf', output.getvalue())
    assert doc.pages == 1
    assert chunks[0].page == 1
    assert '20 days' in chunks[0].content


def test_invalid_overlap():
    with pytest.raises(ValueError):
        Settings(chunk_size=10, chunk_overlap=10)
