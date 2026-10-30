from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from core.state import TransactionState
from config.settings import RISK_THRESHOLD, HIGH_VALUE_THRESHOLD_USD
from agents.nodes import (
    triage_node,
    create_compliance_agent_node,
    fx_routing_agent_node,
    document_verification_agent_node,
    risk_evaluation_node,
    human_review_node,
    execution_node
)


def route_after_evaluation(state: TransactionState) -> str:
    if state["overall_risk_score"] > RISK_THRESHOLD or state["amount_usd"] > HIGH_VALUE_THRESHOLD_USD:
        return "human_review"
    return "execution"


def route_after_human_review(state: TransactionState) -> str:
    if state.get("status") == "APPROVED":
        return "execution"
    return END


def build_workflow(qdrant_db):
    workflow = StateGraph(TransactionState)

    # Add Nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("compliance_agent", create_compliance_agent_node(qdrant_db))
    workflow.add_node("fx_agent", fx_routing_agent_node)
    workflow.add_node("doc_agent", document_verification_agent_node)
    workflow.add_node("risk_evaluator", risk_evaluation_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("execution", execution_node)

    # Build Parallel Edges
    workflow.add_edge(START, "triage")
    workflow.add_edge("triage", "compliance_agent")
    workflow.add_edge("triage", "fx_agent")
    workflow.add_edge("triage", "doc_agent")

    workflow.add_edge("compliance_agent", "risk_evaluator")
    workflow.add_edge("fx_agent", "risk_evaluator")
    workflow.add_edge("doc_agent", "risk_evaluator")

    # Conditional Branching
    workflow.add_conditional_edges("risk_evaluator", route_after_evaluation, {
        "human_review": "human_review",
        "execution": "execution"
    })
    
    workflow.add_conditional_edges("human_review", route_after_human_review, {
        "execution": "execution",
        END: END
    })
    
    workflow.add_edge("execution", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)