import sqlite3
import json
import time

from embeddings import get_embedding
from ingestion import process_documents
from foundry_local_sdk import Configuration, FoundryLocalManager

DB_NAME = "rag_database.db"
COMMIT_EVERY = 25       # büyük veri setlerinde kayıp olmaması için periyodik kayıt
SLEEP_BETWEEN_CALLS = 0.05  # yerel sunucuyu art arda isteklerle boğmamak için küçük bekleme


def setup_database():
    """Recreates SQLite schema for clean ingestion run."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS documents")

    cursor.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            chunk_id INTEGER,
            text TEXT,
            section TEXT,
            embedding TEXT
        )
    """)

    conn.commit()
    return conn


def save_to_db(chunks):
    """Generate embeddings and store structured chunks in SQLite.

    Commits periodically (every COMMIT_EVERY rows) instead of only at the
    end, so a crash or interruption on a large dataset (e.g. Wikipedia
    parquet) doesn't wipe out all progress made so far. Also sleeps
    briefly between calls so the local Foundry server isn't hit with a
    continuous burst of requests, which can otherwise cause connection
    errors partway through a large run.
    """

    conn = setup_database()
    cursor = conn.cursor()

    total = len(chunks)
    print(f"Processing {total} chunks for vectorization...")

    saved_count = 0
    failed_count = 0

    for i, chunk in enumerate(chunks, start=1):

        print(
            f"Processing {i}/{total} | "
            f"{chunk['source']} | section={chunk['section']}"
        )

        try:
            vector = get_embedding(chunk["text"])
        except Exception as e:
            print(f"Embedding failed: {e}")
            failed_count += 1
            continue

        if not vector:
            failed_count += 1
            continue

        cursor.execute(
            """
            INSERT INTO documents (source, chunk_id, text, section, embedding)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                chunk["source"],
                chunk["chunk_id"],
                chunk["text"],
                chunk["section"],
                json.dumps(vector),
            ),
        )

        saved_count += 1

        if saved_count % COMMIT_EVERY == 0:
            conn.commit()
            print(f"Checkpoint: {saved_count} chunks saved so far ({failed_count} failed).")

        time.sleep(SLEEP_BETWEEN_CALLS)

    conn.commit()
    conn.close()

    print(
        f"Vector database build completed. "
        f"Saved: {saved_count}/{total} | Failed: {failed_count}/{total}"
    )


def main():
    try:
        print("Initializing Foundry Local runtime...")

        config = Configuration(app_name="TrustRag")
        FoundryLocalManager.initialize(config)
        manager = FoundryLocalManager.instance

        embed_model = manager.catalog.get_model("qwen3-embedding-0.6b")
        embed_model.load()

        manager.start_web_service()

        chunks = process_documents("data", parquet_max_rows=5)

        if not chunks:
            print("No documents found.")
            return

        save_to_db(chunks)

    except Exception as e:
        print(f"Pipeline error: {e}")


if __name__ == "__main__":
    main()