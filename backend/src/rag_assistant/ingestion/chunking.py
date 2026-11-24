from typing import TypedDict
from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_spans_from_pages_directory(pages: list[dict]) -> list[dict]:
    # load_data_from_pdf returns [{"page_number": 1, "text": "...", "spans": [...]}, ...]
    # Put the spans of every page into one list, in reading order
    spans = []
    for page in pages:
        spans.extend(page["spans"])
    return spans


def is_heading(span: dict) -> bool:
    # Checks ONE span; the loop over all spans belongs in the chunking function
    size = span["size"]
    return size >= 13.0


class DocumentSection(TypedDict):
    heading: str | None
    text: str
    page_number: int  # Page where the section starts
    end_page: int  # Page where the section ends

def build_sections(pages: list[dict]) -> list[DocumentSection]:
    sections: list[DocumentSection] = []  # All the sections we build
    current_section: DocumentSection | None = None  # The section we are adding text to right now
    previous_position = None  # (page_number, block_number) of the last body text added , kept across pages

    for page in pages:  # Go through every page
        page_number = page["page_number"]  # The page is the source of truth for where a section starts
        for span in page["spans"]:  # Go through every span on the page
            text = span["text"].strip()
            if not text:  # Skip empty spans so they add no empty content or extra spaces
                continue
            position = (page_number, span.get("block_number", 0))  # .get with 0, so test spans without block_number still work
            if not is_heading(span):  # Body text: keep adding it to the current section
                if current_section is None:  # Only at the very start of the document, before the first heading: text gets its own section without a heading
                    current_section = {"heading": None, "text": text, "page_number": page_number, "end_page": page_number}
                    sections.append(current_section)  # Put it in the list
                elif current_section["text"]:
                    # same paragraph (block) -> a space , new paragraph or new page -> a paragraph break the splitter can cut at
                    separator = " " if position == previous_position else "\n\n"
                    current_section["text"] += separator + text  # Add the text to the current section, even if it started on an earlier page, continue the section
                    current_section["end_page"] = page_number  # The section now reaches this page
                else:  # First body text right after a heading: no leading space
                    current_section["text"] = text # new section with no earlier data
                    current_section["end_page"] = page_number  # The heading may be at the bottom of the previous page
                previous_position = position  # remember where this body text came from , to choose the next separator
            else:  # Heading: create a new section, ready for the body text that comes after it
                current_section = {"heading": text, "text": "", "page_number": page_number, "end_page": page_number}
                sections.append(current_section)  # Put it in the list; it is now the current section

    return sections  # The last section is already in the list, so nothing else to save

# why are we splitting sections into chunks? sections keep one topic together but can be too long to embed, so we split them into smaller chunks that each make sense on their own and keep the section's heading and pages

def split_sections_into_chunks(
    sections: list[DocumentSection], max_chunk_size: int = 1000, chunk_overlap: int = 200
) -> list[DocumentSection]:
    # Check the settings once, before doing any work
    if max_chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= max_chunk_size:
        raise ValueError(
            "max_chunk_size must be positive, chunk_overlap must not be negative, "
            "and chunk_overlap must be less than max_chunk_size"
        )

    chunks: list[DocumentSection] = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],  # paragraph, line, sentence, word, character
        keep_separator="end",
    )

    for section in sections:
        if not section["text"].strip():  # Heading-only or blank section: nothing to chunk
            continue
        for text in splitter.split_text(section["text"]):
            chunks.append({**section, "text": text})  # Keep the heading and page numbers of the section
    return chunks