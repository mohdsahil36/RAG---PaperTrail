from pathlib import Path

import pytest
from rag_assistant.ingestion.file_loader import load_file_from_path

# First test - a file that is not a PDF is rejected, only PDFs are supported for now


def test_non_pdf_file_is_rejected(tmp_path: Path):
    # Create a temporary text file for the test
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Hello there , this is RAG file", encoding="utf-8")

    # The file does not start with the "%PDF-" header, so the loader must raise ValueError
    with pytest.raises(ValueError):
        load_file_from_path(str(file_path))


# Second test - for the input file does not exist at the defined path
def test_load_file_if_does_not_exists(tmp_path: Path):
    # Arrange: define a path to a file that does not exist
    file_path = tmp_path / "missingFile.txt"  # this file does not exist

    # Act and Assert: verify that the loader raises FileNotFoundError
    with pytest.raises(
        FileNotFoundError
    ):  # we cannot just put this for safty anywhere , this code block expects error to be present so that it can point it out
        load_file_from_path(str(file_path))


# Third test- File exists but does not have any content inside
def test_empty_file_is_rejected(tmp_path: Path):
    # Arrange a temp file which exists but does not have content inside
    file_path = tmp_path / "emptyFile.txt"  # this file does not have any content
    file_path.write_text(
        "", encoding="utf-8"
    )  # this defines that the file does not have any content

    # An empty file has no "%PDF-" header, so the loader must raise ValueError
    with pytest.raises(ValueError):
        load_file_from_path(str(file_path))
