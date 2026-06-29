import sqlite3
import json

from embeddings import get_embedding
from ingestion import process_documents
from foundry_local_sdk import Configuration, FoundryLocalManager

DB_NAME = "rag_database.db"


def setup_database():
    """
    Initialize SQLite database and create documents table if it does not exist.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            chunk_id INTEGER,
            text TEXT,
            embedding TEXT
        )
    """)

    conn.commit()
    return conn


def save_to_db(chunks):
    """
    Generate embeddings for text chunks and store them in SQLite database.
    """
    conn = setup_database()
    cursor = conn.cursor()

    total = len(chunks)
    print(f"Processing {total} chunks for embedding and storage.")

    for i, chunk in enumerate(chunks, start=1):
        print(f"Processing {i}/{total}: {chunk['source']} (chunk {chunk['chunk_id']})")

        vector = get_embedding(chunk["text"])

        if not vector:
            print(f"Skipping chunk due to missing embedding: {chunk['source']} - {chunk['chunk_id']}")
            continue

        cursor.execute(
            """
            INSERT INTO documents (source, chunk_id, text, embedding)
            VALUES (?, ?, ?, ?)
            """,
            (
                chunk["source"],
                chunk["chunk_id"],
                chunk["text"],
                json.dumps(vector),
            ),
        )

    conn.commit()
    conn.close()

    print("Database update completed successfully.")


if __name__ == "__main__":
    print("Starting SQLite vector database pipeline (Day 3).")

    try:
        print("Initializing Foundry Local runtime...")

        config = Configuration(app_name="TrustRag")
        FoundryLocalManager.initialize(config)
        manager = FoundryLocalManager.instance

        embed_model = manager.catalog.get_model("qwen3-embedding-0.6b")
        embed_model.load()

        manager.start_web_service()

        chunks = process_documents("data")

        if not chunks:
            print("No documents found in data directory.")
        else:
            save_to_db(chunks)

    except Exception as e:
        print(f"Pipeline failed with error: {e}")