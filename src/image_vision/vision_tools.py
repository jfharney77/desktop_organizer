"""
vision_tools.py

Tool and implementation for describing an image using llama3.2-vision via Ollama.

Design note — preventing hallucination
---------------------------------------
The existence check is performed entirely in Python before any call is made to
the LLM.  If the file cannot be found the function returns an error dict
immediately; the model is never invoked, so it has no opportunity to fabricate
a description.

Temperature is fixed at 0.0 for deterministic output, and the system prompt
explicitly instructs the model to describe only what is directly visible.
"""

import base64
from pathlib import Path
from typing import Annotated

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from model_config import VISION_MODEL, get_vision_model

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
}

SYSTEM_PROMPT = (
    "You are an image analysis assistant. "
    "Describe ONLY what you can directly observe in the image. "
    "Do NOT speculate, infer, or add any information that is not clearly visible. "
    "If you cannot determine something with confidence, say so explicitly."
)


# ---------------------------------------------------------------------------
# Pure-Python implementation (called directly by the StateGraph and by @tool)
# ---------------------------------------------------------------------------

def _describe_image_impl(
    image_name: str,
    search_directory: str,
    model_name: str = VISION_MODEL,
) -> dict:
    """
    Locate *image_name* inside *search_directory* and return a vision-model
    description.  Returns an error dict (found=False) without touching the
    LLM if the file cannot be located or is not a supported image type.
    """
    search_dir = Path(search_directory)

    # --- 1. Resolve path (no LLM involved) ---
    candidate = search_dir / image_name
    if not candidate.exists():
        # Recursive fallback — still no LLM
        matches = list(search_dir.rglob(image_name))
        if not matches:
            return {
                "found": False,
                "image_path": None,
                "description": None,
                "error": (
                    f"Image '{image_name}' was not found in '{search_directory}'. "
                    "Please check the filename and try again."
                ),
            }
        candidate = matches[0]

    suffix = candidate.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return {
            "found": False,
            "image_path": str(candidate),
            "description": None,
            "error": (
                f"'{candidate.name}' is not a supported image type. "
                f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}."
            ),
        }

    # --- 2. Encode image ---
    mime_type = SUPPORTED_EXTENSIONS[suffix]
    with candidate.open("rb") as fh:
        image_b64 = base64.b64encode(fh.read()).decode()

    # --- 3. Call vision model ---
    model = get_vision_model(model_name)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
            },
            {
                "type": "text",
                "text": "Please describe this image in detail.",
            },
        ]),
    ]

    response = model.invoke(messages)
    description = response.content if hasattr(response, "content") else str(response)

    return {
        "found": True,
        "image_path": str(candidate),
        "description": description,
        "error": None,
    }


# ---------------------------------------------------------------------------
# LangChain @tool wrapper (available for future agent-style use)
# ---------------------------------------------------------------------------

@tool
def describe_image(
    image_name: Annotated[str, "Filename of the image to describe (e.g. 'photo.jpg')"],
    search_directory: Annotated[str, "Absolute path to the directory to search in"],
) -> dict:
    """
    Describe an image using the llama3.2-vision model.

    Looks for *image_name* inside *search_directory* (recursively if needed).
    Returns a description of the image if found, or a clear error message if
    the file does not exist — the model is never called when the file is absent.
    """
    return _describe_image_impl(image_name, search_directory)
