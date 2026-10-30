import gradio as gr
import easyocr
import numpy as np
from langgraph.types import Command
from core.state import TransactionState


def build_dashboard(app):
    print("[INITIALIZATION] Loading EasyOCR Vision Engine...")
    reader = easyocr.Reader(['en'], gpu=False)

    def run_pipeline(tx_id, amount, sender, receiver, destination, invoice_img, manual_doc_text):
        ocr_text = ""
        if invoice_img is not None:
            img_np = np.array(invoice_img)
            ocr_results = reader.readtext(img_np, detail=0)
            ocr_text = " ".join(ocr_results)
        
        combined_doc_summary = f"{manual_doc_text} | OCR Text Extracted: {ocr_text}" if ocr_text else manual_doc_text
        
        initial_state: TransactionState = {
            "transaction_id": tx_id,
            "amount_usd": float(amount),
            "sender_name": sender,
            "receiver_name": receiver,
            "destination_country": destination,
            "trade_document_summary": combined_doc_summary,
            "sanction_flag": False,
            "sanction_confidence": 1.0,
            "optimal_rail": None,
            "fx_fee_usd": None,
            "doc_discrepancy_found": False,
            "overall_risk_score": 0.0,
            "status": "INITIATED",
            "human_decision": None,
            "remediation_notes": []
        }

        config = {"configurable": {"thread_id": tx_id}}
        final_state = app.invoke(initial_state, config=config)
        
        # Handle native LangGraph interrupt state
        if "__interrupt__" in final_state:
            status = "PENDING_HUMAN_REVIEW"
            risk_score = f"{final_state.get('overall_risk_score', 1.0):.2f}"
            notes = final_state.get("remediation_notes", [])
            notes.append("⚠️ Execution interrupted: High-risk parameters require manual approval.")
            audit_trail = "\n".join([f"• {note}" for note in notes])
            return status, risk_score, audit_trail, ocr_text, gr.update(interactive=True), gr.update(interactive=True)

        audit_trail = "\n".join([f"• {note}" for note in final_state.get("remediation_notes", [])])
        return final_state.get("status", "COMPLETED"), f"{final_state.get('overall_risk_score', 0.0):.2f}", audit_trail, ocr_text, gr.update(interactive=False), gr.update(interactive=False)

    def resume_pipeline(tx_id, decision):
        config = {"configurable": {"thread_id": tx_id}}
        final_state = app.invoke(Command(resume={"decision": decision}), config=config)
        
        audit_trail = "\n".join([f"• {note}" for note in final_state.get("remediation_notes", [])])
        return final_state.get("status", "RESOLVED"), f"{final_state.get('overall_risk_score', 0.0):.2f}", audit_trail, gr.update(interactive=False), gr.update(interactive=False)

    with gr.Blocks(title="Agentic-X-Border Settlement Platform") as demo:
        gr.Markdown("# 🏦 Agentic-X-Border Settlement & Compliance Platform")
        gr.Markdown("Enterprise Multi-Agent Cross-Border Settlement Engine with Qdrant Vector Watchlists, EasyOCR, and Native LangGraph Human-in-the-Loop Interruption.")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 1. Transaction Details")
                tx_id = gr.Textbox(value="TXN-9941-DEMO", label="Transaction ID")
                amount = gr.Number(value=450000.0, label="Amount (USD)")
                sender = gr.Textbox(value="Global Tech Logistics", label="Sender Name")
                receiver = gr.Textbox(value="Apex Holdings International", label="Receiver Name")
                destination = gr.Textbox(value="SG", label="Destination Country Code")
                
                gr.Markdown("### 2. Trade Document & OCR Scan")
                invoice_img = gr.Image(type="pil", label="Upload Invoice Image (EasyOCR Scan)")
                manual_doc_text = gr.Textbox(value="Bill of lading attached. Document discrepancy warning: amounts mismatch.", label="Trade Document Notes")
                
                submit_btn = gr.Button("🚀 Run Multi-Agent Analysis", variant="primary")

            with gr.Column(scale=1):
                gr.Markdown("### 3. Execution Status & Risk Analysis")
                status_output = gr.Textbox(label="Final Transaction Status")
                risk_output = gr.Textbox(label="Holistic Risk Score (0.00 to 1.00)")
                ocr_output = gr.Textbox(label="Extracted EasyOCR Text")
                audit_output = gr.TextArea(label="Multi-Agent Audit Trail Logs", lines=10)
                
                gr.Markdown("### 4. Human-in-the-Loop Override Gate")
                with gr.Row():
                    approve_btn = gr.Button("✅ Approve Override", variant="success", interactive=False)
                    reject_btn = gr.Button("❌ Reject Transaction", variant="stop", interactive=False)

        submit_btn.click(
            fn=run_pipeline,
            inputs=[tx_id, amount, sender, receiver, destination, invoice_img, manual_doc_text],
            outputs=[status_output, risk_output, audit_output, ocr_output, approve_btn, reject_btn]
        )

        approve_btn.click(
            fn=lambda tid: resume_pipeline(tid, "APPROVED"),
            inputs=[tx_id],
            outputs=[status_output, risk_output, audit_output, approve_btn, reject_btn]
        )

        reject_btn.click(
            fn=lambda tid: resume_pipeline(tid, "REJECTED"),
            inputs=[tx_id],
            outputs=[status_output, risk_output, audit_output, approve_btn, reject_btn]
        )

    return demo