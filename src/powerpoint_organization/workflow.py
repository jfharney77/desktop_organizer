"""
workflow.py

LangGraph StateGraph for the PowerPoint organizer.

Why StateGraph instead of a ReAct agent?
-----------------------------------------
A ReAct agent asks the LLM to decide what tool to call next AND to pass
the results of one tool call as arguments to the next.  For this workflow
that means the LLM must copy a potentially large list of file paths from
the scan result into the move call.  Local models (llama3.2, etc.) reliably
drop or truncate that list, so files are never actually moved.

A StateGraph fixes this by carrying data through typed graph *state*:
the scan node writes found paths into state, and the move node reads them
directly — the LLM is never involved in the data handoff.
"""

from typing import List, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from powerpoint_organization.tools import _move_pptx_impl, _scan_pptx_impl, make_configured_tools


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------

class PowerpointOrganizerState(TypedDict):
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

def scan_node(state: PowerpointOrganizerState) -> dict:
    """Discover PowerPoint files; write ignored list to log file."""
    result = _scan_pptx_impl(state["source_dir"], state["ignored_log"])
    return {
        "found_files": result.get("found", []),
        "ignored_files": result.get("ignored", []),
    }


def move_node(state: PowerpointOrganizerState) -> dict:
    """Move all found PowerPoint files to the destination directory."""
    found = state.get("found_files", [])
    if not found:
        return {"summary": "Scan complete — no PowerPoint files found to move."}
    result = _move_pptx_impl(
        found,
        state["destination_dir"],
        moved_log=state.get("moved_log", ""),
        retain_copy=state.get("retain_copy", False),
    )
    return {"summary": result["summary"]}


# ---------------------------------------------------------------------------
# Graph wiring — StateGraph (direct function calls, no LLM)
# ---------------------------------------------------------------------------

def _build_graph():
    graph = StateGraph(PowerpointOrganizerState)
    graph.add_node("scan", scan_node)
    graph.add_node("move", move_node)
    graph.set_entry_point("scan")
    graph.add_edge("scan", "move")
    graph.add_edge("move", END)
    return graph.compile()


# ---------------------------------------------------------------------------
# Agent graph (ReAct — LLM dispatches tool calls)
# ---------------------------------------------------------------------------

def _build_agent_graph(
    source_dir: str,
    destination_dir: str,
    ignored_log: str,
    moved_log: str,
    retain_copy: bool,
    model_name: str,
    temperature: float,
):
    """
    Build a ReAct agent that uses the LLM to decide when and how to call the
    scan and move tools.  Config parameters are baked into the tools so the
    LLM only needs to reason about directory paths.

    Note: local models may struggle to relay large file-path lists between
    tool calls.  Use use_agent=false for more reliable operation.
    """
    from langgraph.prebuilt import create_react_agent
    from model_config import get_text_model

    scan_tool, move_tool = make_configured_tools(ignored_log, moved_log, retain_copy)
    model = get_text_model(model_name, temperature)
    return create_react_agent(model=model, tools=[scan_tool, move_tool])


# ---------------------------------------------------------------------------
# Public entry point (called by api.py and main.py)
# ---------------------------------------------------------------------------

def run_workflow(
    source_dir: str,
    destination_dir: str,
    ignored_log: str,
    moved_log: str = "",
    retain_copy: bool = False,
    use_agent: bool = False,
    model_name: str = "llama3.2",
    temperature: float = 0.0,
) -> str:
    """Run the PowerPoint organizer graph and return a human-readable summary."""
    if use_agent:
        app = _build_agent_graph(
            source_dir, destination_dir, ignored_log, moved_log,
            retain_copy, model_name, temperature,
        )
        result = app.invoke({
            "messages": [
                SystemMessage(content=(
                    "You are a PowerPoint file organizer. "
                    "You have two tools: scan_powerpoints_agent and move_powerpoints_agent. "
                    "You MUST call these tools — never guess or fabricate directory contents. "
                    "Step 1: call scan_powerpoints_agent to discover files. "
                    "Step 2: call move_powerpoints_agent with the exact paths returned by the scan. "
                    "Do not produce a final answer until both tool calls are complete."
                )),
                HumanMessage(content=(
                    f"Organize PowerPoint files step by step:\n"
                    f"1. Call scan_powerpoints_agent with directory='{source_dir}'\n"
                    f"2. Call move_powerpoints_agent with the found paths and destination_directory='{destination_dir}'\n"
                    f"3. Report how many files were moved and any errors."
                )),
            ]
        })
        return result["messages"][-1].content

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
        f"PowerPoint files found: {found_count}  |  ignored (in git repos): {ignored_count}"
    )
