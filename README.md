# Agentic Cross-Border Payment Settlement & Compliance Platform

A multi-agent cross-border payment settlement and compliance engine built with **LangGraph**, **Qdrant**, **EasyOCR**, and **Gradio**. It uses LangGraph's native `interrupt()` to pause execution for Human-in-the-Loop (HITL) compliance review.

---

## Key Features & Architecture

- **Multi-Agent Orchestration:** LangGraph state machine with parallel fan-out and conditional branching between agents.
- **Vector Watchlist Screening:** Semantic entity matching in Qdrant against sanctions lists (e.g., OFAC SDN and the EU Consolidated Financial Sanctions List).
- **Document AI & OCR Ingestion:** Text extraction from scanned trade invoices, receipts, and forms using EasyOCR.
- **Human-in-the-Loop (HITL) Gate:** High-risk transactions interrupt the graph and wait for manual approval or rejection before the state checkpoint is finalized.

---

## Repository Structure

```text
AgenticXBorder/
├── agents/            # LangGraph node functions (OCR, Compliance, Risk, Gate)
├── config/            # System settings and environment constants
├── core/              # Database models, state definitions, and Qdrant client
├── graph/             # LangGraph workflow definition and state machine
├── ui/                # Gradio dashboard layout and event handlers
├── app.py             # Server entry point and dashboard launcher
├── download_docvqa.py # Downloads and flattens benchmark datasets
├── requirements.txt   # Pinned Python dependencies
└── README.md          # Project overview and documentation
```

---

## Running Locally

```bash
pip install -r requirements.txt
python app.py
```

Once the server is running, open the dashboard in your browser at either address:

- http://localhost:7860
- http://127.0.0.1:7860

---

## OCR Benchmark Results

The EasyOCR pipeline was run on 100 samples from each of four public document-AI datasets (400 documents in total), on CPU.

| Dataset | Samples | Non-Empty Extractions | Failed | Extraction Rate | Document Type |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **DocVQA** | 100 | 100 | 0 | 100.00% | Scanned industry documents |
| **SROIE** | 100 | 100 | 0 | 100.00% | Scanned receipts |
| **FUNSD** | 100 | 100 | 0 | 100.00% | Noisy scanned forms |
| **CORD** | 100 | 100 | 0 | 100.00% | Receipts (Consolidated Receipt Dataset) |

> **Note:** "Extraction rate" is the share of documents for which EasyOCR returned a non-empty text payload. It is **not** a measure of OCR accuracy: it does not compare the extracted text with ground-truth labels. Character/word error rate (CER/WER) or field-level F1 against each dataset's annotations would be needed to report accuracy.

**Benchmark script output:**

```text
==========================================
EVALUATION COMPLETE! Report saved to 'ocr_benchmark_report.json'
==========================================
Dataset 'docvqa': Total=100 | Success=100 | Failed=0 | Accuracy Rate=100.00%
Dataset 'sroie': Total=100 | Success=100 | Failed=0 | Accuracy Rate=100.00%
Dataset 'funsd': Total=100 | Success=100 | Failed=0 | Accuracy Rate=100.00%
Dataset 'cord': Total=100 | Success=100 | Failed=0 | Accuracy Rate=100.00%
```
