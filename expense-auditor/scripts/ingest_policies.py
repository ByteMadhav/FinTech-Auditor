
import os
import logging
from pathlib import Path


from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


PDF_FILE_PATH = "data/Allowance_Reimburesement.pdf"
CHROMA_DB_DIR = "./chroma_db"

def ingest_pdf(file_path: str, policy_section_name: str = "General"):
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}. Please make sure it is in the data/ folder.")
        return

    logger.info(f"Loading PDF: {file_path}")
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    
    logger.info("Splitting document into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_documents(pages)
    
    for chunk in chunks:
        
        chunk.metadata["section"] = policy_section_name
        chunk.metadata["source_file"] = Path(file_path).name

    logger.info("Downloading local model and generating embeddings... (This may take a minute)")
    
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    logger.info(f"✅ Successfully ingested {len(chunks)} chunks from {file_path} into {CHROMA_DB_DIR}")

if __name__ == "__main__":
    
    ingest_pdf(PDF_FILE_PATH, policy_section_name="Kerala Service Rules - Travelling Allowances")