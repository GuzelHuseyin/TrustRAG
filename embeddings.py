from foundry_local_sdk import FoundryLocalManager
import openai


def get_embedding(text, model_name="qwen3-embedding-0.6b"):
    """
    Converts input text into an embedding vector using a local Foundry model.
    """
    try:
        manager = FoundryLocalManager.instance

        server_url = manager.urls[0].rstrip('/') if manager.urls else "http://localhost:8080"

        client = openai.OpenAI(
            base_url=f"{server_url}/v1",
            api_key="local-key"
        )

        response = client.embeddings.create(
            model=model_name,
            input=text
        )

        return response.data[0].embedding

    except Exception as e:
        print(f"Embedding error: {e}")
        return []