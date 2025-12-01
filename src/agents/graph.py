import operator
import logging
import os
from typing import Annotated, Sequence, TypedDict, List
from dotenv import load_dotenv

# --- IMPORT LIBRARY ---
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage 
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Import Tools từ file tools.py chúng ta đã build
from src.agents.tools import python_analyst_tool, search_knowledge_tool
from src.agents.schemas import AgentState
# Load biến môi trường (.env)
load_dotenv()

# Cấu hình log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AMAZON_BRAIN")

# --- 1. ĐỊNH NGHĨA STATE ---
class AgentState(TypedDict):
    # Lịch sử chat (Cộng dồn)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # Biến đếm số vòng lặp để tránh Agent chạy vô tận
    loop_step: Annotated[int, operator.add]

# --- 2. SETUP MODEL & TOOLS ---
tools = [python_analyst_tool, search_knowledge_tool]

# Sử dụng biến môi trường trực tiếp để an toàn hơn
llm = ChatOpenAI(
    api_key=os.getenv("MEGALLM_API_KEY"),
    base_url=os.getenv("MEGALLM_BASE_URL"),
    model=os.getenv("MEGALLM_MODEL"),
    temperature=0, # Set 0 cho các tác vụ Coding/Analyst
    streaming=True
)

llm_with_tools = llm.bind_tools(tools)

# --- 3. PROMPT SYSTEM ---
# Prompt này cực kỳ quan trọng: Nó báo cho Agent biết "df" đã nằm trong tay rồi.

SYSTEM_PROMPT = """
Bạn là Amazon AI Analyst.

DỮ LIỆU CÓ SẴN:
1. DataFrame `df`: Đã được tải sẵn.
2. Cột ĐẶC BIỆT: `df` đã có sẵn cột `ai_sentiment` (chứa giá trị: 'positive', 'neutral', 'negative').

CHIẾN THUẬT TỐC ĐỘ:
- Khi user hỏi "Có bao nhiêu review tích cực/tiêu cực?": 
  -> Dùng `python_analyst_tool` để `value_counts()` cột `ai_sentiment`. KHÔNG ĐƯỢC chạy lại hàm phân tích sentiment trên text.
  
- Khi user hỏi "Tìm các review nói về pin":
  -> Dùng `search_knowledge_tool` (Vector Search) để tìm theo ngữ nghĩa.

Tuyệt đối không dùng loop Python để xử lý text vì sẽ rất chậm.
"""
# --- 4. NODE AGENT ---
def agent_node(state):
    messages = list(state["messages"])
    
    # --- LOGIC QUẢN LÝ SYSTEM MESSAGE ---
    # Lọc bỏ SystemMessage cũ (nếu có) để tránh bị duplicate khi loop
    filtered_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
    
    # Luôn chèn System Message mới nhất vào đầu
    final_messages = [SystemMessage(content=SYSTEM_PROMPT)] + filtered_messages
    
    logger.info("🧠 Agent đang suy nghĩ...")
    
    # Gọi Model
    response = llm_with_tools.invoke(final_messages)
    
    # Trả về kết quả
    return {
        "messages": [response],
        "loop_step": 1 # Tăng biến đếm
    }

# --- 5. NODE CHECK LOOP (AN TOÀN) ---
def should_continue(state):
    last_message = state["messages"][-1]
    
    # Nếu Agent muốn gọi Tool
    if last_message.tool_calls:
        # Safety Check: Nếu chạy quá 10 bước mà chưa xong thì ngắt (tránh tốn tiền)
        if state.get("loop_step", 0) > 10:
            return END
        return "tools"
    
    # Nếu Agent đã có câu trả lời cuối cùng
    return END

# --- 6. XÂY DỰNG GRAPH ---
workflow = StateGraph(AgentState)

# Định nghĩa các Node
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools)) # ToolNode tự động chạy function trong tools.py

# Định nghĩa Luồng đi (Edge)
workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# Sau khi Tool chạy xong -> Quay lại Agent để suy luận tiếp
workflow.add_edge("tools", "agent")

# Compile
app = workflow.compile()