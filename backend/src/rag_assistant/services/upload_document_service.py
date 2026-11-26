from rag_assistant.ingestion.file_loader import load_file_from_path
from rag_assistant.ingestion.chunking import build_sections, split_sections_into_chunks
from rag_assistant.ingestion.embeddings import embed_chunks
from rag_assistant.storage.vector_store import add_chunk_to_db

def upload_document(file_path: str, file_name:str):
    if not file_path:
        raise ValueError("File path is required")

    pages = load_file_from_path(file_path)

    sections = build_sections(pages)
    all_embedded: list = []

    for i, section in enumerate(sections):
        parent_id = f"{file_name}--parent--{i}"
        parent_chunks = embed_chunks([section], chunk_type="parent", parent_id="")
        all_embedded.extend(parent_chunks)

        child_sections = split_sections_into_chunks([section])
        child_chunks = embed_chunks(child_sections, chunk_type="child", parent_id=parent_id)
        all_embedded.extend(child_chunks)

    chunks_stored = add_chunk_to_db(file_name, all_embedded)

    # Testing only: uncomment to print sections and chunks for an uploaded PDF
    # print(f"\n===== {len(pages)} pages -> {len(sections)} sections -> {len(chunks)} chunks =====")
    # for number, section in enumerate(sections, start=1):
    #     print(f"\n--- Section {number}: {section['heading']!r} (pages {section['page_number']}-{section['end_page']}, {len(section['text'])} chars)")
    #     print(section["text"][:300] + ("..." if len(section["text"]) > 300 else ""))  # first 300 characters is enough to check
    # print(f"\n===== Chunk sizes: {[len(chunk['text']) for chunk in chunks]} =====\n")

    return {"pages": pages, "chunks": all_embedded, "chunks_stored": chunks_stored}  # a dict with named keys , {pages, chunks} would be a set and fail
