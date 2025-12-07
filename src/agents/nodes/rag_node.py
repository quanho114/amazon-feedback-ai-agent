"""
RAG Node - The Knowledge Brain
Wraps the AdvancedRAG pipeline to answer user questions
"""
from langchain_core.messages import AIMessage

# Import Singleton instance from optimized module
try:
    from src.rag.advanced_rag import get_advanced_rag
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


def rag_node(state):
    """
    Main RAG Logic:
    1. Check if RAG system is available
    2. Detect Sentiment Filter (user wants negative or positive reviews?)
    3. Call AdvancedRAG Pipeline
    4. Format output
    
    Args:
        state: Current agent state with messages
        
    Returns:
        Updated state with RAG search results
    """
    messages = state["messages"]
    last_user_message = next(
        (msg.content for msg in reversed(messages) if hasattr(msg, 'content')),
        ""
    )
    
    # STEP 1: Check Availability
    if not RAG_AVAILABLE:
        return {
            "messages": [AIMessage(content="**RAG System Not Initialized**\n\nPlease check backend configuration.")],
            "loop_step": 1,
            "current_node": "rag"
        }
    
    # STEP 2: Detect Sentiment Filter (Simple keyword-based logic)
    query_lower = last_user_message.lower()
    sentiment_filter = None
    
    if any(w in query_lower for w in [
        'negative', 'bad', 'complaint', 'problem', 'issue', 
        'angry', 'terrible', 'worst', 'hate', 'disappointed'
    ]):
        sentiment_filter = 'negative'
    elif any(w in query_lower for w in [
        'positive', 'good', 'great', 'love', 'excellent',
        'best', 'amazing', 'wonderful', 'happy', 'satisfied'
    ]):
        sentiment_filter = 'positive'
    
    # STEP 3: Call RAG Pipeline
    try:
        rag_engine = get_advanced_rag()
        
        # Call query() method from AdvancedRAG class
        result = rag_engine.query(
            question=last_user_message,
            top_k=5,
            sentiment_filter=sentiment_filter,
            use_reranking=True,         # Enable reranking for accuracy
            use_query_expansion=False,  # Disable expansion for speed
            synthesize=True             # Enable answer synthesis
        )
        
        # STEP 4: Format Output
        response_text = _format_rag_result(result)
        
        return {
            "messages": [AIMessage(content=response_text)],
            "loop_step": 1,
            "current_node": "rag"
        }
        
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"**RAG Error**\n\n{str(e)}\n\nPlease try again or check if data has been uploaded.")],
            "loop_step": 1,
            "current_node": "rag"
        }


def _format_rag_result(result) -> str:
    """
    Helper to format RAGResult dataclass object into beautiful Markdown
    
    Args:
        result: RAGResult dataclass with answer, sources, confidence
        
    Returns:
        Formatted markdown string
    """
    # Note: result is a dataclass, access with dot notation
    answer = result.answer
    confidence = result.confidence
    sources = result.sources
    
    # Build Markdown
    parts = [
        f"{answer}",
        f"\n_(Confidence: {confidence:.0%})_",
        "\n---",
        "\n**Sources:**"
    ]
    
    if not sources:
        parts.append("- No relevant sources found.")
    else:
        # Show top 3 sources
        for i, src in enumerate(sources[:3], 1):
            # Metadata and content are in dict
            meta = src.get("metadata", {})
            content = src.get("content", "")[:150].replace("\n", " ")
            sentiment = meta.get("sentiment", "N/A")
            rating = meta.get("rating", "N/A")
            rerank_score = src.get("rerank_score", 0)
            
            parts.append(f"\n{i}. **[{sentiment.upper()} | Rating: {rating}]** (relevance: {rerank_score:.2f})")
            parts.append(f"   {content}...")
    
    return "\n".join(parts)
