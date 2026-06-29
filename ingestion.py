import os
from pypdf import PdfReader
import docx


def read_pdf(file_path):
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"PDF read error ({file_path}): {e}")
    return text


def read_word(file_path):
    text = ""
    try:
        doc = docx.Document(file_path)
        text = "\n".join(
            para.text for para in doc.paragraphs if para.text.strip()
        )
    except Exception as e:
        print(f"Word read error ({file_path}): {e}")
    return text


def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1

        if current_length >= chunk_size:
            chunks.append(" ".join(current_chunk))

            current_chunk = (
                current_chunk[-overlap:]
                if overlap < len(current_chunk)
                else []
            )
            current_length = sum(len(w) + 1 for w in current_chunk)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def process_documents(data_folder="data"):
    """
    Reads PDF and Word documents from a folder and splits them into text chunks.
    """
    all_chunks = []

    print(f"Scanning documents in '{data_folder}'...")

    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        text = ""

        if filename.endswith(".pdf"):
            print(f"Reading file: {filename} (PDF)")
            text = read_pdf(file_path)

        elif filename.endswith(".docx"):
            print(f"Reading file: {filename} (Word)")
            text = read_word(file_path)

        else:
            continue

        if text:
            file_chunks = chunk_text(text, chunk_size=400, overlap=40)
            print(f"File split into {len(file_chunks)} chunks: {filename}")

            for i, chunk_text_content in enumerate(file_chunks):
                all_chunks.append({
                    "source": filename,
                    "chunk_id": i,
                    "text": chunk_text_content
                })

    return all_chunks


if __name__ == "__main__":
    print("Starting ingestion process...")

    chunks = process_documents("data")

    print(f"Total chunks created: {len(chunks)}")

    if chunks:
        print("Sample output (first chunk):")
        print(f"Source: {chunks[0]['source']}")
        print(f"Text preview: {chunks[0]['text'][:200]}... [TRUNCATED]")