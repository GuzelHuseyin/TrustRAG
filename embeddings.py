import time
from foundry_local_sdk import FoundryLocalManager
import openai


def get_embedding(text, model_name="qwen3-embedding-0.6b", max_retries=3, retry_delay=2):
    """
    Converts input text into an embedding vector using a local Foundry model.

    Retries on connection errors with a short delay, since the local
    Foundry server can occasionally drop a request under sustained load
    (e.g. when processing thousands of chunks back-to-back).
    """
    if not text or not text.strip():
        print("Embedding skipped: empty text input.")
        return []

    try:
        manager = FoundryLocalManager.instance
        server_url = manager.urls[0].rstrip('/') if manager.urls else "http://localhost:8080"
    except Exception as e:
        print(f"Embedding error (manager not available): {e}")
        return []

    client = openai.OpenAI(
        base_url=f"{server_url}/v1",
        api_key="local-key",
        timeout=30.0,  
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.embeddings.create(
                model=model_name,
                input=text.strip()
            )
            return response.data[0].embedding

        except Exception as e:
            print(f"Embedding error (attempt {attempt}/{max_retries}): {e}")

            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                print("Embedding failed after max retries, skipping this chunk.")
                return []

    return []