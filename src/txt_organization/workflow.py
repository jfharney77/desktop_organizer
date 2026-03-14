"""
workflow.py

LangGraph StateGraph for the text file organiser.

Uses the same StateGraph pattern as image_organization and
powerpoint_organization — file paths are carried through typed graph state
so the LLM is never involved in the data handoff between scan and move steps.
"""

from typing import List, TypedDict

from langgraph.graph import END, StateGraph

from txt_organization.tools import _move_txt_impl, _scan_txt_impl


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class TxtOrganizerState(TypedDict):
    source_dir: str
    destination_dir: str
    ignored_log: str
    moved_log: str
    retain_copy: bool
    found_files: List[str]
    ignored_files: List[str]
    summary: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def scan_node(state: TxtOrganizerState) -> dict:
    """Discover .txt files; write ignored list to log file."""
    result = _scan_txt_impl(state["source_dir"], state["ignored_log"])
    return {
        "found_files": result.get("found", []),
        "ignored_files": result.get("ignored", []),
    }


def move_node(state: TxtOrganizerState) -> dict:
    """Move all found text files to the destination directory."""
    found = state.get("found_files", [])
    if not found:
        return {"summary": "Scan complete — no text files found to move."}
    result = _move_txt_impl(
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
    graph = StateGraph(TxtOrganizerState)
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
) -> str:
    """Run the text file organiser graph and return a human-readable summary."""
    app = _build_graph()

    final_state = app.invoke({
        "source_dir": source_dir,
        "destination_dir": destination_dir,
        "ignored_log": ignored_log,
        "moved_log": moved_log,
        "retain_copy": retain_copy,
        "found_files": [],
        "ignored_files": [],
        "summary": "",
    })

    found_count   = len(final_state.get("found_files", []))
    ignored_count = len(final_state.get("ignored_files", []))
    move_summary  = final_state.get("summary", "")

    return (
        f"{move_summary}\n"
        f"Files found: {found_count}  |  ignored (in git repos): {ignored_count}"
    )
