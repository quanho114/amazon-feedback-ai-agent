"""
Vector Search Module - RAG Pipeline
Handles data ingestion and retrieval from ChromaDB
"""
import os
import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Global variables
VECTOR_DB = None
EMBEDDING_MODEL = None

# Constants
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
PERSIST_DIRECTORY = "data/vector_store"


def get_embedding_model():
    """
    Get or create embedding model (cached)
    
    Returns:
        HuggingFaceEmbeddings: Embedding model instance
    """
    global EMBEDDING_MODEL
    
    if EMBEDDING_MODEL is None:
        print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL_NAME}...")
        EMBEDDING_MODEL = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("[OK] Embedding model loaded successfully!")
    
    return EMBEDDING_MODEL


def ingest_data(df: pd.DataFrame, text_column: str = None, session_id: str = 'default'):
    """
    Ingest DataFrame into vector database
    
    Args:
        df: DataFrame containing review data
        text_column: Name of column containing text (auto-detect if None)
        session_id: Session identifier for vector store
        
    Returns:
        Chroma: Vector database instance
    """
    global VECTOR_DB
    
    print("[INFO] Starting RAG ingestion pipeline...")
    
    # Auto-detect text column
    if text_column is None:
        text_column = next(
            (col for col in df.columns if 'review' in col.lower() or 'text' in col.lower() or 'content' in col.lower()),
            None
        )
    
    if text_column is None:
        raise ValueError("Cannot find text column. Please specify text_column parameter.")
    
    print(f"[INFO] Using text column: {text_column}")
    
    # Get embedding model
    embedding_model = get_embedding_model()
    
    # Create documents with metadata
    print("[INFO] Creating documents with chunking...")
    documents = []
    
    for idx, row in df.iterrows():
        text = str(row[text_column])
        
        # Chunking strategy: split long texts
        if len(text) > CHUNK_SIZE:
            # Simple chunking by sentences
            chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        else:
            chunks = [text]
        
        for chunk_idx, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": f"row_{idx}_chunk_{chunk_idx}",
                    "row_index": idx,
                    "sentiment": row.get('ai_sentiment', 'unknown'),
                    "rating": str(row.get('rating', row.get('star', row.get('score', 'N/A')))),
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks)
                }
            )
            documents.append(doc)
    
    print(f"[OK] Created {len(documents)} document chunks from {len(df)} rows")
    
    # Clear old vector store if exists
    if os.path.exists(PERSIST_DIRECTORY):
        print("[INFO] Clearing old vector store...")
        import shutil
        shutil.rmtree(PERSIST_DIRECTORY)
    
    # Create vector database
    print("[INFO] Building vector index with ChromaDB...")
    VECTOR_DB = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        collection_name=f"reviews_{session_id}",
        persist_directory=PERSIST_DIRECTORY
    )
    
    print("[OK] RAG ingestion completed successfully!")
    
    return VECTOR_DB


def search_vector_db(query: str, top_k: int = 5, filter_metadata: dict = None):
    """
    Search vector database for relevant documents
    
    Args:
        query: Search query
        top_k: Number of results to return
        filter_metadata: Optional metadata filters (e.g., {"sentiment": "negative"})
        
    Returns:
        list: List of dictionaries with 'content' and 'metadata' keys
    """
    global VECTOR_DB
    
    if VECTOR_DB is None:
        return [{
            "content": "Vector database not initialized. Please upload data first.",
            "metadata": {}
        }]
    
    try:
        # Perform similarity search
        if filter_metadata:
            results = VECTOR_DB.similarity_search(
                query=query,
                k=top_k,
                filter=filter_metadata
            )
        else:
            results = VECTOR_DB.similarity_search(
                query=query,
                k=top_k
            )
        
        # Format results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        
        return formatted_results
        
    except Exception as e:
        print(f"[ERROR] Error during vector search: {str(e)}")
        return [{
            "content": f"Search error: {str(e)}",
            "metadata": {}
        }]


def hybrid_search(query: str, top_k: int = 5, sentiment_filter: str = None):
    """
    Hybrid search combining vector search with metadata filtering
    
    Args:
        query: Search query
        top_k: Number of results
        sentiment_filter: Filter by sentiment (positive/negative/neutral)
        
    Returns:
        list: Search results
    """
    filter_dict = None
    
    if sentiment_filter:
        filter_dict = {"sentiment": sentiment_filter}
    
    return search_vector_db(query, top_k, filter_dict)


def clear_vector_store():
    """
    Clear the vector store and reset global variables
    Useful when user wants to upload a new dataset
    """
    global VECTOR_DB
    
    try:
        # Delete the vector store
        if VECTOR_DB is not None:
            try:
                VECTOR_DB.delete_collection()
                print("[INFO] Vector store collection deleted")
            except Exception as e:
                print(f"[WARNING] Could not delete collection: {e}")
            
            VECTOR_DB = None
        
        # Clear persisted data if exists
        import shutil
        if os.path.exists(PERSIST_DIRECTORY):
            shutil.rmtree(PERSIST_DIRECTORY)
            print(f"[INFO] Cleared vector store directory: {PERSIST_DIRECTORY}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to clear vector store: {e}")
        return False
