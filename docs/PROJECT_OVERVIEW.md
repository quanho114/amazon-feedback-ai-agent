# 📋 TỔNG QUAN DỰ ÁN - Amazon Feedback AI Agent

> **Tài liệu này ghi lại toàn bộ quá trình phát triển từ đầu đến giờ**  
> Ngày cập nhật: 2024-12-07

---

## 🎯 MỤC TIÊU DỰ ÁN

Xây dựng hệ thống AI phân tích feedback khách hàng Amazon với:
- ✅ Multi-agent system (6 workers)
- ✅ ML Model (SVM 90% accuracy)
- ✅ RAG Search (ChromaDB + Reranking)
- ✅ Smart Summarizer (Gatekeeper pattern)
- ✅ React Frontend + FastAPI Backend

---

## 🏗️ KIẾN TRÚC TỔNG QUAN

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND                           │
│              (Vite + Tailwind + Recharts)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP API
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                          │
│                      (api.py)                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /api/upload  → Upload CSV + Run SVM Model          │  │
│  │  /api/chat    → Multi-agent routing                 │  │
│  │  /api/sentiment → Get sentiment stats               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              LANGGRAPH SUPERVISOR (graph.py)                │
│                   Pattern Matching + LLM Routing            │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌──────────────────┐                  ┌──────────────────────┐
│   6 AI WORKERS   │                  │   CORE MODULES       │
│   (Nodes)        │  ──── calls ──>  │   (Logic Layer)      │
└──────────────────┘                  └──────────────────────┘
│                                      │
├─ chat_node                           ├─ sentiment_model.py
│  (Trò chuyện chung)                  │  (SVM 90% accuracy)
│                                      │
├─ sentiment_node ─────────────────────┤
│  (Phân tích cảm xúc)                 │
│                                      ├─ smart_summarizer.py
├─ summarize_node ─────────────────────┤  (Gatekeeper pattern)
│  (Tóm tắt reviews)                   │
│                                      ├─ vector_search.py
├─ rag_node ───────────────────────────┤  (ChromaDB)
│  (Tìm kiếm reviews)                  │
│                                      ├─ advanced_rag.py
├─ analyst_node                        │  (Reranking)
│  (Tính toán + vẽ chart)              │
│                                      ├─ stats.py
├─ insight_node                        │  (Statistics)
│  (Tư vấn chiến lược)                 │
│                                      └─ forecasting.py
│                                         (Trend analysis)
└──────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ SESSION_DATA │  │  ChromaDB    │  │  SVM Model   │     │
│  │  (DataFrame) │  │ (Vector DB)  │  │   (.pkl)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 LUỒNG XỬ LÝ CHI TIẾT

### **Phase 1: Upload & Preprocessing**

```
User Upload CSV
      ↓
┌─────────────────────────────────────────────────────────┐
│ api.py - POST /api/upload                               │
├─────────────────────────────────────────────────────────┤
│ 1. Đọc CSV file                                         │
│    df = pd.read_csv(file)                               │
│                                                          │
│ 2. Chạy SVM Model (90% accuracy)                        │
│    from src.analytics.sentiment_model import            │
│         analyze_dataframe                               │
│    df = analyze_dataframe(df, text_col='Review Text')   │
│    → Tạo cột 'ai_sentiment' (positive/negative/neutral) │
│                                                          │
│ 3. Lưu vào Session                                      │
│    SESSION_DATA['default'] = df                         │
│                                                          │
│ 4. Ingest vào ChromaDB (RAG)                            │
│    from src.rag.vector_search import ingest_data        │
│    ingest_data(df, text_column='Review Text')           │
│    → Tạo vector embeddings + metadata                   │
└─────────────────────────────────────────────────────────┘
      ↓
✅ Data sẵn sàng cho analysis
```

---

### **Phase 2: User Query Processing**

```
User: "Phân tích sentiment cho tôi"
      ↓
┌─────────────────────────────────────────────────────────┐
│ api.py - POST /api/chat                                 │
├─────────────────────────────────────────────────────────┤
│ 1. Nhận message từ user                                 │
│ 2. Build state với conversation history                 │
│ 3. Gọi LangGraph agent                                  │
│    agent_graph.stream(inputs)                           │
└─────────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────────┐
│ graph.py - Supervisor Node                              │
├─────────────────────────────────────────────────────────┤
│ 1. Pattern Matching (Fast Path)                         │
│    - "bao nhiêu" → ANALYST                              │
│    - "tìm" → RAG                                        │
│    - "cảm xúc" → SENTIMENT                              │
│    - "insight" → INSIGHT                                │
│                                                          │
│ 2. LLM Routing (Fallback)                               │
│    - Nếu không match pattern → Gọi LLM                  │
│    - LLM quyết định worker phù hợp                      │
└─────────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────────┐
│ sentiment_node.py - Worker Node                         │
├─────────────────────────────────────────────────────────┤
│ 1. Lấy DataFrame từ SESSION_DATA                        │
│    df = SESSION_DATA.get('default')                     │
│                                                          │
│ 2. Đọc cột 'ai_sentiment' (từ SVM)                      │
│    sentiment_counts = df['ai_sentiment'].value_counts() │
│    → positive: 7500, negative: 1500, neutral: 1000      │
│                                                          │
│ 3. Lấy sample reviews                                   │
│    - 3 negative samples (pain points)                   │
│    - 2 positive samples (strengths)                     │
│                                                          │
│ 4. Gọi LLM để phân tích insights                        │
│    llm.invoke([SystemMessage, HumanMessage])            │
│    → Tạo report với strengths, pain points, actions     │
│                                                          │
│ 5. Share analysis_data với nodes khác                   │
│    analysis_data = {                                    │
│        "total_reviews": 10000,                          │
│        "sentiment_counts": {...},                       │
│        "sentiment_distribution": {...}                  │
│    }                                                    │
└─────────────────────────────────────────────────────────┘
      ↓
✅ Trả response về user
```

---

## 🤖 CHI TIẾT 6 AI WORKERS

### **1. chat_node.py** 💬
**Nhiệm vụ:** Trò chuyện chung, hướng dẫn user

**Đặc điểm:**
- ✅ Check data status (có data chưa?)
- ✅ Smart cache (instant response)
- ✅ Context-aware (nhớ lịch sử chat)
- ✅ Sliding window (10 messages gần nhất)

**Khi nào dùng:**
- Chào hỏi, giới thiệu
- Hỏi về tính năng
- Câu hỏi chung chung

---

### **2. sentiment_node.py** 🎭
**Nhiệm vụ:** Phân tích cảm xúc khách hàng

**Flow:**
1. Đọc cột `ai_sentiment` (từ SVM model)
2. Tính distribution (positive/negative/neutral %)
3. Lấy sample reviews (3 negative + 2 positive)
4. LLM phân tích: strengths, pain points, recommendations
5. Share `analysis_data` với insight_node

**Output:**
```
## CUSTOMER SENTIMENT ANALYSIS
### Overview
- Positive: 75% (7,500 reviews)
- Negative: 15% (1,500 reviews)

### Key Strengths
- Fast delivery
- Good product quality

### Areas for Improvement
- Customer service response time
- Refund process complexity

### Recommendations
1. Implement 24/7 chat support
2. Simplify refund workflow
3. Train CS team on empathy
```

---

### **3. rag_node.py** 🔍
**Nhiệm vụ:** Tìm kiếm reviews cụ thể

**Tech Stack:**
- ChromaDB (vector database)
- HuggingFace Embeddings (all-MiniLM-L6-v2)
- Cross-encoder reranking (ms-marco-MiniLM)

**Flow:**
1. Detect sentiment filter (negative/positive)
2. Query expansion (optional)
3. Vector search (top 10)
4. Reranking (top 5)
5. LLM synthesize answer

**Ví dụ:**
```
User: "Tìm reviews về delivery problems"
→ RAG tìm 5 reviews liên quan
→ LLM tổng hợp: "Khách hàng phản ánh 3 vấn đề chính:
   1. Giao hàng trễ 2-3 ngày
   2. Shipper không gọi điện
   3. Hàng bị ướt do mưa"
```

---

### **4. summarize_node.py** 📝
**Nhiệm vụ:** Tóm tắt reviews thông minh

**Gatekeeper Pattern:**
```python
# Chỉ gọi LLM khi cần thiết (tiết kiệm 70% API calls)

if len(review) < 10 words:
    → SKIP (quá ngắn, đã là summary)
    
elif sentiment == 'positive' and no_issues:
    → SKIP (không có vấn đề)
    
elif sentiment == 'negative':
    → ANALYZE with LLM (extract root cause)
    
elif is_mixed_review:
    → ANALYZE with LLM (separate pros/cons)
```

**Smart Summarizer:**
- Topic classification (keyword-based, không dùng LLM)
- Issue extraction (LLM)
- Severity assessment (High/Medium/Low)

---

### **5. analyst_node.py** 📊
**Nhiệm vụ:** Tính toán số liệu + vẽ chart

**Code Interpreter Pattern:**
```python
# LLM tạo Python code → Execute → Trả kết quả

User: "Có bao nhiêu positive reviews?"
→ LLM tạo code:
    result = int(df['ai_sentiment'].value_counts()['positive'])
→ Execute: result = 7500
→ Response: "✅ Kết quả: 7,500 positive reviews"

User: "Vẽ pie chart sentiment"
→ LLM tạo code:
    chart_data = {
        "type": "pie",
        "data": [{"name": "Positive", "value": 7500}, ...]
    }
→ Frontend nhận JSON → Vẽ bằng Recharts
```

**8 loại chart hỗ trợ:**
- Pie, Bar, Line, Scatter, Area, Radar, Treemap, Composed

---

### **6. insight_node.py** 💡
**Nhiệm vụ:** Tư vấn chiến lược kinh doanh

**Flow:**
1. Nhận `analysis_data` từ sentiment_node (hoặc tính từ DataFrame)
2. LLM phân tích chiến lược với framework:
   - Pattern Recognition
   - Root Cause Analysis
   - Impact Assessment
   - Action Planning

**Output:**
```
## [ANALYSIS] Key Findings
- 15% negative reviews concentrated in delivery
- Customer service complaints increased 20%

## [INSIGHTS] Strategic Implications
1. **Delivery Optimization**: High impact on NPS
2. **CS Training**: Reduce churn rate

## [ACTIONS] Recommended Next Steps
Priority 1: Implement real-time tracking
Priority 2: Hire 5 more CS agents
Priority 3: Create self-service portal

## [RISKS] Potential Concerns
- Risk 1: Delivery partners may resist change
- Risk 2: Training cost $50K
```

---

## 🧠 CORE MODULES (Logic Layer)

### **1. sentiment_model.py** (SVM 90% accuracy)

**Training Process:**
```python
# 1. Load data
df = pd.read_csv('Amazon_Reviews.csv')

# 2. Preprocess
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    return text

# 3. TF-IDF Vectorization
vectorizer = TfidfVectorizer(max_features=5000)
X = vectorizer.fit_transform(texts)

# 4. Train SVM
model = LinearSVC()
model.fit(X_train, y_train)

# 5. Save model
pickle.dump(model, open('sentiment_svm.pkl', 'wb'))
pickle.dump(vectorizer, open('sentiment_vectorizer.pkl', 'wb'))
```

**Usage:**
```python
# Predict single text
sentiment = predict_sentiment("This product is amazing!")
# → "positive"

# Predict batch (faster)
sentiments = predict_batch(texts_list)

# Add to DataFrame
df = analyze_dataframe(df, text_col='Review Text')
# → Tạo cột 'ai_sentiment'
```

**Performance:**
- Accuracy: 90.10%
- F1-Score: 0.8877
- Speed: ~3.5ms/review
- Batch: ~0.5ms/review

---

### **2. smart_summarizer.py** (Gatekeeper)

**Architecture:**
```
Review Input
    ↓
┌─────────────────────┐
│   GATEKEEPER        │
│  (Rule-based)       │
├─────────────────────┤
│ • Length check      │
│ • Sentiment check   │
│ • Issue keywords    │
└─────────────────────┘
    ↓           ↓
  SKIP        ANALYZE
  (70%)       (30%)
              ↓
    ┌─────────────────┐
    │  TOPIC CLASSIFY │
    │  (Keyword-based)│
    ├─────────────────┤
    │ • Delivery      │
    │ • CS            │
    │ • Account       │
    │ • Refund        │
    └─────────────────┘
              ↓
    ┌─────────────────┐
    │   LLM ANALYZE   │
    │  (Only 30%)     │
    ├─────────────────┤
    │ • Extract issue │
    │ • Severity      │
    │ • Tags          │
    └─────────────────┘
```

**Cost Savings:**
- Traditional: 100% LLM calls
- Smart: 30% LLM calls
- **Savings: 70% API cost** 💰

---

### **3. advanced_rag.py** (Reranking)

**Pipeline:**
```
User Query
    ↓
┌─────────────────────┐
│ Query Expansion     │ (Optional)
│ "delivery problem"  │
│ → "late delivery"   │
│ → "shipping issue"  │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ Vector Search       │
│ (ChromaDB)          │
│ Top 10 results      │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ Deduplication       │
│ (MD5 hash)          │
│ Remove duplicates   │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ Cross-Encoder       │
│ Reranking           │
│ Top 5 results       │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ LLM Synthesis       │
│ Generate answer     │
└─────────────────────┘
```

**Optimizations:**
1. Confidence Score: Sigmoid(logit)
2. Deduplication: MD5 hash
3. Query Expansion: Optional (default off)
4. Retry Logic: 3 attempts with backoff

---

## 📁 CẤU TRÚC PROJECT

```
amazon-feedback-ai-agent/
│
├── 🔧 Backend (FastAPI)
│   ├── api.py                      # REST API server
│   ├── requirements.txt            # Dependencies
│   └── src/
│       ├── agents/                 # Multi-agent system
│       │   ├── graph.py           # Supervisor routing
│       │   ├── state.py           # State management
│       │   ├── tools.py           # Data tools
│       │   └── nodes/             # 6 AI workers
│       │       ├── chat_node.py
│       │       ├── sentiment_node.py
│       │       ├── analyst_node.py
│       │       ├── rag_node.py
│       │       ├── insight_node.py
│       │       └── summarize_node.py
│       │
│       ├── rag/                    # Vector search
│       │   ├── vector_search.py   # ChromaDB
│       │   └── advanced_rag.py    # Reranking
│       │
│       ├── analytics/              # ML & Analytics
│       │   ├── sentiment_model.py # SVM 90%
│       │   ├── smart_summarizer.py # Gatekeeper
│       │   ├── stats.py           # Statistics
│       │   └── forecasting.py     # Trend analysis
│       │
│       ├── utils/                  # Utilities
│       │   └── cache.py           # Response cache
│       │
│       └── config.py               # Configuration
│
├── 🎨 Frontend (React + Vite)
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   │   ├── ChatInterface.jsx
│       │   │   ├── ChartDisplay.jsx    # 8 chart types
│       │   │   ├── Dashboard.jsx
│       │   │   └── FileUpload.jsx
│       │   ├── services/
│       │   │   └── api.js              # API integration
│       │   └── App.jsx
│       ├── package.json
│       └── vite.config.js
│
├── 📁 Data
│   └── data/
│       ├── raw/                    # CSV uploads
│       ├── processed/              # Processed data
│       └── vector_store/           # ChromaDB storage
│
├── 🤖 Models
│   └── models/
│       ├── sentiment_svm.pkl       # Trained SVM
│       └── sentiment_vectorizer.pkl # TF-IDF
│
├── 📚 Documentation
│   └── docs/
│       ├── PROJECT_OVERVIEW.md     # This file
│       ├── DEPLOYMENT.md
│       ├── SENTIMENT_BENCHMARK.md
│       └── INSIGHT_NODE_FIX.md
│
└── 🚀 Scripts
    └── scripts/
        ├── start_backend.bat
        ├── start_frontend.bat
        ├── run_benchmark.py
        └── save_best_model.py
```

---

## 🔄 STATE MANAGEMENT

### **AgentState Structure:**
```python
class AgentState(TypedDict):
    # Chat history (accumulated)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Loop counter (prevent infinite loops)
    loop_step: Annotated[int, operator.add]
    
    # DataFrame metadata
    data_info: dict
    
    # Current node name (for debugging)
    current_node: str
    
    # Shared analysis data (between nodes)
    analysis_data: dict  # ← sentiment_node share với insight_node
```

### **Data Flow Between Nodes:**
```
sentiment_node:
    analysis_data = {
        "total_reviews": 10000,
        "sentiment_counts": {
            "positive": 7500,
            "negative": 1500,
            "neutral": 1000
        },
        "sentiment_distribution": {
            "positive": "75.0%",
            "negative": "15.0%",
            "neutral": "10.0%"
        }
    }
    ↓
insight_node:
    # Nhận analysis_data từ state
    analysis_data = state.get("analysis_data", {})
    # Dùng để tạo strategic insights
```

---

## 🎯 TECH STACK

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + Vite | Modern UI framework |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Charts** | Recharts | Data visualization |
| **Backend** | FastAPI | REST API server |
| **AI Framework** | LangGraph | Multi-agent orchestration |
| **LLM** | OpenAI/Gemini | Language models |
| **ML Model** | Scikit-learn SVM | Sentiment classification |
| **Vector DB** | ChromaDB | Semantic search |
| **Embeddings** | HuggingFace | Text embeddings |
| **Reranking** | Cross-Encoder | Result reranking |

---

## 📊 PERFORMANCE METRICS

### **SVM Model:**
- Accuracy: 90.10%
- F1-Score: 0.8877
- Precision: 0.89
- Recall: 0.88
- Speed: 3.5ms/review (single), 0.5ms/review (batch)

### **Smart Summarizer:**
- LLM Call Rate: 30%
- Skip Rate: 70%
- Cost Savings: 70%
- Accuracy: Maintained (same quality)

### **RAG System:**
- Query Expansion: Optional (default off for speed)
- Reranking: Cross-encoder (ms-marco-MiniLM)
- Confidence: Sigmoid(logit)
- Deduplication: MD5 hash

### **API Response Time:**
- Chat (cached): <100ms
- Chat (LLM): 1-3s
- Sentiment Analysis: 2-4s
- RAG Search: 3-5s
- Chart Generation: 1-2s

---

## 🚀 DEPLOYMENT

### **Local Development:**
```bash
# Backend
python api.py

# Frontend
cd frontend
npm run dev
```

### **Docker:**
```bash
docker-compose up -d
```

### **Production:**
- Railway (recommended)
- VPS Ubuntu
- AWS/GCP/Azure

---

## ✅ HOÀN THÀNH

### **Phase 1: Core System** ✅
- [x] FastAPI backend
- [x] React frontend
- [x] LangGraph multi-agent
- [x] 6 AI workers

### **Phase 2: ML & Analytics** ✅
- [x] SVM sentiment model (90%)
- [x] Smart summarizer (Gatekeeper)
- [x] Statistics & forecasting

### **Phase 3: RAG System** ✅
- [x] ChromaDB vector search
- [x] Advanced RAG (reranking)
- [x] Query expansion

### **Phase 4: Optimization** ✅
- [x] Smart cache
- [x] Error handling
- [x] Context awareness
- [x] Sample reviews in prompts

### **Phase 5: Cleanup** ✅
- [x] Xóa test files
- [x] Xóa legacy code (charts.py)
- [x] Update imports
- [x] Documentation

---

## 🔜 TIẾP THEO (TODO)

### **Cần làm tiếp:**
1. ⏳ Test toàn bộ hệ thống
2. ⏳ Fix bugs (nếu có)
3. ⏳ Optimize performance
4. ⏳ Add more chart types
5. ⏳ Improve prompts
6. ⏳ Add authentication
7. ⏳ Deploy to production

### **Nice to have:**
- [ ] Real-time streaming responses
- [ ] Multi-language support
- [ ] Export reports (PDF/Excel)
- [ ] Email notifications
- [ ] Dashboard analytics
- [ ] A/B testing framework

---

## 📝 GHI CHÚ QUAN TRỌNG

### **1. SVM Model chỉ chạy 1 lần:**
```python
# ✅ ĐÚNG - Chạy khi upload
api.py → analyze_dataframe() → Tạo cột 'ai_sentiment'

# ❌ SAI - Không chạy lại ở nodes
sentiment_node.py → CHỈ ĐỌC cột 'ai_sentiment'
```

### **2. LLM không dùng để classify:**
```python
# ✅ ĐÚNG
SVM Model → Classify sentiment (positive/negative/neutral)
LLM → Analyze insights (strengths, pain points, recommendations)

# ❌ SAI
LLM → Classify sentiment (chậm, tốn tiền, không ổn định)
```

### **3. Data flow:**
```
Upload CSV
    ↓
SVM classify → 'ai_sentiment' column
    ↓
SESSION_DATA['default'] = df
    ↓
All nodes read from SESSION_DATA
```

### **4. Nodes không gọi nhau:**
```
# ✅ ĐÚNG
Supervisor → Route to 1 node → Execute → Return

# ❌ SAI
sentiment_node → gọi insight_node → gọi analyst_node
(Không có chain như vậy!)
```

### **5. analysis_data sharing:**
```python
# sentiment_node tạo và share
return {
    "analysis_data": {...}  # Share với nodes khác
}

# insight_node nhận
analysis_data = state.get("analysis_data", {})
```

---

## 🎓 BÀI HỌC RÚT RA

1. **Separation of Concerns:** ML model riêng, LLM riêng, rõ ràng
2. **Performance First:** Cache, gatekeeper, pattern matching
3. **Error Handling:** Try-catch, fallback, retry logic
4. **Context Awareness:** Nodes biết data status, conversation history
5. **Cost Optimization:** Smart summarizer tiết kiệm 70% API calls
6. **User Experience:** Fast response, clear error messages

---

## 📞 SUPPORT

Nếu quên đang làm gì:
1. Đọc file này từ đầu
2. Check TODO list
3. Xem git log
4. Review code comments

---

**🎉 Project đã hoàn thành 95%! Còn testing + deployment!**

