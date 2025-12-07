"""
State definition for LangGraph multi-agent system
"""
import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Shared state across all agent nodes
    """
    # Chat history (accumulated)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Loop counter to prevent infinite loops
    loop_step: Annotated[int, operator.add]
    
    # Current DataFrame info (optional metadata)
    data_info: dict
    
    # Last selected node (for debugging)
    current_node: str
    
    # Analysis data context (shared between nodes)
    analysis_data: dict
