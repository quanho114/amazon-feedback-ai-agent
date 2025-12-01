# File: src/test_model.py
from langchain_openai import ChatOpenAI
from src.config import MEGALLM_API_KEY, MEGALLM_BASE_URL, MEGALLM_MODEL

def test_megallm():
    print(f"🚀 Đang gửi tin nhắn tới model: {MEGALLM_MODEL}...")
    
    # 1. Khởi tạo kết nối
    try:
        llm = ChatOpenAI(
            api_key=MEGALLM_API_KEY,
            base_url=MEGALLM_BASE_URL,
            model=MEGALLM_MODEL,
            temperature=0.7 # Độ sáng tạo
        )

        # 2. Gửi thử một câu hỏi
        question = "Xin chào, hãy giới thiệu ngắn gọn bạn là ai?"
        print(f"👤 User: {question}")
        
        response = llm.invoke(question)
        
        # 3. In câu trả lời
        print("\n" + "="*30)
        print(f"🤖 MegaLLM trả lời:\n{response.content}")
        print("="*30 + "\n")
        print("✅ CHÚC MỪNG! Model hoạt động ngon lành.")

    except Exception as e:
        print("\n❌ LỖI KẾT NỐI RỒI!")
        print(f"Chi tiết lỗi: {e}")
        print("👉 Gợi ý: Kiểm tra lại API Key hoặc Base URL xem có đúng của MegaLLM không.")

if __name__ == "__main__":
    test_megallm()