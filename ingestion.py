import os
from pypdf import PdfReader
import docx
import pandas as pd


SECTION_KEYWORDS = {
    "contact": ["email", "e-posta", "mail", "@", "iletişim"],
    "skills": ["teknik beceri", "skills", "yetenek", "programming", "tools"],
    "experience": ["deneyim", "experience", "tecrübe", "intern", "staj"],
    "education": ["eğitim", "education", "üniversite", "university", "lise"],
}


def detect_section(text: str) -> str:
    """Classifies text chunk into semantic section type."""
    text_lower = text.lower()

    for section, keywords in SECTION_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return section

    return "general"


def read_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        reader = PdfReader(file_path)
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )
    except Exception as e:
        print(f"PDF read error: {file_path} | {e}")
        return ""


def read_word(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        doc = docx.Document(file_path)
        return "\n".join(
            para.text for para in doc.paragraphs if para.text.strip()
        )
    except Exception as e:
        print(f"DOCX read error: {file_path} | {e}")
        return ""


def read_parquet(file_path: str, max_rows: int = 50) -> str:
    """Extract text from a Parquet file.

    Looks for a 'text' column (Wikipedia-style datasets use this).
    Falls back to concatenating all string columns if 'text' is missing.
    max_rows limits how many rows get pulled in, since these files can
    be hundreds of MB / millions of rows.
    """
    try:
        df = pd.read_parquet(file_path)

        if "text" in df.columns:
            rows = df["text"].astype(str).tolist()[:max_rows]
            return " ".join(rows)

        # Fallback: no 'text' column, just join all object/string columns
        text_cols = df.select_dtypes(include="object").columns
        if len(text_cols) == 0:
            print(f"Parquet file has no text-like columns: {file_path}")
            return ""

        rows = df[text_cols].astype(str).agg(" ".join, axis=1).tolist()[:max_rows]
        return " ".join(rows)

    except Exception as e:
        print(f"Parquet read error: {file_path} | {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 40):
    """Split text into overlapping chunks."""
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


def process_documents(data_folder: str = "data", parquet_max_rows: int = 50):
    """Process documents and return structured chunks with metadata."""

    all_chunks = []

    if not os.path.exists(data_folder):
        print(f"Data folder not found: {data_folder}")
        return all_chunks

    print(f"Scanning documents in folder: {data_folder}")

    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)

        if filename.endswith(".pdf"):
            print(f"Reading (PDF): {filename}")
            text = read_pdf(file_path)

        elif filename.endswith(".docx"):
            print(f"Reading (DOCX): {filename}")
            text = read_word(file_path)

        elif filename.endswith(".parquet"):
            print(f"Reading (Parquet): {filename}")
            text = read_parquet(file_path, max_rows=parquet_max_rows)

        else:
            continue

        if not text:
            continue

        chunks = chunk_text(text, chunk_size=400, overlap=40)

        for i, chunk in enumerate(chunks):
            section = detect_section(chunk)

            all_chunks.append({
                "source": filename,
                "chunk_id": i,
                "text": chunk,
                "section": section
            })

    print(f"Total chunks produced: {len(all_chunks)}")
    return all_chunks