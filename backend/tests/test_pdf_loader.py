import pytest
import pymupdf
from pathlib import Path
from rag_assistant.ingestion.pdf_loader import load_data_from_pdf

# Test 1 - check if the pdf is valid and exisits otherwise raise FileNotFoundError
def test_load_file_does_not_exist(tmp_path:Path):
    file_path=tmp_path/"missingFile.pdf"

    with pytest.raises(FileNotFoundError):
        load_data_from_pdf(str(file_path))

# Test 2: A valid PDF with one page.
def test_load_file_exists_single_page(tmp_path:Path):
    # Sample file path
    file_path=tmp_path/"sampleFile.pdf"
    # Create the sample pdf file for testing
    document=pymupdf.open()
    # Add a new page to the document
    page = document.new_page()
    # Adding content to the new document's first page
    refPoint=pymupdf.Point(20,20) #20,20 so that it does not start at the absolute corner , it has a little bit of margin
    page.insert_text(refPoint,"This is sample PDF text!")
    document.save(str(file_path))
    document.close()

    result=load_data_from_pdf(str(file_path))
    
    assert len(result) == 1 # check the number of pages
    assert result[0]["page_number"] == 1 # check the page number 
    # then check if the text is present in the result
    assert "This is sample PDF text!" in result[0]["text"]
    # every span must record its block (paragraph) number , build_sections needs it to keep paragraph breaks
    assert result[0]["spans"][0]["block_number"] == 0 # only one block on this page , so it is the first block (0)

# Test 3 : A valid PDF with multiple pages
def test_load_file_exists_multiple_pages(tmp_path:Path):
    # Sample file path with multiple pages
    file_path=tmp_path/"multiplePages.pdf"
    # Create the file for testing
    document=pymupdf.open()
    # Add multiple pages to the document
    for page_number in range(3):
        page=document.new_page()
        page.insert_text(pymupdf.Point(20,20),f"This is page {page_number+1} of the PDF")
    document.save(str(file_path))
    document.close()

    result = load_data_from_pdf(str(file_path)) # load the sample file in the pdf loader
    assert len(result)==3 # check if the number of pages in the file is 3
    assert result[0]["page_number"] == 1 # check the page number 
    assert result[1]["page_number"] == 2 # check the page number 
    assert result[2]["page_number"] == 3 # check the page number 
    # then check if the text is present in the result
    assert "This is page 1 of the PDF" in result[0]["text"]
    assert "This is page 2 of the PDF" in result[1]["text"]
    assert "This is page 3 of the PDF" in result[2]["text"]

# Test 4: A valid PDF with no text (blank PDF and page).
def test_load_file_exists_blank_page(tmp_path:Path):
    # Sample file path
    file_path=tmp_path/"emptyFile.pdf"
    # Create the sample pdf file for testing
    document=pymupdf.open()
    # Add a new page to the document
    page = document.new_page()
    # We have created a blank page , saved it but not added any content to it
    document.save(str(file_path))
    document.close()

    result=load_data_from_pdf(str(file_path))
    
    assert len(result) == 1 # check the number of pages
    assert result[0]["page_number"] == 1 # check the page number 
    # then check if the text is present in the result
    assert result[0]["text"] == ""


# Test 5 : Invalid PDF file (non - existing file path / file extension is not pdf)
def test_load_file_invalid_path(tmp_path:Path):
    # Sample file path but that is not a PDF format
    file_path=tmp_path/"sampleFile.md"
    # Adding a new page with content to the markdown file
    file_path.write_text("This is a sample Markdown file!", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info: # check the condition if the file is not a PDF format and then raise an exception to the parent function as exec_info variable
        load_data_from_pdf(str(file_path))
    print(type(exc_info.value).__name__) # Print the exception type name from the exception value
    assert "not a valid PDF" in str(exc_info.value) # check the error is the "not a PDF" one from our loader , not some other ValueError