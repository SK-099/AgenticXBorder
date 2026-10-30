import operator
from typing import List, Optional, TypedDict, Annotated


class TransactionState(TypedDict):
    transaction_id: str
    amount_usd: float
    sender_name: str
    receiver_name: str
    destination_country: str
    trade_document_summary: str
    
    # Agent Analysis Results
    sanction_flag: bool
    sanction_confidence: float
    optimal_rail: Optional[str]
    fx_fee_usd: Optional[float]
    doc_discrepancy_found: bool
    
    # Combined Policy & Risk Evaluation
    overall_risk_score: float
    status: str
    human_decision: Optional[str]  # "APPROVED" or "REJECTED" via Human-in-the-Loop
    
    # Operator reducer allows concurrent parallel nodes to append notes
    remediation_notes: Annotated[List[str], operator.add]