"""
RAG module initialization
"""
from .vector_search import ingest_data, search_vector_db

__all__ = ['ingest_data', 'search_vector_db']
