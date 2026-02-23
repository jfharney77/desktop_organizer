"""
model_config.py

Single place to configure the LLMs used by the LangGraph workflows.
Swap out a model here without touching the agent or tools.

Run directly to verify both models are reachable:
    python model_config.py
"""

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

DEFAULT_MODEL = "llama3.2"
VISION_MODEL  = "llama3.2-vision"


def get_text_model(model_name: str = DEFAULT_MODEL, temperature: float = 0.0) -> ChatOllama:
    """Return a ChatOllama instance for text-to-text tasks."""
    return ChatOllama(
        model=model_name,
        temperature=temperature,
    )


def get_vision_model(model_name: str = VISION_MODEL, temperature: float = 0.0) -> ChatOllama:
    """Return a ChatOllama instance for vision (image-to-text) tasks."""
    return ChatOllama(
        model=model_name,
        temperature=temperature,
    )


def main() -> None:
    # --- Text model ---
    print(f"Testing text model  : {DEFAULT_MODEL}")
    print("-" * 40)
    text_response = get_text_model().invoke([
        HumanMessage(content="In one sentence, what is the capital of France?")
    ])
    print(text_response.content)

    print()

    # --- Vision model ---
    print(f"Testing vision model: {VISION_MODEL}")
    print("-" * 40)
    vision_response = get_vision_model().invoke([
        HumanMessage(content="What can you do with an image? Answer in one sentence.")
    ])
    print(vision_response.content)


if __name__ == "__main__":
    main()
