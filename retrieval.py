import sqlite3
import json
import numpy as np

from embeddings import get_embedding

DB_NAME = "rag_database.db"


def cosine_similarity(v1, v2):
    """Compute cosine similarity between two embedding vectors."""
    v1 = np.array(v1)
    v2 = np.array(v2)

    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0

    return dot_product / (norm_v1 * norm_v2)


def detect_query_type(query: str) -> str:
    """Classify query intent for retrieval routing."""
    q = query.lower()

    if any(k in q for k in ["email", "mail", "e-posta", "contact", "iletişim"]):
        return "contact"

    if any(k in q for k in ["work", "where does", "deneyim", "tecrübe", "staj"]):
        return "experience"

    if any(k in q for k in ["skill", "skills", "yetenek", "teknik", "know"]):
        return "skills"

    if any(k in q for k in ["education", "eğitim", "university", "mezun", "okudu"]):
        return "education"

    return "general"


def fetch_documents(cursor, query_type: str):
    """Fetch relevant documents with optional filtering."""
    if query_type == "general":
        cursor.execute(
            "SELECT id, source, chunk_id, text, section, embedding FROM documents"
        )
        return cursor.fetchall()

    cursor.execute(
        """
        SELECT id, source, chunk_id, text, section, embedding
        FROM documents
        WHERE section = ?
        """,
        (query_type,),
    )

    rows = cursor.fetchall()

    if rows:
        return rows

    print(f"Warning: No documents found for section '{query_type}', falling back to full search.")

    cursor.execute(
        "SELECT id, source, chunk_id, text, section, embedding FROM documents"
    )
    return cursor.fetchall()


def get_top_chunks(query, top_k=3, threshold=0.25):
    """Retrieve top-k relevant chunks using hybrid routing + cosine similarity."""

    query_type = detect_query_type(query)
    print(f"Query routed to category: {query_type}")

    query_vector = get_embedding(query)

    if not query_vector:
        print("Failed to generate query embedding.")
        return []

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        rows = fetch_documents(cursor, query_type)
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()

    if not rows:
        print("No documents available in database.")
        return []

    results = []

    for doc_id, source, chunk_id, text, section, embedding_str in rows:
        doc_vector = json.loads(embedding_str)
        similarity = cosine_similarity(query_vector, doc_vector)

        if similarity < threshold:
            continue

        results.append({
            "source": source,
            "section": section,
            "text": text,
            "similarity": similarity
        })

    results.sort(key=lambda x: x["similarity"], reverse=True)

    return results[:top_k]


if __name__ == "__main__":
    from foundry_local_sdk import Configuration, FoundryLocalManager

    print("Starting intelligent retrieval pipeline (Day 4).")

    try:
        config = Configuration(app_name="TrustRag")
        FoundryLocalManager.initialize(config)
        manager = FoundryLocalManager.instance

        embed_model = manager.catalog.get_model("qwen3-embedding-0.6b")
        embed_model.load()

        manager.start_web_service()

        test_queries = [
            "What is Hüseyin Güzel's email address?",
            "What technical skills does he have?"
        ]

        for query in test_queries:
            print("\n" + "-" * 60)
            print(f"Query: {query}")

            results = get_top_chunks(query, top_k=2, threshold=0.25)

            if not results:
                print("No relevant results found above similarity threshold.")
                continue

            print("Top results:")

            for i, r in enumerate(results, start=1):
                print(
                    f"\nResult {i} | Section: {r['section']} | Score: {r['similarity']:.4f}"
                )
                print(f"Source: {r['source']}")
                print(f"Text: {r['text']}")

    except Exception as e:
        print(f"Pipeline error: {e}")