"""
Chat Node - Fallback Conversational Worker
Handles general questions and clarifications when other nodes are not suitable
Uses faster LLM model for quick responses
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

# Import smart cache
try:
    from src.utils.cache import get_smart_response, RESPONSE_CACHE
except ImportError:
    # Fallback if import fails
    def get_smart_response(query):
        return None
    class DummyCache:
        def set(self, q, r): pass
    RESPONSE_CACHE = DummyCache()

# Import Session Data to check data status
from src.agents.tools import SESSION_DATA

# Import config
try:
    from src.config import CHAT_API_KEY, CHAT_BASE_URL, CHAT_MODEL
except ImportError:
    # Fallback to main config if chat config not available
    CHAT_API_KEY = os.getenv("MEGALLM_API_KEY")
    CHAT_BASE_URL = os.getenv("MEGALLM_BASE_URL")
    CHAT_MODEL = os.getenv("MEGALLM_MODEL")

load_dotenv()

# Initialize FAST LLM for chat
llm = ChatOpenAI(
    api_key=CHAT_API_KEY,
    base_url=CHAT_BASE_URL,
    model=CHAT_MODEL,
    temperature=0.3,  # Lower = faster + more deterministic
    streaming=True,
    max_tokens=150  # Short responses for chat
)

CHAT_PROMPT_TEMPLATE = """You are Amazon AI Assistant - a friendly and concise AI assistant.

DATA STATUS:
- Data Uploaded: {has_data}
- Dataset: {filename}
- Total Reviews: {total_reviews}

YOUR ROLE:
Answer general questions briefly and guide users on features.

SYSTEM FEATURES (6 AI Agents):
1. **Chat** - General conversation (you!)
2. **Sentiment** - Analyze review sentiment (SVM model, 90% accuracy)
3. **Analyst** - Create charts (pie, bar, line, scatter, etc.)
4. **RAG** - Search specific reviews using semantic search
5. **Insight** - Strategic business recommendations
6. **Summarize** - Summarize review themes

RESPONSE STYLE:
- **KEEP IT SHORT** - 2-4 sentences maximum
- **BE DIRECT** - No long explanations unless asked
- **USE BULLET POINTS** - For lists (max 5 items)
- **NO TECHNICAL JARGON** - Simple language
- **NO EMOJI ICONS** - Plain text only

EXAMPLES:

User: "How does this work?"
You: "I'm an AI with 6 specialized agents for analyzing Amazon reviews. You can ask me to analyze sentiment, search reviews, create charts, or get business insights. What would you like to do?"

User: "What can you do?"
You: "I can:
- Analyze sentiment distribution
- Search specific reviews
- Create charts and visualizations
- Provide strategic insights
- Summarize feedback

Try: 'Analyze sentiment' or 'Find reviews about delivery'"

IMPORTANT:
- If Data Uploaded is "NO" → Tell user to upload CSV first
- If Data Uploaded is "YES" → Confirm ready to analyze
- Keep responses under 100 words
"""


def chat_node(state):
    """
    General chat/fallback node with smart caching and data-aware context
    Ultra-fast responses for common queries
    
    Args:
        state: Current agent state with messages
        
    Returns:
        Updated state with conversational response
    """
    messages = state["messages"]
    
    # Get last user message
    last_user_message = next(
        (msg.content for msg in reversed(messages) if hasattr(msg, 'content')),
        ""
    )
    
    # STEP 1: Check smart cache first (instant response)
    cached_response = get_smart_response(last_user_message)
    if cached_response:
        return {
            "messages": [AIMessage(content=cached_response)],
            "loop_step": 1,
            "current_node": "chat"
        }
    
    # STEP 2: Check data status (to make AI context-aware)
    df = SESSION_DATA.get('default')
    has_data = "YES" if df is not None else "NO"
    filename = "Amazon_Reviews.csv" if df is not None else "Not uploaded yet"
    total_reviews = f"{len(df):,}" if df is not None else "0"
    
    # STEP 3: Build dynamic system prompt with data context
    system_prompt = CHAT_PROMPT_TEMPLATE.format(
        has_data=has_data,
        filename=filename,
        total_reviews=total_reviews
    )
    
    # STEP 4: Build conversation context (sliding window)
    # Filter only HumanMessage and AIMessage (exclude old SystemMessage)
    chat_history = []
    for msg in messages[-10:]:  # Last 10 messages
        if isinstance(msg, (HumanMessage, AIMessage)):
            chat_history.append(msg)
    
    # STEP 5: Construct final message list
    # [New System Prompt] + [Recent Chat History]
    context_messages = [SystemMessage(content=system_prompt)] + chat_history
    
    # STEP 6: Invoke LLM with full context
    response = llm.invoke(context_messages)
    
    # STEP 7: Cache the response for future use
    RESPONSE_CACHE.set(last_user_message, response.content)
    
    return {
        "messages": [response],
        "loop_step": 1,
        "current_node": "chat"
    }

