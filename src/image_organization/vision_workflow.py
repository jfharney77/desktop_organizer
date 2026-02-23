"""
vision_workflow.py

LangGraph StateGraph for describing a single image with llama3.2-vision.

Graph structure
---------------
  [check] --found--> [describe] --> END
         \\
          --not found-----------> END

The check node performs only Python-level file resolution — the LLM node
(describe) is structurally unreachable when the image does not exist, which
guarantees the model cannot hallucinate a description for a missing file.
"""

import base64
from pathlib import Path
from typing import Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from model_config import VISION_MODEL, get_vision_model
from image_organization.vision_tools import SUPPORTED_EXTENSIONS, SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class VisionState(TypedDict):
    image_name: str
    search_directory: str
    model_name: str
    # populated by nodes
    image_path: Optional[str]
    found: bool
    description: Optional[str]
    error: Optional[str]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def check_node(state: VisionState) -> dict:
    """
    Resolve the image path entirely in Python.
    Sets found=True and image_path if the file exists and is a supported type.
    Sets found=False and error if not — the LLM is never involved here.
    """
    search_dir = Path(state["search_directory"])
    image_name = state["image_name"]

    candidate = search_dir / image_name
    if not candidate.exists():
        matches = list(search_dir.rglob(image_name))
        if not matches:
            return {
                "found": False,
                "image_path": None,
                "error": (
                    f"Image '{image_name}' was not found in '{state['search_directory']}'. "
                    "Please check the filename and try again."
                ),
            }
        candidate = matches[0]

    suffix = candidate.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        return {
            "found": False,
            "image_path": str(candidate),
            "error": (
                f"'{candidate.name}' is not a supported image type. "
                f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}."
            ),
        }

    return {"found": True, "image_path": str(candidate), "error": None}


def describe_node(state: VisionState) -> dict:
    """
    Call the vision model.  Only reachable when check_node set found=True,
    so state['image_path'] is guaranteed to be a valid, readable image file.
    """
    image_path = Path(state["image_path"])
    mime_type = SUPPORTED_EXTENSIONS[image_path.suffix.lower()]

    with image_path.open("rb") as fh:
        image_b64 = base64.b64encode(fh.read()).decode()

    model = get_vision_model(state["model_name"])
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
    return {"description": description}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route_after_check(state: VisionState) -> str:
    return "describe" if state.get("found") else END


# ---------------------------------------------------------------------------
# Graph wiring
# ---------------------------------------------------------------------------

def _build_vision_graph():
    graph = StateGraph(VisionState)
    graph.add_node("check", check_node)
    graph.add_node("describe", describe_node)
    graph.set_entry_point("check")
    graph.add_conditional_edges("check", _route_after_check)
    graph.add_edge("describe", END)
    return graph.compile()


# ---------------------------------------------------------------------------
# Public entry point (called by api.py)
# ---------------------------------------------------------------------------

def run_vision_workflow(
    image_name: str,
    search_directory: str,
    model_name: str = VISION_MODEL,
) -> dict:
    """
    Run the vision graph and return a dict with keys:
      found, image_path, description, error
    """
    app = _build_vision_graph()

    final_state = app.invoke({
        "image_name": image_name,
        "search_directory": search_directory,
        "model_name": model_name,
        "image_path": None,
        "found": False,
        "description": None,
        "error": None,
    })

    return {
        "found":       final_state.get("found", False),
        "image_path":  final_state.get("image_path"),
        "description": final_state.get("description"),
        "error":       final_state.get("error"),
    }
