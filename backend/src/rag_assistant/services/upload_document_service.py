from rag_assistant.ingestion.file_loader import load_file_from_path
from rag_assistant.ingestion.chunking import build_sections, split_sections_into_chunks
from rag_assistant.ingestion.embeddings import embed_chunks
from rag_assistant.storage.vector_store import add_chunk_to_db

def upload_document(file_path: str, file_name:str):
    if not file_path:
        raise ValueError("File path is required")

    pages = load_file_from_path(file_path)

    sections = build_sections(pages)  # group the text by heading
    chunks = split_sections_into_chunks(sections)  # default size and overlap (1000 / 200) , made for real documents
    embedded_chunks=embed_chunks(chunks) # convert the chunks to vectors
    chunks_stored=add_chunk_to_db(file_name, embedded_chunks)

    # Testing only: uncomment to print sections and chunks for an uploaded PDF
    # print(f"\n===== {len(pages)} pages -> {len(sections)} sections -> {len(chunks)} chunks =====")
    # for number, section in enumerate(sections, start=1):
    #     print(f"\n--- Section {number}: {section['heading']!r} (pages {section['page_number']}-{section['end_page']}, {len(section['text'])} chars)")
    #     print(section["text"][:300] + ("..." if len(section["text"]) > 300 else ""))  # first 300 characters is enough to check
    # print(f"\n===== Chunk sizes: {[len(chunk['text']) for chunk in chunks]} =====\n")

    return {"pages": pages, "chunks": chunks, "chunks_stored": chunks_stored}  # a dict with named keys , {pages, chunks} would be a set and fail
