import logging

import openai
from foundry_local_sdk import Configuration, FoundryLocalManager

from retrieval import get_top_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

CHAT_MODEL = "phi-3.5-mini"
EMBEDDING_MODEL = "qwen3-embedding-0.6b"

TOP_K = 3
SIMILARITY_THRESHOLD = 0.25
TEMPERATURE = 0.3

SYSTEM_PROMPT = (
    "Sen profesyonel bir yapay zeka asistanısın. "
    "Kullanıcının sorularını yalnızca sana verilen kaynak metinleri kullanarak cevapla. "
    "Kaynaklarda cevap bulunmuyorsa, 'Bu bilgiye sahip değilim.' şeklinde yanıt ver. "
    "Yanıtların kısa, doğru ve açık olmalıdır."
)


def build_context(chunks: list[dict]) -> str:
    """
    Retrieved document chunks are converted into a single context string
    that will be supplied to the language model.
    """
    return "\n\n".join(
        (
            f"Source: {chunk['source']}\n"
            f"Section: {chunk['section'].upper()}\n"
            f"{chunk['text']}"
        )
        for chunk in chunks
    )


def get_client() -> openai.OpenAI:
    """
    Creates an OpenAI-compatible client connected to the local Foundry service.
    """
    manager = FoundryLocalManager.instance

    server_url = (
        manager.urls[0].rstrip("/")
        if manager.urls
        else "http://localhost:8080"
    )

    return openai.OpenAI(
        base_url=f"{server_url}/v1",
        api_key="local-key",
    )


def generate_answer(query: str) -> str:
    """
    Retrieves the most relevant document chunks and generates an answer
    using the local language model.
    """
    logger.info("Searching relevant documents...")

    chunks = get_top_chunks(
        query=query,
        top_k=TOP_K,
        threshold=SIMILARITY_THRESHOLD,
    )

    if not chunks:
        return "Belgelerde bu soruya ilişkin bir bilgi bulunamadı."

    context = build_context(chunks)

    try:
        client = get_client()

        logger.info("Generating response...")

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"KAYNAKLAR:\n{context}\n\n"
                        f"SORU:\n{query}"
                    ),
                },
            ],
            temperature=TEMPERATURE,
            max_tokens=512, 
        )

        return response.choices[0].message.content

    except Exception as exc:
        logger.exception("Response generation failed.")
        return f"Response generation failed: {exc}"


def initialize_models() -> None:
    """
    Loads required models and starts the local inference service.
    """
    config = Configuration(app_name="TrustRag")

    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    logger.info("Loading embedding model...")
    manager.catalog.get_model(EMBEDDING_MODEL).load()

    logger.info("Loading chat model...")
    manager.catalog.get_model(CHAT_MODEL).load()

    logger.info("Starting local inference service...")
    manager.start_web_service()


def main() -> None:
    """
    Entry point for local testing.
    """
    try:
        initialize_models()

        query = "Hüseyin Güzel'in e-posta adresi nedir?"
        answer = generate_answer(query)

        print("\nGenerated Answer")
        print("-" * 60)
        print(answer)

    except Exception:
        logger.exception("Application terminated unexpectedly.")


if __name__ == "__main__":
    main()