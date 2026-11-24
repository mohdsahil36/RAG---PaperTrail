from pathlib import Path
from typing import cast

import pymupdf


def extract_pdf_spans(page_content: pymupdf.Page, page_number: int) -> list[dict]:
    # Get the page as a nested dictionary: page -> blocks -> lines -> spans
    # get_text() can return str, list or dict depending on the option, so tell the type checker it is a dict here
    data = cast(dict, page_content.get_text("dict"))
    spans = []

    for block_number, block in enumerate(data.get("blocks", [])): # enumerate gives each block its position (0, 1, 2...) , a block is roughly one paragraph , so we can tell which paragraph each span belongs to
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                span_text = span["text"].strip()
                # Skip spans that are only spaces
                if span_text:
                    spans.append(
                        {
                            "text": span_text,
                            "size": span["size"],
                            "page_number": page_number,
                            "block_number": block_number, # which paragraph (block) on this page the span came from , build_sections uses it to keep paragraph breaks so the splitter can cut at paragraphs first
                            "font": span["font"],
                            "flags": span["flags"],
                        }
                    )

    return spans


# Diagnosis only: counts spans by (font size, is bold, is italic) to find the heading sizes for chunking
# def analyse_pdf_structure(spans: list[dict]) -> dict[tuple[float, bool, bool], int]:
#     # Count spans by (font size, is bold, is italic), e.g. {(12.0, False, False): 1074, (12.0, True, False): 39}
#     style_groups: dict[tuple[float, bool, bool], int] = {}
#
#     for span in spans:
#         # Round so that sizes like 11.9999 and 12.0 are counted as the same size
#         size = round(span["size"], 1)
#         # bool() turns the flag check (16 or 0, 2 or 0) into True or False
#         is_bold = bool(span["flags"] & pymupdf.TEXT_FONT_BOLD)
#         is_italic = bool(span["flags"] & pymupdf.TEXT_FONT_ITALIC)
#
#         # One key per combination, so 12.0 normal and 12.0 bold are counted separately
#         key = (size, is_bold, is_italic)
#
#         if key not in style_groups:
#             # First span seen with this combination
#             style_groups[key] = 1
#         else:
#             style_groups[key] += 1
#
#     # Print the counts as a table, smallest font size first
#     print("Size\tBold\tItalic\tCount")
#     for key in sorted(style_groups):
#         size, is_bold, is_italic = key
#         print(f"{size}\t{is_bold}\t{is_italic}\t{style_groups[key]}")
#
#     return style_groups


def load_data_from_pdf(file_path: str):
    # Convert the incoming file path into a Path object
    path = Path(file_path)

    # Check whether the PDF exists before trying to open it
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Open the PDF and automatically close it when finished
    with pymupdf.open(path) as document:
        # check if the document is a valid PDF
        if not document.is_pdf:
            raise ValueError("The file is not a valid PDF format file")
        # Store the extracted text, page number and spans for each page
        pages = []

        # Start page numbering at 1 instead of Python's default 0
        for page_number, page_content in enumerate(document.pages(), start=1):
            # Extract text from the current pages
            text = page_content.get_text()

            # Store the text and its spans (text pieces with font size and style) together with the page number
            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "spans": extract_pdf_spans(page_content, page_number),
                }
            )

        # Diagnosis only: uncomment to check the spans of the whole document
        # all_spans = [span for page in pages for span in page["spans"]]

        # Print only the spans with size 16.0 or 20.0 (the headings)
        # for span in all_spans:
        #     # Check the size inside the loop, so each span is tested on its own
        #     if round(span["size"], 1) in (16.0, 20.0):
        #         print(
        #             f"Page: {span['page_number']} | Size: {round(span['size'], 1)} | Flags: {span['flags']} | Text: {span['text']}"
        #         )

        # Print the table of span counts by font size, bold and italic
        # analyse_pdf_structure(all_spans)
    # Return all extracted pages after processing the PDF
    return pages
