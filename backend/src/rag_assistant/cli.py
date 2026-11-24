from pathlib import Path  # Provides tools to work with file and directory paths

from rag_assistant.ingestion.file_loader import load_file_from_path  # Imports the loader function used to read the document


def main():
    # Identify the project root based on the location of this Python file
    project_root = Path(__file__).resolve().parents[2]

    # Build the path to the document stored inside the project's data directory
    document_path = project_root / "data" / "sample.txt"

    try:
        # Call the loader and store the text returned from the document
        text = load_file_from_path(str(document_path))

        # Check whether the loader returned any text
        if text:
            # Display a success message when the document contains text
            print("Document loaded successfully!")

            # Display the contents of the loaded document
            print(text)
        else:
            # Handle the scenario where the file exists but contains no text
            print("The document is empty.")

    except FileNotFoundError:
        # Handle the scenario where the requested file does not exist
        print(f"Error: File not found at {document_path}")


# Ensure main() runs only when this module is executed directly, not when imported
if __name__ == "__main__":
    main()
