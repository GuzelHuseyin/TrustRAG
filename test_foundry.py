import os
import openai
from foundry_local_sdk import Configuration, FoundryLocalManager


def main():
    print("Starting Foundry Local engine...")

    try:
        config = Configuration(app_name="TrustRag")
        FoundryLocalManager.initialize(config)
        manager = FoundryLocalManager.instance

        print("Checking models and loading into available hardware (VRAM/RAM)...")
        print("Note: If a hardware profile is missing, a short optimization step may occur...")

        chat_model = manager.catalog.get_model("phi-3.5-mini")
        chat_model.download()
        chat_model.load()

        embed_model = manager.catalog.get_model("qwen3-embedding-0.6b")
        embed_model.download()
        embed_model.load()

        print("Starting local API server...")
        manager.start_web_service()

        server_url = manager.urls[0].rstrip('/') if manager.urls else "http://localhost:8080"

        client = openai.OpenAI(
            base_url=f"{server_url}/v1",
            api_key="local-key"
        )

        test_prompt = "Hello! I am building a local RAG assistant. Respond with 'Hi' if you are working."

        print(f"Testing chat model ({chat_model.id})...")

        response = client.chat.completions.create(
            model=chat_model.id,
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=30
        )

        print(f"Model response: {response.choices[0].message.content}")

        print(f"Testing embedding model ({embed_model.id})...")

        embedding_response = client.embeddings.create(
            model=embed_model.id,
            input="RAG systems help securely manage and query data."
        )

        vector = embedding_response.data[0].embedding

        print(f"Embedding generation successful. Vector size: {len(vector)}")
        print(f"First 3 vector values: {vector[:3]}")

        print("Pipeline execution completed successfully.")

    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    main()