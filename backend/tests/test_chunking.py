import pytest

from rag_assistant.ingestion.chunking import is_heading
from rag_assistant.ingestion.chunking import build_sections
from rag_assistant.ingestion.chunking import split_sections_into_chunks
from rag_assistant.ingestion.chunking import DocumentSection

# we have defined here the paramters for which we will be testing the is_heading function
@pytest.mark.parametrize(
    "size, expected",
    [
        (14.0, True),
        (16.0, True),
        (20.0, True),
        (26.0, True),
        (11.0, False),
        (12.0, False),
    ],
)

def test_get_spans_from_pages_directory(size:float,expected:bool):
    span = {"size": size}

    assert is_heading(span) == expected


def test_single_heading_with_body():
    pages = [
        {
            "page_number": 1,
            "text": "Introduction RAG retrieves information.",
            "spans": [
                {"text": "Introduction", "size": 16, "page_number": 1},
                {"text": "RAG retrieves information.", "size": 12, "page_number": 1},
            ],
        }
    ]

    result = build_sections(pages)

    assert len(result)==1
    assert result[0]["heading"]=="Introduction"
    assert result[0]["text"]=="RAG retrieves information."
    assert result[0]["page_number"]==1

def test_multiple_heading_multiple_sections():
    pages = [
        {
            "page_number": 1,
            "text": "Introduction RAG retrieves information. Chunking splits text.",
            "spans": [
                {"text": "Introduction", "size": 16, "page_number": 1},
                {"text": "RAG retrieves information.", "size": 12, "page_number": 1},
                {"text": "Chunking", "size": 16, "page_number": 1},
                {"text": "Chunking splits text.", "size": 12, "page_number": 1},
            ],
        }
    ]

    result = build_sections(pages)

    assert len(result)==2
    assert result[0]["heading"]=="Introduction"
    assert result[1]["heading"]=="Chunking"
    assert result[0]["text"]=="RAG retrieves information."
    assert result[1]["text"]=="Chunking splits text."

def test_body_text_before_first_heading():
    pages = [
        {
            "page_number": 1,
            "text": "Opening text. Introduction Details here.",
            "spans": [
                {"text": "Opening text.", "size": 12, "page_number": 1},
                {"text": "Introduction", "size": 16, "page_number": 1},
                {"text": "Details here.", "size": 12, "page_number": 1},
            ],
        }
    ]

    result = build_sections(pages)
    assert len(result)==2
    assert result[0]["heading"] is None
    assert result[0]["text"]=="Opening text."
    assert result[1]["heading"]=="Introduction"
    assert result[1]["text"]=="Details here."

def test_sections_across_pages():
    pages = [
        {
            "page_number": 1,
            "text": "Introduction First part.",
            "spans": [
                {"text": "Introduction", "size": 16, "page_number": 1},
                {"text": "First part.", "size": 12, "page_number": 1},
            ],
        },
        {
            "page_number": 2,
            "text": "Second part.",
            "spans": [
                {"text": "Second part.", "size": 12, "page_number": 2},
            ],
        },
    ]

    result = build_sections(pages)
    assert len(result) == 1
    assert result[0]["heading"] == "Introduction"
    assert "First part." in result[0]["text"]
    assert "Second part." in result[0]["text"]
    assert result[0]["page_number"] == 1
    assert result[0]["end_page"] == 2

def test_heading_at_bottom_of_page():
    pages = [
        {
            "page_number": 1,
            "text": "Introduction",
            "spans": [
                {"text": "Introduction", "size": 16, "page_number": 1},
            ],
        },
        {
            "page_number": 2,
            "text": "Body on next page.",
            "spans": [
                {"text": "Body on next page.", "size": 12, "page_number": 2},
            ],
        },
    ]

    result = build_sections(pages)
    assert len(result) == 1
    assert result[0]["text"] == "Body on next page."
    assert result[0]["page_number"] == 1
    assert result[0]["end_page"] == 2

def test_empty_pages():
    assert build_sections([]) == []

# tests for splitting text into chunks
def test_empty_input_empty_section():
    input_section: list[DocumentSection] = [{"heading": None, "text": "", "page_number": 1, "end_page": 1}]

    result = split_sections_into_chunks(input_section, max_chunk_size=100, chunk_overlap=20)

    assert result == []
    # below test is for completely empty document
    assert split_sections_into_chunks([], max_chunk_size=100, chunk_overlap=20) == []

# Text that fits (shorter than or exactly max_chunk_size) must stay one chunk, unchanged
@pytest.mark.parametrize(
    "text",
    [
        "Short text.",  # shorter than max_chunk_size , if the length is small or shorter then it should stay as one chunk
        "a" * 100,  # exactly max_chunk_size
    ],
    ids=["shorter", "equal"],
)
def test_text_that_fits_stays_one_chunk(text: str):
    input_section: list[DocumentSection] = [{"heading": "Heading", "text": text, "page_number": 1, "end_page": 1}]

    result = split_sections_into_chunks(input_section, max_chunk_size=100, chunk_overlap=20)

    assert len(result) == 1
    assert result[0]["text"] == text


def test_text_longer_than_chunk_size_is_split():
    long_text = " ".join(f"This is sentence {i}." for i in range(20))  # About 400 characters
    input_section: list[DocumentSection] = [{"heading": "Heading", "text": long_text, "page_number": 1, "end_page": 1}]

    result = split_sections_into_chunks(input_section, max_chunk_size=100, chunk_overlap=20)

    assert len(result) > 1
    assert all(len(chunk["text"]) <= 100 for chunk in result)  # No chunk is over the limit

def test_neighbouring_chunks_overlap():
    # testing if the overlapping text lies in the consecutive chunks
    long_text = " ".join(f"This is sentence {i}." for i in range(20))  # About 400 characters
    input_section: list[DocumentSection] = [{"heading": "Heading", "text": long_text, "page_number": 1, "end_page": 1}]

    result = split_sections_into_chunks(input_section, max_chunk_size=100, chunk_overlap=20)

    chunk1_text = result[0]["text"]
    chunk2_text = result[1]["text"]

    # The last sentence of the first chunk must be repeated at the start of the second chunk
    last_sentence_of_first_chunk = chunk1_text.split(". ")[-1]
    assert chunk2_text.startswith(last_sentence_of_first_chunk)

def test_check_metadata_is_preserved():
    long_text = " ".join(f"This is sentence {i}." for i in range(20))  # About 400 characters
    input_section: list[DocumentSection] = [{"heading": "Leave Policy", "text": long_text, "page_number": 3, "end_page": 5}] # we have given specifc page metadata , now need to check if the metadata is preserved in the individual chunks

    result = split_sections_into_chunks(input_section, max_chunk_size=100, chunk_overlap=20)

    assert len(result)>1
    for chunk in result:
        assert chunk["heading"]=="Leave Policy"
        assert chunk["page_number"]==3
        assert chunk["end_page"]==5

        assert set(chunk.keys())=={"heading","text","page_number","end_page"} # check if the inidividual chunks have the same metadata keys

def test_no_text_or_metadata_mixes_between_chunks():
    long_text1 = " ".join(f"This is First Chunk sentence {i}." for i in range(20))  # About 400 characters
    long_text2 = "This is Second Chunk Text."

    # Both sections go into one call, as in real use, so the test can catch text or metadata mixing between them
    input_sections: list[DocumentSection] = [
        {"heading": "Section A", "text": long_text1, "page_number": 1, "end_page": 2},
        {"heading": "Section B", "text": long_text2, "page_number": 3, "end_page": 3},
    ]

    result = split_sections_into_chunks(input_sections, max_chunk_size=100, chunk_overlap=20)

    a_chunks = [chunk for chunk in result if chunk["heading"] == "Section A"]
    b_chunks = [chunk for chunk in result if chunk["heading"] == "Section B"]

    # Every chunk belongs to one of the two sections
    assert len(a_chunks) + len(b_chunks) == len(result)

    # Section A was split, keeps its own pages, and has no text from section B
    assert len(a_chunks) > 1
    for chunk in a_chunks:
        assert chunk["page_number"] == 1
        assert chunk["end_page"] == 2
        assert "Second" not in chunk["text"]

    # Section B stayed whole, with its own text and pages
    assert len(b_chunks) == 1
    assert b_chunks[0]["text"] == long_text2
    assert b_chunks[0]["page_number"] == 3
    assert b_chunks[0]["end_page"] == 3

    # Chunks keep the document order: section B comes after section A
    assert result[-1]["heading"] == "Section B"

def test_heading_only_section_chunk():
    input_sections: list[DocumentSection] = [
        {"heading": "Only Heading", "text": "", "page_number": 1, "end_page": 2},
        {"heading": "Leave Policy", "text": "This is the content for the section on leave policy", "page_number": 3, "end_page": 3},
    ]


    result = split_sections_into_chunks(input_sections, max_chunk_size=100, chunk_overlap=20)

    assert len(result) == 1
    assert all(chunk["text"].strip() for chunk in result) # strip to remove spaces so empty chunk comes as "", empty is false / non empty is true , all is true only if all the chunks have real text , we ensure here that no empty chunk is created
    assert result[0]["heading"] == "Leave Policy"
    assert result[0]["text"] == input_sections[1]["text"]

    for chunk in result:
        assert chunk["heading"] != "Only Heading"  # The heading-only section must not produce a chunk

def test_whitespace_only_section():
    input_sections: list[DocumentSection] = [
        {"heading": "Blank Section With No Text", "text": "  ", "page_number": 1, "end_page": 2},
        {"heading": "Leave Policy", "text": "This is the content for the section on leave policy", "page_number": 3, "end_page": 3},
    ]


    result = split_sections_into_chunks(input_sections, max_chunk_size=100, chunk_overlap=20)

    assert len(result)==1 # without text the first input does not create a new chunk
    for chunk in result:
        assert chunk["heading"]!="Blank Section With No Text" # same as the above , blank section does not create a new chunk
        assert chunk["heading"]=="Leave Policy"
        assert chunk["text"]==input_sections[1]["text"]

@pytest.mark.parametrize(
    "max_chunk_size,chunk_overlap", # parameter names
    [
        (0,0), # chunk size is not positive
        (100,-1), # negative overlap value
        (100, 100), # overlap is equal to the chunk size , the splitter cannot move forward to the next chunk
        (100,200), # overlap is greater than the chunk size , the splitter cannot move forward to the next chunk
    ],
        ids=["zero_chunk_size", "negative_overlap", "overlap_equal_to_size", "overlap_greater_than_size"], # readable test name
)
# each time pytest calls the below function with the above values , of the max_chunk_size and chunk overlap , also it sends its id for the test name
def test_invalidation_errors_raised(max_chunk_size:int, chunk_overlap:int):
    input_sections: list[DocumentSection] = [{"heading": "Heading", "text": "Some text.", "page_number": 1, "end_page": 1}]

    with pytest.raises(ValueError):
        split_sections_into_chunks(input_sections, max_chunk_size=max_chunk_size, chunk_overlap=chunk_overlap)


# Paragraph breaks: same block -> a space , new block or new page -> "\n\n"
@pytest.mark.parametrize(
    "second_page, second_block, expected_text",
    [
        (1, 1, "First. Second."), # same page and same block , the same paragraph wrapped onto another line
        (1, 2, "First.\n\nSecond."), # same page but a new block , a new paragraph
        (2, 0, "First.\n\nSecond."), # a new page , always a new paragraph
    ],
    ids=["same_paragraph", "new_paragraph", "new_page"],
)
def test_paragraph_breaks_between_blocks(second_page: int, second_block: int, expected_text: str):
    first_page_spans = [
        {"text": "Leave Policy", "size": 16, "page_number": 1, "block_number": 0}, # heading
        {"text": "First.", "size": 12, "page_number": 1, "block_number": 1}, # first body text
    ]
    second_span = {"text": "Second.", "size": 12, "page_number": second_page, "block_number": second_block}

    if second_page == 1:
        # second span is on the same page , so it goes in the same span list
        pages = [{"page_number": 1, "spans": first_page_spans + [second_span]}]
    else:
        # second span is on the next page , so it goes in its own page dictionary
        pages = [
            {"page_number": 1, "spans": first_page_spans},
            {"page_number": second_page, "spans": [second_span]},
        ]

    result = build_sections(pages)

    assert len(result) == 1 # one heading , so one section
    assert result[0]["text"] == expected_text # space or paragraph break between the two body texts
