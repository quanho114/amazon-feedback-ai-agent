import operator
from typing import Annotated, List, TypedDict, Union
from langchain_core.messages import BaseMessage

# Chúng ta chỉ cần đúng 1 class này thôi
class AgentState(TypedDict):
    # 1. messages: Lưu lịch sử chat (Bắt buộc cho LangGraph)
    # operator.add giúp nối tin nhắn mới vào danh sách cũ
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 2. (Optional) Các biến phụ trợ nếu cần kiểm soát luồng
    # Ví dụ: đếm số lần loop để tránh treo
    loop_step: int