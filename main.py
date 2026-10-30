import os
import operator
from typing import Dict, List, Optional, Any, Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Ensure API Key is available
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key")


# ---------------------------------------------------------------------------
# 1. State Definition (with Operator Add Reducer for Parallel Agents)
# ---------------------------------------------------------------------------
class TransactionState(TypedDict):
    transaction_id: str
    amount_usd: float
    sender_name: str
    receiver_name: str
    destination_country: str
    trade_document_summary: str
    
    # Agent Analysis Results
    sanction_flag: bool
    sanction_confidence: float  # 0.0 to 1.0 (Higher = safer / false positive)
    optimal_rail: Optional[str]
    fx_fee_usd: Optional[float]
    doc_discrepancy_found: bool
    
    # Combined Policy Evaluation
    overall_risk_score: float  # 0.0 (Safe) to 1.0 (Critical Risk)
    status: str                # "PROCESSING", "APPROVED", "PENDING_HUMAN_REVIEW", "REJECTED"
    human_approval: Optional[bool]
    
    # Reducer fix: operator.add allows concurrent nodes to append notes safely
    remediation_notes: Annotated[List[str], operator.add]


# ---------------------------------------------------------------------------
# 2. Agent Node Definitions
# ---------------------------------------------------------------------------
llm = ChatOpenAI(model="gpt-4o", temperature=0)


def triage_node(state: TransactionState) -> Dict[str, Any]:
    """Ingests transaction state and prepares initial audit trail."""
    print(f"\n[TRIAGE] Ingesting Transaction: {state['transaction_id']} (${state['amount_usd']:,})")
    return {
        "status": "PROCESSING",
        "remediation_notes": [f"Transaction {state['transaction_id']} ingested for automated multi-agent analysis."]
    }


def compliance_agent_node(state: TransactionState) -> Dict[str, Any]:
    """Evaluates potential sanction matches and false positives."""
    print("[COMPLIANCE AGENT] Analyzing sanction records & entity matching...")
    
    if "Acme Corp" in state['receiver_name'] and state['destination_country'] != "SanctionedLand":
        sanction_flag = False
        confidence_clean = 0.95
        reason = "Receiver matched common commercial entity name; no watchlist hit on destination."
    else:
        sanction_flag = True
        confidence_clean = 0.35
        reason = "Receiver name matched high-risk entity watchlist flag."

    return {
        "sanction_flag": sanction_flag,
        "sanction_confidence": confidence_clean,
        "remediation_notes": [f"Compliance Check: {reason}"]
    }


def fx_routing_agent_node(state: TransactionState) -> Dict[str, Any]:
    """Determines optimal settlement network (SWIFT vs. Visa Direct vs. Mastercard Send vs. DLT)."""
    print("[FX & ROUTING AGENT] Evaluating settlement rails & liquidity...")
    
    amount = state["amount_usd"]
    destination = state["destination_country"]
    
    if amount < 100000 and destination in ["GB", "EU", "US", "SG"]:
        rail = "Visa Direct / Mastercard Send"
        fee = amount * 0.0015
    elif amount >= 100000:
        rail = "SWIFT ISO 20022 Direct Liquidity"
        fee = amount * 0.0005
    else:
        rail = "DLT / Ripple Settlement Rail"
        fee = amount * 0.0010
        
    return {
        "optimal_rail": rail,
        "fx_fee_usd": fee,
        "remediation_notes": [f"FX Routing Selected: {rail} (Est. Fee: ${fee:,.2f})"]
    }


def document_verification_agent_node(state: TransactionState) -> Dict[str, Any]:
    """Cross-checks trade finance documents against payment amounts and entities."""
    print("[DOC VERIFICATION AGENT] Cross-verifying trade invoice metadata...")
    
    doc_text = state.get("trade_document_summary", "")
    discrepancy = False
    reason = "Trade invoices match transaction line items."
    
    if "mismatch" in doc_text.lower() or "discrepancy" in doc_text.lower():
        discrepancy = True
        reason = "Discrepancy detected between invoice value and transfer payload."
        
    return {
        "doc_discrepancy_found": discrepancy,
        "remediation_notes": [f"Document Verification: {reason}"]
    }


def risk_evaluation_node(state: TransactionState) -> Dict[str, Any]:
    """Synthesizes parallel agent outputs into a unified risk score."""
    print("[EVALUATOR] Calculating holistic risk score...")
    
    risk_score = 0.0
    
    if state.get("sanction_flag"):
        risk_score += 0.50
    if state.get("sanction_confidence", 1.0) < 0.70:
        risk_score += 0.25
    if state.get("doc_discrepancy_found"):
        risk_score += 0.30
    if state.get("amount_usd", 0) > 1000000:
        risk_score += 0.10

    risk_score = min(risk_score, 1.0)
    
    return {
        "overall_risk_score": risk_score,
        "remediation_notes": [f"Holistic Risk Score Computed: {risk_score:.2f}"]
    }


def human_review_node(state: TransactionState) -> Dict[str, Any]:
    """Handles flagged cases requiring manual intervention."""
    print("\n" + "="*60)
    print(" [HUMAN-IN-THE-LOOP] MANUAL REMEDIATION REQUIRED")
    print(f" Transaction ID : {state['transaction_id']}")
    print(f" Risk Score     : {state['overall_risk_score']:.2f}")
    print(" Audit Trail    :")
    for note in state.get("remediation_notes", []):
        print(f"  - {note}")
    print("="*60 + "\n")
    
    return {"status": "PENDING_HUMAN_REVIEW"}


def execution_node(state: TransactionState) -> Dict[str, Any]:
    """Executes transaction settlement via selected API rail."""
    print(f"[SETTLEMENT EXECUTION] Processing transfer of ${state['amount_usd']:,} via {state['optimal_rail']}...")
    
    return {
        "status": "APPROVED",
        "remediation_notes": [f"Settlement finalized successfully via {state['optimal_rail']}."]
    }


# ---------------------------------------------------------------------------
# 3. Conditional Routing Logic
# ---------------------------------------------------------------------------
def route_after_evaluation(state: TransactionState) -> str:
    """Routes to settlement execution or triggers Human-In-The-Loop review."""
    risk_threshold = 0.35
    high_value_limit = 500000.0
    
    if state["overall_risk_score"] > risk_threshold or state["amount_usd"] > high_value_limit:
        return "human_review"
    return "execution"


# ---------------------------------------------------------------------------
# 4. Graph Construction
# ---------------------------------------------------------------------------
workflow = StateGraph(TransactionState)

# Add Nodes
workflow.add_node("triage", triage_node)
workflow.add_node("compliance_agent", compliance_agent_node)
workflow.add_node("fx_agent", fx_routing_agent_node)
workflow.add_node("doc_agent", document_verification_agent_node)
workflow.add_node("risk_evaluator", risk_evaluation_node)
workflow.add_node("human_review", human_review_node)
workflow.add_node("execution", execution_node)

# Build Edges
workflow.add_edge(START, "triage")

# Fan-out parallel processing from triage to specialized agents
workflow.add_edge("triage", "compliance_agent")
workflow.add_edge("triage", "fx_agent")
workflow.add_edge("triage", "doc_agent")

# Fan-in convergence to risk evaluator
workflow.add_edge("compliance_agent", "risk_evaluator")
workflow.add_edge("fx_agent", "risk_evaluator")
workflow.add_edge("doc_agent", "risk_evaluator")

# Conditional edge based on risk score
workflow.add_conditional_edges(
    "risk_evaluator",
    route_after_evaluation,
    {
        "human_review": "human_review",
        "execution": "execution"
    }
)

workflow.add_edge("human_review", END)
workflow.add_edge("execution", END)

# Compile graph with memory checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)


# ---------------------------------------------------------------------------
# 5. Simulation / Test Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test Scenario 1: Low Risk, Automated Approval
    sample_transaction_low_risk: TransactionState = {
        "transaction_id": "TXN-9021-SAFE",
        "amount_usd": 45000.0,
        "sender_name": "Global Tech Logistics Ltd",
        "receiver_name": "Acme Corp Europe",
        "destination_country": "DE",
        "trade_document_summary": "Bill of Lading #4021 matches purchase order quantity of 500 units.",
        "sanction_flag": False,
        "sanction_confidence": 1.0,
        "optimal_rail": None,
        "fx_fee_usd": None,
        "doc_discrepancy_found": False,
        "overall_risk_score": 0.0,
        "status": "INITIATED",
        "human_approval": None,
        "remediation_notes": []
    }

    config = {"configurable": {"thread_id": "thread-1"}}
    
    print("\n--- RUNNING SCENARIO 1: Low-Risk Transaction ---")
    final_state = app.invoke(sample_transaction_low_risk, config=config)
    print(f"Final Status: {final_state['status']}")
    print("Audit Log:")
    for note in final_state["remediation_notes"]:
        print(f" - {note}")

    # Test Scenario 2: High Risk / Document Discrepancy (Triggers Human-In-The-Loop)
    sample_transaction_high_risk: TransactionState = {
        "transaction_id": "TXN-8833-RISK",
        "amount_usd": 750000.0,
        "sender_name": "Apex Holdings",
        "receiver_name": "Unknown Entity Trading",
        "destination_country": "SG",
        "trade_document_summary": "Warning: Discrepancy detected between invoice value ($500k) and payload ($750k).",
        "sanction_flag": False,
        "sanction_confidence": 1.0,
        "optimal_rail": None,
        "fx_fee_usd": None,
        "doc_discrepancy_found": False,
        "overall_risk_score": 0.0,
        "status": "INITIATED",
        "human_approval": None,
        "remediation_notes": []
    }

    config2 = {"configurable": {"thread_id": "thread-2"}}
    
    print("\n--- RUNNING SCENARIO 2: High-Value / Discrepancy Transaction ---")
    final_state_2 = app.invoke(sample_transaction_high_risk, config=config2)
    print(f"Final Status: {final_state_2['status']}")
    print("Audit Log:")
    for note in final_state_2["remediation_notes"]:
        print(f" - {note}")