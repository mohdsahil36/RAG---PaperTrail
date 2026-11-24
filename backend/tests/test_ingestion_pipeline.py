import pymupdf
from pathlib import Path
from rag_assistant.ingestion.pdf_loader import load_data_from_pdf
from rag_assistant.ingestion.chunking import split_sections_into_chunks, build_sections


def test_pdf_to_chunks_definitive_pipeline(tmp_path: Path):
    file_path = tmp_path / "sample_upload_file.pdf"
    document = pymupdf.open()  # empty PDF in memory, saved to file_path below

    # Page 1: a heading (16pt, above the 13pt heading threshold) and body text (11pt)
    page1 = document.new_page()
    page1.insert_text(pymupdf.Point(50, 72), "Leave Policy", fontsize=16)
    page1.insert_text(pymupdf.Point(50, 110), "Employees get 20 days of paid leave per year.", fontsize=11)

    # Page 2: body text only, so the "Leave Policy" section continues across the page break
    page2 = document.new_page()
    page2.insert_text(pymupdf.Point(50, 72), "Unused leave can be carried forward.", fontsize=11)

    document.save(str(file_path))
    document.close()

    # Run the real pipeline: PDF -> pages with spans -> sections -> chunks
    pages = load_data_from_pdf(str(file_path))
    sections = build_sections(pages)
    chunks = split_sections_into_chunks(sections, max_chunk_size=100, chunk_overlap=20)

    assert len(chunks) >= 1  # the pipeline produced output

    texts = []
    for chunk in chunks:
        texts.append(chunk["text"])  # collect each chunk's whole text
        assert chunk["heading"] == "Leave Policy"  # the 16pt text from the real PDF was detected as a heading
        assert chunk["page_number"] == 1  # the section starts on page 1
        assert chunk["end_page"] == 2  # the section continued across the page break
        assert chunk["text"].strip()  # no empty chunks
    all_text = " ".join(texts)  # join once, after the loop, into one string with the text of every chunk

    assert "Employees get 20 days" in all_text  # page 1 body text is kept
    assert "carried forward" in all_text  # page 2 text was attached to the section, not lost
    assert "Leave Policy" not in all_text  # the heading is metadata, not copied into the body text