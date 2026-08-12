"""LangGraph State Machine Graph Orchestrator for Beacon Compliance (graph.py).

Connects:
Node 1 (Ingest) -> Node 1.5 (Classify) -> Node 3 (Calculator) -> [Conditional: Halt if Breach else Node 2]
-> Node 2 (Writer) -> Node 4 (Auditor) -> Node 5 (Assembler) -> END

Uses genuine LangGraph StateGraph pipeline compilation with conditional edges.
"""

from typing import Any, Literal

from backend.src.agents.node_assembler import run_node_assembler
from backend.src.agents.node_auditor import run_node_auditor
from backend.src.agents.node_calculator import run_node_calculator
from backend.src.agents.node_classify import run_node_classify
from backend.src.agents.node_ingest import run_node_ingest
from backend.src.agents.node_writer import run_node_writer
from backend.src.agents.state import BeaconComplianceState
from backend.src.core.telemetry import default_tracer
from langgraph.graph import END, START, StateGraph


def route_after_calculator(state: BeaconComplianceState) -> Literal["node_writer", "__end__"]:
    """Conditional edge evaluating income threshold breach state (Red-Line 5)."""
    if state.get("income_threshold_breach"):
        return END
    return "node_writer"


def route_after_ingest(state: BeaconComplianceState) -> Literal["node_classify", "__end__"]:
    """Conditional edge evaluating ingest-layer income threshold breach (Red-Line 5)."""
    if state.get("income_threshold_breach"):
        return END
    return "node_classify"


def build_compliance_graph() -> StateGraph:
    """Build and compile genuine LangGraph StateGraph workflow DAG."""
    workflow = StateGraph(BeaconComplianceState)

    # Add Nodes
    workflow.add_node("node_ingest", run_node_ingest)
    workflow.add_node("node_classify", run_node_classify)
    workflow.add_node("node_calculator", run_node_calculator)
    workflow.add_node("node_writer", run_node_writer)
    workflow.add_node("node_auditor", run_node_auditor)
    workflow.add_node("node_assembler", run_node_assembler)

    # Add Edges
    workflow.add_edge(START, "node_ingest")
    workflow.add_conditional_edges(
        "node_ingest",
        route_after_ingest,
        {
            "node_classify": "node_classify",
            END: END,
        },
    )
    workflow.add_edge("node_classify", "node_calculator")
    workflow.add_conditional_edges(
        "node_calculator",
        route_after_calculator,
        {
            "node_writer": "node_writer",
            END: END,
        },
    )
    workflow.add_edge("node_writer", "node_auditor")
    workflow.add_edge("node_auditor", "node_assembler")
    workflow.add_edge("node_assembler", END)

    return workflow


class BeaconComplianceGraph:
    """State machine pipeline executor for Beacon Compliance."""

    def __init__(self) -> None:
        self.workflow = build_compliance_graph()
        self.app = self.workflow.compile()

    def run(
        self, initial_state: BeaconComplianceState, config: dict[str, Any] | None = None
    ) -> BeaconComplianceState:
        """Run compiled LangGraph StateGraph execution with optional telemetry callbacks."""
        run_config = config.copy() if config else {}
        if default_tracer.is_enabled():
            callback = default_tracer.get_langchain_callback()
            if callback:
                existing_callbacks = run_config.get("callbacks", [])
                run_config["callbacks"] = [*list(existing_callbacks), callback]
        return self.app.invoke(initial_state, config=run_config if run_config else None)
