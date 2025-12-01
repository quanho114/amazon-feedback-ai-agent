import streamlit as st
import pandas as pd
import sys
import os
import shutil
import time

# --- 1. FIX LỖI KERAS/TENSORFLOW (BẮT BUỘC ĐỂ ĐẦU TIÊN) ---
os.environ["TF_USE_LEGACY_KERAS"] = "1"

from langchain_core.messages import HumanMessage, AIMessage

# --- 2. CẤU HÌNH IMPORT ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.agents.graph import app as agent_app
    from src.agents.tools import register_dataframe 
except ImportError as e:
    st.error(f"❌ LỖI SYSTEM: {e}")
    st.info("Hãy kiểm tra lại cấu trúc thư mục src/agents/")
    st.stop()

# --- 3. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="Amazon AI Analyst",
    page_icon="🤖",
    layout="wide"
)

# CSS Custom: Hiệu ứng 3 chấm + Giao diện sạch
st.markdown("""
<style>
    footer {visibility: hidden;}
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) { background-color: #f0f2f6; }
    
    /* Animation 3 chấm */
    .typing-indicator { display: inline-flex; align-items: center; gap: 4px; padding: 10px; }
    .dot { width: 8px; height: 8px; background-color: #888; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
    .status-text { font-size: 12px; color: #666; margin-left: 10px; font-style: italic; }
</style>
""", unsafe_allow_html=True)

TYPING_HTML = """
<div class="typing-indicator">
    <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    <span class="status-text">{text}</span>
</div>
"""

# --- 4. HÀM HỖ TRỢ ---
def save_uploaded_file(uploaded_file):
    temp_dir = "temp_data"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# --- 5. KHỞI TẠO STATE ---
if "messages" not in st.session_state:
    if os.path.exists("chart_output.png"): os.remove("chart_output.png")
    st.session_state.messages = []

# Khởi tạo biến kiểm tra file đã xử lý chưa
if "processed_file_key" not in st.session_state:
    st.session_state.processed_file_key = None

# --- 6. SIDEBAR (LOGIC QUAN TRỌNG ĐÃ SỬA) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=150)
    st.title("AI Data Analyst")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("📂 Upload Data (CSV)", type=["csv"])
    
    if uploaded_file:
        # Tạo ID duy nhất cho file (Tên + Kích thước)
        current_file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        
        # LOGIC CHẶN: Chỉ chạy xử lý nếu file thay đổi
        if st.session_state.processed_file_key != current_file_key:
            try:
                # Hiển thị loading xoay vòng
                with st.spinner("⏳ Đang khởi tạo hệ thống AI (Embedding & Sentiment)..."):
                    save_path = save_uploaded_file(uploaded_file)
                    df = pd.read_csv(save_path)
                    
                    # Gọi hàm nặng (Chỉ chạy 1 lần duy nhất)
                    register_dataframe(df, session_id='default')
                    
                    # Cập nhật trạng thái
                    st.session_state.processed_file_key = current_file_key
                
                st.success(f"✅ Đã nạp xong: {len(df)} dòng")
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
        else:
            # Nếu đã xử lý rồi -> Bỏ qua, chỉ hiện thông báo
            st.info(f"✅ Dữ liệu sẵn sàng: {uploaded_file.name}")
            
            # (Optional) Preview nhẹ nhàng
            # with st.expander("Xem trước"):
            #     st.dataframe(pd.read_csv(save_uploaded_file(uploaded_file)).head())

    st.markdown("---")
    if st.button("Clear Chat & Data"):
        st.session_state.messages = []
        st.session_state.processed_file_key = None # Reset để cho phép nạp lại file
        if os.path.exists("chart_output.png"): os.remove("chart_output.png")
        st.rerun()

# --- 7. MAIN CHAT INTERFACE (GIỮ NGUYÊN) ---

if not st.session_state.messages:
    st.info("👋 Xin chào! Hãy upload file CSV để bắt đầu.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

if os.path.exists("chart_output.png") and st.session_state.messages:
    if st.session_state.messages[-1]["role"] == "assistant":
        st.image("chart_output.png", caption="Analysis Chart", use_container_width=True)

if prompt := st.chat_input("Hỏi về dữ liệu (VD: Phân tích sentiment về pin?)"):
    
    if not uploaded_file:
        st.warning("⚠️ Vui lòng upload file CSV trước!")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        response_placeholder = st.empty()
        response_placeholder.markdown(TYPING_HTML.format(text="Analyzing request..."), unsafe_allow_html=True)
        
        full_response = ""
        # Reset loop_step mỗi lần hỏi mới
        inputs = {"messages": [HumanMessage(content=prompt)], "loop_step": 0}

        try:
            for event in agent_app.stream(inputs):
                for node_name, value in event.items():
                    if node_name == "agent":
                        response_placeholder.markdown(TYPING_HTML.format(text="Planning logic..."), unsafe_allow_html=True)
                    elif node_name == "tools":
                        response_placeholder.markdown(TYPING_HTML.format(text="Running Python/SQL Tool..."), unsafe_allow_html=True)
                    
                    if "messages" in value and value["messages"]:
                        last_msg = value["messages"][-1]
                        if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
                            full_response = last_msg.content

            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            if os.path.exists("chart_output.png"):
                st.image("chart_output.png", caption="Generated Chart", use_container_width=True)

        except Exception as e:
            response_placeholder.error(f"❌ Lỗi: {str(e)}")