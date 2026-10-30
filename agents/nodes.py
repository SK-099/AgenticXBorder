from typing import Dict, Any
from langgraph.types import interrupt
from core.state import TransactionState


def triage_node(state: TransactionState) -> Dict[str, Any]:
    return {
        "status": "PROCESSING",
        "remediation_notes": [f"Transaction {state['transaction_id']} ingested for automated multi-agent analysis."]
    }


def create_compliance_agent_node(qdrant_db):
    def compliance_agent_node(state: TransactionState) -> Dict[str, Any]:
        receiver = state['receiver_name']
        results = qdrant_db.similarity_search_with_score(receiver, k=1)
        
        sanction_flag = False
        confidence_clean = 0.95
        reason = "No semantic watchlist matches found in Qdrant Vector DB."
        
        if results:
            doc, score = results[0]
            if score > 0.5 and ("Sanctioned" in doc.page_content or "Flagged" in doc.page_content):
                sanction_flag = True
                confidence_clean = 0.30
                reason = f"Qdrant Watchlist Match (Similarity Score: {score:.2f}): {doc.page_content}"

        return {
            "sanction_flag": sanction_flag,
            "sanction_confidence": confidence_clean,
            "remediation_notes": [f"Compliance Check (Qdrant): {reason}"]
        }
    return compliance_agent_node


def fx_routing_agent_node(state: TransactionState) -> Dict[str, Any]:
    amount = state["amount_usd"]
    destination = state["destination_country"]
    
    if amount >= 1000000.0:
        rail = "J.P. Morgan Onyx / JPM Coin DLT Network"
        fee = amount * 0.0002
    elif amount < 100000.0 and destination in ["GB", "EU", "US", "SG"]:
        rail = "Visa Direct / Mastercard Send Push Payments"
        fee = amount * 0.0012
    else:
        rail = "SWIFT ISO 20022 Cross-Border Rail"
        fee = amount * 0.0005
        
    return {
        "optimal_rail": rail,
        "fx_fee_usd": fee,
        "remediation_notes": [f"FX Routing Selected: {rail} (Est. Fee: ${fee:,.2f})"]
    }


def document_verification_agent_node(state: TransactionState) -> Dict[str, Any]:
    doc_text = state.get("trade_document_summary", "")
    has_discrepancy = False
    reason = "Trade document details match transaction metadata."
    
    if any(term in doc_text.lower() for term in ["mismatch", "discrepancy", "warning", "error"]):
        has_discrepancy = True
        reason = "Discrepancy detected between trade invoice text and payload parameters."

    return {
        "doc_discrepancy_found": has_discrepancy,
        "remediation_notes": [f"Document Verification: {reason}"]
    }


def risk_evaluation_node(state: TransactionState) -> Dict[str, Any]:
    risk_score = 0.0
    
    if state.get("sanction_flag"):
        risk_score += 0.50
    if state.get("sanction_confidence", 1.0) < 0.70:
        risk_score += 0.25
    if state.get("doc_discrepancy_found"):
        risk_score += 0.30
    if state.get("amount_usd", 0) > 500000:
        risk_score += 0.10

    risk_score = min(risk_score, 1.0)
    
    return {
        "overall_risk_score": risk_score,
        "remediation_notes": [f"Holistic Risk Score Computed: {risk_score:.2f}"]
    }


def human_review_node(state: TransactionState) -> Dict[str, Any]:
    human_response = interrupt({
        "message": "High Risk / High Value transaction flagged for compliance review.",
        "transaction_id": state["transaction_id"],
        "risk_score": state["overall_risk_score"]
    })
    
    decision = human_response.get("decision", "REJECTED")
    return {
        "status": "APPROVED" if decision == "APPROVED" else "REJECTED",
        "human_decision": decision,
        "remediation_notes": [f"Human Officer Gate Action: Transaction {decision}"]
    }


def execution_node(state: TransactionState) -> Dict[str, Any]:
    return {
        "status": "APPROVED",
        "remediation_notes": [f"Settlement finalized successfully via {state['optimal_rail']}."]
    }