"""
LangGraph Supervisor - Multi-Agent Orchestrator
Routes user queries to appropriate worker nodes
"""
import operator
import logging
import os
from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

# Import state and nodes
from src.agents.state import AgentState
from src.agents.nodes import (
    sentiment_node,
    rag_node,
    summarize_node,
    insight_node,
    analyst_node,
    chat_node
)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SUPERVISOR")

# --- SUPERVISOR LLM ---
supervisor_llm = ChatOpenAI(
    api_key=os.getenv("MEGALLM_API_KEY"),
    base_url=os.getenv("MEGALLM_BASE_URL"),
    model=os.getenv("MEGALLM_MODEL"),
    temperature=0,  # Deterministic routing
    streaming=False,  # No streaming for supervisor
    max_tokens=20  # Only need worker name
)

# --- SUPERVISOR PROMPT ---
SUPERVISOR_PROMPT = """
You are the Supervisor - AI Worker Coordinator.

MISSION: Analyze user question and select the most appropriate worker.

AVAILABLE WORKERS:
1. SENTIMENT - Sentiment analysis expert
   When: "analyze sentiment", "pain points", "customer complaints", "customer psychology"
   
2. RAG - Information retrieval expert
   When: "find reviews about...", "what customers say about...", "any reviews mentioning..."
   
3. SUMMARIZE - Summarization expert
   When: "summarize", "summary", "overview", "general view"
   
4. INSIGHT - Strategic analysis expert
   When: "insight", "recommendation", "strategy", "SWOT"
   
5. ANALYST - Data calculation AND CHART DRAWING expert
   When: "how many", "calculate average", "percentage", "statistics", "count", "mean", "draw chart", "graph", "plot"
   
6. CHAT - General assistant (fallback)
   When: General questions, greetings, unclear requests

RULES:
- Only return worker NAME (SENTIMENT, RAG, SUMMARIZE, INSIGHT, ANALYST, CHAT)
- NO explanation, NO extra words
- Prioritize ANALYST for numerical questions
- Prioritize RAG for specific search queries

EXAMPLES:
User: "How many positive reviews?"
Output: ANALYST

User: "Find reviews about battery"
Output: RAG

User: "Analyze customer sentiment"
Output: SENTIMENT

User: "Recommend product improvements"
Output: INSIGHT
"""


def supervisor_node(state):
    """
    Supervisor node - Routes to appropriate worker
    Fast pattern matching first, then LLM if needed
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with routing decision
    """
    messages = state["messages"]
    
    # Get last user message
    last_user_message = next(
        (msg.content for msg in reversed(messages) if isinstance(msg, HumanMessage)),
        ""
    ).lower()
    
    # FAST PATTERN MATCHING (no LLM call)
    selected_worker = None
    
    # Simple greetings & self-intro -> CHAT (fast path)
    if any(word in last_user_message for word in [
        'hello', 'hi', 'hey', 'thanks', 'thank you',
        'who are you', 'what are you', 'introduce yourself',
        'what can you do', 'help me', 'help',
        'guide', 'how to use', 'tutorial'
    ]):
        selected_worker = "CHAT"
    
    # Charts/Visualization -> ANALYST (HIGHEST PRIORITY!)
    elif any(word in last_user_message for word in [
        'treemap', 'pie chart', 'bar chart', 'line chart', 'scatter', 'area chart', 'radar',
        'draw', 'create', 'make', 'generate', 'build',
        'chart', 'graph', 'plot', 'visualize', 'visualization'
    ]):
        logger.info(f"[PATTERN] Detected chart request → ANALYST")
        selected_worker = "ANALYST"
    
    # Numbers/Stats/Calculations -> ANALYST
    elif any(word in last_user_message for word in [
        'how many', 'count', 'calculate', 'compute',
        'average', 'mean', 'median', 'percent', 'percentage', 'statistics', 'stats'
    ]):
        selected_worker = "ANALYST"
    
    # Search queries -> RAG
    elif any(word in last_user_message for word in [
        'search', 'find', 'look for', 'show reviews',
        'reviews about', 'mention', 'talk about', 'say about'
    ]):
        selected_worker = "RAG"
    
    # Sentiment analysis (but NOT if asking for chart) -> SENTIMENT
    elif any(word in last_user_message for word in [
        'analyze sentiment', 'sentiment distribution', 'sentiment breakdown',
        'emotion', 'feeling', 'mood'
    ]) and not any(chart_word in last_user_message for chart_word in ['chart', 'graph', 'plot', 'draw', 'treemap', 'pie', 'bar']):
        selected_worker = "SENTIMENT"
    
    # Summary -> SUMMARIZE
    elif any(word in last_user_message for word in [
        'summary', 'summarize', 'overview', 'brief',
        'key points', 'main points', 'highlights'
    ]):
        selected_worker = "SUMMARIZE"
    
    # Insights -> INSIGHT
    elif any(word in last_user_message for word in [
        'insight', 'insights', 'recommend', 'recommendation', 'suggest',
        'strategy', 'strategic', 'swot', 'improve', 'improvement', 'action'
    ]):
        selected_worker = "INSIGHT"
    
    # If no pattern match, use LLM (slower but accurate)
    if selected_worker is None:
        routing_messages = [
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=f"User question: {last_user_message}")
        ]
        response = supervisor_llm.invoke(routing_messages)
        selected_worker = response.content.strip().upper()
    
    logger.info(f"[SUPERVISOR] Routes to: {selected_worker}")
    
    return {
        "messages": [],
        "loop_step": 0,
        "current_node": selected_worker
    }


def route_to_worker(state):
    """
    Routing function - Determines next node based on supervisor decision
    
    Args:
        state: Current agent state
        
    Returns:
        str: Next node name
    """
    current_node = state.get("current_node", "CHAT")
    
    # Map to node names
    node_mapping = {
        "SENTIMENT": "sentiment",
        "RAG": "rag",
        "SUMMARIZE": "summarize",
        "INSIGHT": "insight",
        "ANALYST": "analyst",
        "CHAT": "chat"
    }
    
    return node_mapping.get(current_node, "chat")


# --- BUILD GRAPH ---
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("sentiment", sentiment_node)
workflow.add_node("rag", rag_node)
workflow.add_node("summarize", summarize_node)
workflow.add_node("insight", insight_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("chat", chat_node)

# Set entry point
workflow.set_entry_point("supervisor")

# Add routing from supervisor to workers
workflow.add_conditional_edges(
    "supervisor",
    route_to_worker,
    {
        "sentiment": "sentiment",
        "rag": "rag",
        "summarize": "summarize",
        "insight": "insight",
        "analyst": "analyst",
        "chat": "chat"
    }
)

# All workers end after execution
workflow.add_edge("sentiment", END)
workflow.add_edge("rag", END)
workflow.add_edge("summarize", END)
workflow.add_edge("insight", END)
workflow.add_edge("analyst", END)
workflow.add_edge("chat", END)

# Compile graph
app = workflow.compile()

logger.info("[SUCCESS] LangGraph Supervisor compiled successfully!")