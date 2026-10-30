import os

# Model & Tracing Configurations
OPENAI_MODEL_NAME = "gpt-4o"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Enable LangSmith Tracing if API Key is available
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "Agentic-X-Border-JPMC-Demo"

# Enterprise Policy Thresholds
RISK_THRESHOLD = 0.35
HIGH_VALUE_THRESHOLD_USD = 500000.0