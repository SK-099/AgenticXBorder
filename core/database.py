from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config.settings import EMBEDDING_MODEL_NAME


def init_qdrant_db():
    print("[DATABASE] Initializing In-Memory Qdrant Vector Engine...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    # Sanctions / Watchlist Records
    sanction_records = [
        Document(page_content="Apex Holdings International - Sanctioned entity under OFAC & EU illicit trade watchlists.", metadata={"entity": "Apex Holdings"}),
        Document(page_content="Unknown Entity Trading LLC - Flagged for money laundering and shell company operations.", metadata={"entity": "Unknown Entity Trading"}),
        Document(page_content="Global Logistics Corp - Whitelisted commercial trade logistics partner.", metadata={"entity": "Global Logistics Corp"})
    ]

    client = QdrantClient(location=":memory:")

    if not client.collection_exists("ofac_sanctions"):
        client.create_collection(
            collection_name="ofac_sanctions",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

    qdrant_db = QdrantVectorStore(
        client=client,
        collection_name="ofac_sanctions",
        embedding=embeddings
    )
    qdrant_db.add_documents(sanction_records)
    return qdrant_db