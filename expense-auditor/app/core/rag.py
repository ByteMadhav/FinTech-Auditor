import logging
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2") 
        self.vector_store = Chroma(
            persist_directory="./chroma_db", 
            embedding_function=embeddings
        )

    def find_similar_transactions(self, query: str, user_id: str = None) -> List[Dict[str, Any]]:
        try:
            docs = self.vector_store.similarity_search_with_score(query, k=5)
            return [
                {
                    "score": 1.0 / (1.0 + score), 
                    "metadata": {
                        "policy_section": doc.metadata.get("section", "General"),
                        "rule_text": doc.page_content
                    }
                } for doc, score in docs
            ]
        except Exception:
            return []

rag_service = RAGService()