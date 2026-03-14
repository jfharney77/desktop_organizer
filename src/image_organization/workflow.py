"""
workflow.py

LangGraph StateGraph for the image organiser.

Why StateGraph instead of a ReAct agent?
-----------------------------------------
A ReAct agent asks the LLM to decide what tool to call next AND to pass
the results of one tool call as arguments to the next.  For this workflow
that means the LLM must copy a potentially large list of file paths from
the scan result into the move call.  Local models (llama3.2, etc.) reliably
drop or truncate that list, so images are never actually moved.

A StateGraph fixes this by carrying data through typed graph *state*:
the scan node writes found paths into state, and the move node reads them
directly — the LLM is never involved in the data handoff.

model_config.py is kept for future nodes that genuinely need LLM reasoning
(e.g. de-duplicating, tagging, or summarising results).
"""

from typing import List, TypedDict

from langgraph.graph import END, StateGraph

from image_organization.tools import IMAGE_EXTENSIONS, _move_images_impl, _scan_images_impl


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class OrganizerState(TypedDict):
    source_dir: str
    destination_dir: str
    ignored_log: str
    moved_log: str
    retain_copy: bool
    extensions: List[str]
    found_images: List[str]
    ignored_images: List[str]
    summary: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def scan_node(state: OrganizerState) -> dict:
    """Discover image files matching configured extensions; write ignored list to log file."""
    result = _scan_images_impl(state["source_dir"], state["ignored_log"], set(state.get("extensions", IMAGE_EXTENSIONS)))
    return {
        "found_images": result.get("found", []),
        "ignored_images": result.get("ignored", []),
    }


def move_node(state: OrganizerState) -> dict:
    """Move all found images to the destination directory."""
    found = state.get("found_images", [])
    if not found:
        return {"summary": "Scan complete — no images found to move."}
    result = _move_images_impl(
        found,
        state["destination_dir"],
        moved_log=state.get("moved_log", ""),
        retain_copy=state.get("retain_copy", False),
    )
    return {"summary": result["summary"]}


# ---------------------------------------------------------------------------
# Graph wiring
# ---------------------------------------------------------------------------

def _build_graph():
    graph = StateGraph(OrganizerState)
    graph.add_node("scan", scan_node)
    graph.add_node("move", move_node)
    graph.set_entry_point("scan")
    graph.add_edge("scan", "move")
    graph.add_edge("move", END)
    return graph.compile()


# ---------------------------------------------------------------------------
# Public entry point (called by api.py and main.py)
# ---------------------------------------------------------------------------

def run_workflow(
    source_dir: str,
    destination_dir: str,
    ignored_log: str,
    moved_log: str = "",
    retain_copy: bool = False,
    extensions: List[str] = list(IMAGE_EXTENSIONS),
    model_name: str = "llama3.2",   # reserved for future LLM nodes
    temperature: float = 0.0,        # reserved for future LLM nodes
) -> str:
    """Run the organiser graph and return a human-readable summary."""
    app = _build_graph()

    final_state = app.invoke({
        "source_dir": source_dir,
        "destination_dir": destination_dir,
        "ignored_log": ignored_log,
        "moved_log": moved_log,
        "retain_copy": retain_copy,
        "extensions": extensions,
        "found_images": [],
        "ignored_images": [],
        "summary": "",
    })

    found_count   = len(final_state.get("found_images", []))
    ignored_count = len(final_state.get("ignored_images", []))
    move_summary  = final_state.get("summary", "")

    return (
        f"{move_summary}\n"
        f"Images found: {found_count}  |  ignored (in git repos): {ignored_count}"
    )
