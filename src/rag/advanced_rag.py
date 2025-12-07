"""
Advanced RAG Pipeline - Production Optimized
Optimizations:
1. Confidence Score: Uses Sigmoid function on Top-1 Logit
2. Deduplication: Hashes full normalized content
3. Latency: Query Expansion is optional (default off)
4. Retry Logic: Handle model overload (Error 500)
"""
import os
import math
import time
import hashlib
from typing import List, Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# Import base vector search
from src.rag.vector_search import search_vector_db, hybrid_search

# LLM for synthesis
try:
    from langchain_openai import ChatOpenAI
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Cross-encoder for reranking
try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("[WARNING] CrossEncoder not available. Install: pip install sentence-transformers")


@dataclass
class RAGResult:
    """Structured RAG result"""
    answer: str
    sources: List[Dict]
    query_variants: List[str]
    confidence: float


class AdvancedRAG:
    """Production-Ready RAG Pipeline"""
    
    def __init__(self):
        # Setup LLM
        if LLM_AVAILABLE:
            self.llm = ChatOpenAI(
                api_key=os.getenv("MEGALLM_API_KEY"),
                base_url=os.getenv("MEGALLM_BASE_URL"),
                model=os.getenv("MEGALLM_MODEL"),
                temperature=0,
                max_tokens=500
            )
        else:
            self.llm = None
        
        # Setup Reranker
        if RERANKER_AVAILABLE:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        else:
            self.reranker = None
        
        print("[INFO] Advanced RAG initialized (Optimized Mode)")
        print(f"  - LLM: {'OK' if self.llm else 'Not available'}")
        print(f"  - Reranker: {'OK' if self.reranker else 'Not available'}")
    
    def _sigmoid(self, x: float) -> float:
        """
        FIX 1: Scientific Confidence Calculation
        Maps unbounded logits (-inf, +inf) to probability (0, 1)
        """
        try:
            return 1 / (1 + math.exp(-x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0
    
    def expand_query(self, query: str, num_variants: int = 2) -> List[str]:
        """Query Expansion logic"""
        if not self.llm:
            return [query]
        
        prompt = f"""Generate {num_variants} alternative search queries for: "{query}".
Focus on synonyms related to Amazon e-commerce context (delivery, service, refund, Prime).
Return ONLY the queries, one per line, no numbering."""
        
        try:
            response = self.llm.invoke(prompt)
            variants = [q.strip() for q in response.content.strip().split('\n') if q.strip()]
            return [query] + variants[:num_variants]
        except Exception as e:
            print(f"[WARNING] Query expansion failed: {e}")
            return [query]
    
    def multi_query_search(
        self, 
        query: str, 
        top_k: int = 5,
        sentiment_filter: str = None,
        expand_query: bool = False
    ) -> List[Dict]:
        """
        Multi-Query Search with Robust Deduplication
        FIX 3: Hash full normalized content to avoid duplicates
        """
        # Step 1: Get Queries
        if expand_query:
            queries = self.expand_query(query)
        else:
            queries = [query]
        
        # Step 2: Search & Deduplicate
        all_results = []
        seen_hashes = set()
        
        for q in queries:
            # Search
            if sentiment_filter:
                results = hybrid_search(q, top_k=top_k, sentiment_filter=sentiment_filter)
            else:
                results = search_vector_db(q, top_k=top_k)
            
            for doc in results:
                content = doc.get("content", "")
                
                # Robust Deduplication: Hash normalized content
                norm_content = content.strip().lower().encode('utf-8')
                content_hash = hashlib.md5(norm_content).hexdigest()
                
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    doc["matched_query"] = q
                    all_results.append(doc)
        
        return all_results
    
    def rerank_results(
        self, 
        query: str, 
        results: List[Dict], 
        top_k: int = 5
    ) -> List[Dict]:
        """Reranking using Cross-Encoder"""
        if not self.reranker or not results:
            return results[:top_k]
        
        pairs = [(query, doc.get("content", "")) for doc in results]
        scores = self.reranker.predict(pairs)
        
        for i, doc in enumerate(results):
            doc["rerank_score"] = float(scores[i])
        
        # Sort by score descending
        sorted_results = sorted(
            results, 
            key=lambda x: x.get("rerank_score", -999), 
            reverse=True
        )
        
        return sorted_results[:top_k]
    
    def synthesize_answer(self, query: str, results: List[Dict]) -> str:
        """
        Generate answer using LLM with Retry Logic
        Handles model overload (Error 500) by retrying with exponential backoff
        """
        if not self.llm or not results:
            return "No relevant information found."
        
        # Build context
        context_parts = []
        for i, doc in enumerate(results):
            meta = doc.get("metadata", {})
            sentiment = meta.get("sentiment", "N/A")
            rating = meta.get("rating", "N/A")
            content = doc.get("content", "")
            
            part = f"[Review {i+1}] (Sentiment: {sentiment}, Rating: {rating})\n{content}"
            context_parts.append(part)
        
        context = "\n\n".join(context_parts)[:3000]  # Limit context size
        
        prompt = f"""Answer the question based strictly on the reviews below.

QUESTION: {query}

REVIEWS:
{context}

ANSWER (Concise, cite examples):"""
        
        # Retry logic for model overload
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(prompt)
                return response.content
            except Exception as e:
                error_msg = str(e)
                print(f"[WARNING] LLM Error (Attempt {attempt+1}/{max_retries}): {error_msg}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    wait_time = 2 ** (attempt + 1)
                    print(f"[INFO] Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Final fallback: return raw context
                    print("[ERROR] Model overloaded after 3 attempts. Returning raw context.")
                    return f"Model is currently overloaded. Here's the raw information found:\n\n{context}"
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        sentiment_filter: str = None,
        use_reranking: bool = True,
        use_query_expansion: bool = False,  # FIX 2: Default False for Low Latency
        synthesize: bool = True
    ) -> RAGResult:
        """
        Main Pipeline Entry Point
        
        Args:
            question: User's question
            top_k: Number of final results
            sentiment_filter: Filter by sentiment
            use_reranking: Whether to use cross-encoder reranking
            use_query_expansion: Whether to expand query (default False for speed)
            synthesize: Whether to synthesize answer with LLM
            
        Returns:
            RAGResult with answer, sources, and confidence
        """
        # 1. Search
        results = self.multi_query_search(
            question, 
            top_k=top_k * 2,  # Fetch more for reranker
            sentiment_filter=sentiment_filter,
            expand_query=use_query_expansion
        )
        
        if not results:
            return RAGResult(
                answer="No data found.",
                sources=[],
                query_variants=[question],
                confidence=0.0
            )
        
        # 2. Rerank
        if use_reranking:
            results = self.rerank_results(question, results, top_k=top_k)
        else:
            results = results[:top_k]
        
        # 3. Calculate Confidence (The Correct Way)
        if results and "rerank_score" in results[0]:
            top_score = results[0]["rerank_score"]
            confidence = self._sigmoid(top_score)
            
            # Penalize if score too low (Logit < 0 means < 50% match)
            if top_score < 0:
                confidence = confidence * 0.5
        else:
            confidence = 0.5  # Default if no reranker
        
        # 4. Synthesize
        answer = ""
        if synthesize:
            # Only answer if confidence is high enough
            if confidence > 0.4:
                answer = self.synthesize_answer(question, results)
            else:
                answer = "I found some information but it may not be directly relevant to your question."
        else:
            answer = "Returned raw context."
        
        return RAGResult(
            answer=answer,
            sources=results,
            query_variants=[question],
            confidence=round(confidence, 4)
        )


# Singleton pattern
_rag_instance = None

def get_advanced_rag() -> AdvancedRAG:
    """Get singleton Advanced RAG instance"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = AdvancedRAG()
    return _rag_instance


def advanced_search(
    question: str,
    top_k: int = 5,
    sentiment_filter: str = None,
    full_pipeline: bool = True
) -> Dict:
    """
    Convenience function for advanced RAG search
    
    Args:
        question: User's question
        top_k: Number of results
        sentiment_filter: Filter by sentiment
        full_pipeline: Use full pipeline (reranking + synthesis)
        
    Returns:
        Dict with answer, sources, confidence
    """
    rag = get_advanced_rag()
    result = rag.query(
        question,
        top_k=top_k,
        sentiment_filter=sentiment_filter,
        use_reranking=full_pipeline,
        use_query_expansion=False,  
        synthesize=full_pipeline
    )
    
    return {
        "answer": result.answer,
        "sources": result.sources,
        "query_variants": result.query_variants,
        "confidence": result.confidence
    }
