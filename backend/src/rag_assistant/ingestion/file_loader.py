from pathlib import Path  # Provides tools to work with file and directory paths
from rag_assistant.ingestion.pdf_loader import load_data_from_pdf


def load_file_from_path(file_path: str) -> list[dict]:
    # Convert the file path string into a Path object so we can work with the file
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Could not locate the file at {file_path}")

    # Open the file in binary mode and read the first 5 bytes to detect the file type
    with path.open("rb") as file:
        header = file.read(5)

    if header == b"%PDF-":
        return load_data_from_pdf(str(path))

    raise ValueError(f"Unsupported file format: {path.name}")
