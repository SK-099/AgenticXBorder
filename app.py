import os
import gradio as gr

from core.database import init_qdrant_db
from graph.workflow import build_workflow
from ui.dashboard import build_dashboard

# Ensure API Key is loaded
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

if __name__ == "__main__":
    # 1. Initialize In-Memory Qdrant Vector Watchlist
    qdrant_db = init_qdrant_db()

    # 2. Compile LangGraph Engine with Interruption Support
    agent_app = build_workflow(qdrant_db)

    # 3. Launch UI Dashboard
    demo = build_dashboard(agent_app)
    demo.launch(theme=gr.themes.Soft())