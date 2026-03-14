"""
workflow.py

LangGraph StateGraph for the git repository organiser.

Uses the same StateGraph pattern as the other organizers — directory paths
are carried through typed graph state so the LLM is never involved in the
data handoff between the scan and move steps.
"""

from typing import List, TypedDict

from langgraph.graph import END, StateGraph

from git_organization.tools import _move_git_repos_impl, _scan_git_repos_impl


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class GitOrganizerState(TypedDict):
    source_dir: str
    destination_dir: str
    ignored_log: str
    moved_log: str
    retain_copy: bool
    found_repos: List[str]
    summary: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def scan_node(state: GitOrganizerState) -> dict:
    """Discover git repositories in source_dir, or pass through pre-selected repos."""
    if state.get("found_repos"):
        return {}  # repos already supplied by the caller — skip scan
    result = _scan_git_repos_impl(state["source_dir"], state["ignored_log"])
    return {"found_repos": result.get("found", [])}


def move_node(state: GitOrganizerState) -> dict:
    """Move all found git repositories to the destination directory."""
    found = state.get("found_repos", [])
    if not found:
        return {"summary": "Scan complete — no git repositories found to move."}
    result = _move_git_repos_impl(
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
    graph = StateGraph(GitOrganizerState)
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
    repo_paths: List[str] = [],
) -> str:
    """Run the git organiser graph and return a human-readable summary.

    If *repo_paths* is provided the scan step is skipped and only those
    repositories are moved.
    """
    app = _build_graph()

    final_state = app.invoke({
        "source_dir":      source_dir,
        "destination_dir": destination_dir,
        "ignored_log":     ignored_log,
        "moved_log":       moved_log,
        "retain_copy":     retain_copy,
        "found_repos":     list(repo_paths),
        "summary":         "",
    })

    found_count  = len(final_state.get("found_repos", []))
    move_summary = final_state.get("summary", "")

    return f"{move_summary}\nRepositories found: {found_count}"
