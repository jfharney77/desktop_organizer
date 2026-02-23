"""
model_config.py

Single place to configure the LLM used by the LangGraph workflow.
Swap out the model here without touching the agent or tools.
"""

from langchain_ollama import ChatOllama


def get_model(model_name: str = "llama3.2", temperature: float = 0.0) -> ChatOllama:
    """Return a ChatOllama instance bound to the given model."""
    return ChatOllama(
        model=model_name,
        temperature=temperature,
    )
