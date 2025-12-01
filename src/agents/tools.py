import pandas as pd
import os
import matplotlib.pyplot as plt
from langchain_core.tools import tool
from langchain_experimental.tools import PythonAstREPLTool

# --- IMPORTS AI ---
from textblob import TextBlob
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# --- GLOBAL STORE ---
SESSION_DATA = {}
VECTOR_DB = None
_MODEL_CACHE = None 

# --- 1. MODEL CACHE (GIỮ NGUYÊN) ---
def get_embedding_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        print("📥 Đang tải Model Embedding (Lần đầu tiên)...")
        _MODEL_CACHE = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _MODEL_CACHE

# --- 2. LOGIC SENTIMENT MỚI (ƯU TIÊN RATING) ---
def _analyze_sentiment_from_rating(score):
    """Quy đổi điểm số sang sentiment"""
    try:
        score = float(score)
        if score >= 4: return "positive"
        elif score <= 2: return "negative"
        else: return "neutral"
    except:
        return "neutral"

def _analyze_sentiment_from_text(text):
    """Fallback: Nếu không có rating thì mới dùng TextBlob (chậm hơn chút)"""
    if not isinstance(text, str): return "neutral"
    score = TextBlob(text).sentiment.polarity
    if score > 0.1: return "positive"
    elif score < -0.1: return "negative"
    else: return "neutral"

# --- 3. QUY TRÌNH XỬ LÝ (NÂNG CẤP) ---
def process_and_index_data(df: pd.DataFrame, session_id: str = 'default'):
    print("⏳ Bắt đầu quy trình xử lý dữ liệu...")
    
    # BƯỚC A: SENTIMENT (LOGIC THÔNG MINH)
    # 1. Tìm xem có cột rating không (rating, star, score...)
    rating_col = next((col for col in df.columns if col in ['rating', 'star', 'stars', 'score']), None)
    
    # 2. Tìm cột text (review, content...)
    text_col = next((col for col in df.columns if 'review' in col.lower() or 'text' in col.lower()), None)

    if rating_col:
        print(f"🚀 Phát hiện cột '{rating_col}'. Dùng rating để gán nhãn (Siêu tốc).")
        df['ai_sentiment'] = df[rating_col].apply(_analyze_sentiment_from_rating)
    elif text_col:
        print("⚠️ Không thấy cột rating. Dùng TextBlob để phân tích (Chậm hơn xíu).")
        df['ai_sentiment'] = df[text_col].apply(_analyze_sentiment_from_text)
    else:
        df['ai_sentiment'] = 'neutral' # Không có cả text lẫn rating

    print("✅ [Sentiment] Đã gán nhãn xong.")
    
    # BƯỚC B: VECTOR EMBEDDING (VẪN CẦN CHẠY ĐỂ SEARCH)
    # (Bước này bắt buộc phải chạy trên text để trả lời câu hỏi "Tìm review về pin...")
    global VECTOR_DB
    if text_col:
        print("⏳ [Embedding] Đang vector hóa dữ liệu (Bước này cần vài giây)...")
        
        embedding_model = get_embedding_model()
        
        docs = [
            Document(
                page_content=str(row[text_col]), 
                metadata={
                    "source": str(i), 
                    "sentiment": row.get('ai_sentiment', 'unknown'),
                    "rating": str(row.get(rating_col, 'N/A')) # Lưu thêm rating gốc vào metadata
                }
            )
            for i, row in df.iterrows()
        ]
        
        VECTOR_DB = Chroma.from_documents(
            documents=docs, 
            embedding=embedding_model,
            collection_name=f"sess_{session_id}"
        )
        print("✅ [Embedding] Đã tạo xong Vector Index!")

    return df

# --- 4. HÀM REGISTER (GIỮ NGUYÊN) ---
def register_dataframe(df: pd.DataFrame, session_id: str = 'default'):
    df.columns = [c.lower().replace(" ", "_").strip() for c in df.columns]
    processed_df = process_and_index_data(df, session_id)
    SESSION_DATA[session_id] = processed_df
    print(f"✅ Data registered for Session: {session_id}")

# --- 5. TOOLS (GIỮ NGUYÊN) ---
@tool
def search_knowledge_tool(query: str):
    """Semantic Search Tool."""
    global VECTOR_DB
    if VECTOR_DB is None: return "Error: No DB."
    
    print(f"🔍 Searching: '{query}'")
    results = VECTOR_DB.similarity_search(query, k=5)
    
    # Hiển thị thêm rating trong kết quả search
    output = "\n".join([f"- {doc.page_content} (Rating: {doc.metadata.get('rating')}, Sentiment: {doc.metadata['sentiment']})" for doc in results])
    return output

@tool
def python_analyst_tool(code: str):
    """Python Analyst Tool."""
    df = SESSION_DATA.get('default')
    if df is None: return "Error: No data."
    plt.switch_backend('Agg') 
    try:
        repl = PythonAstREPLTool(locals={"df": df})
        result = repl.invoke(code)
        if os.path.exists("chart_output.png"):
            return f"Result: {str(result)}\n(System: Chart saved at 'chart_output.png')"
        return f"Result: {str(result)}"
    except Exception as e:
        return f"Python Error: {str(e)}"