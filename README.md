# 🛒 Amazon Feedback AI Agent
### Multi-Agent System for Customer Review Analysis

[![Tech Stack](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tech Stack](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Tech Stack](https://img.shields.io/badge/AI-LangGraph-FF6B6B?logo=ai&logoColor=white)](https://langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Full-stack AI application** với 6 workers multi-agent system, phân tích cảm xúc, RAG search, và data visualization.

---

## ✨ Features

🤖 **6-Agent System** - Chat, Sentiment, RAG, Analyst, Insight, Summarize  
📊 **8 Chart Types** - Pie, Bar, Line, Scatter, Area, Radar, Treemap, Composed  
🔍 **Vector Search** - ChromaDB với semantic search  
⚡ **Real-time Chat** - Streaming responses với LangGraph  
📈 **Analytics Dashboard** - Sentiment stats, trends, forecasting  
🎨 **Modern UI** - React + Tailwind CSS với glassmorphism design  

---

## 🚀 Quick Start (1 Click)

### Windows:
```cmd
start.bat
```

### Manual:
```bash
# Terminal 1 - Backend
python api.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

→ Mở trình duyệt: **http://localhost:3000**

---

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/quanho114/amazon-feedback-ai-agent.git
cd amazon-feedback-ai-agent
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env và thêm API keys
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 4. Environment Variables
Tạo file `.env`:
```env
MEGALLM_API_KEY=your_api_key_here
MEGALLM_BASE_URL=https://ai.megallm.io/v1
MEGALLM_MODEL=gemini-pro
```

---

## 🏗️ Project Structure

```
amazon-feedback-ai-agent/
│
├── 🔧 Backend (FastAPI)
│   ├── api.py                      # REST API server
│   ├── requirements.txt            # Python dependencies
│   └── src/
│       ├── agents/                 # Multi-agent system
│       │   ├── graph.py           # LangGraph workflow
│       │   ├── state.py           # Agent state management
│       │   ├── tools.py           # Data processing tools
│       │   └── nodes/             # 6 AI workers
│       │       ├── chat_node.py
│       │       ├── sentiment_node.py
│       │       ├── analyst_node.py
│       │       ├── rag_node.py
│       │       ├── insight_node.py
│       │       └── summarize_node.py
│       ├── rag/                    # Vector search (ChromaDB)
│       ├── analytics/              # Statistics & forecasting
│       └── utils/                  # Utilities & caching
│
├── 🎨 Frontend (React + Vite)
│   └── frontend/
│       ├── src/
│       │   ├── components/         # React components
│       │   │   ├── ChatInterface.jsx
│       │   │   ├── ChartDisplay.jsx    # 8 chart types
│       │   │   ├── Dashboard.jsx
│       │   │   └── FileUpload.jsx
│       │   ├── services/           # API integration
│       │   └── App.jsx             # Main application
│       ├── package.json
│       └── vite.config.js
│
├── 🐳 Deployment
│   ├── Dockerfile                  # Docker image
│   ├── docker-compose.yml          # Multi-container setup
│   ├── nginx.conf                  # Reverse proxy
│   └── deploy.sh                   # Deploy script
│
├── 📁 Data
│   └── data/
│       ├── raw/                    # CSV uploads
│       ├── processed/              # Processed data
│       └── vector_store/           # ChromaDB storage
│
└── 📚 Documentation
    ├── README.md                   # This file
    ├── DEPLOYMENT.md               # Deploy guide
    └── PROJECT_AUDIT.md            # Code review
```

---

## 🎯 Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | FastAPI | REST API server |
| **Frontend** | React 18 + Vite | Modern UI framework |
| **Styling** | Tailwind CSS | Utility-first CSS |
| **Charts** | Recharts | Data visualization |
| **AI Framework** | LangGraph | Multi-agent orchestration |
| **LLM** | OpenAI/Gemini | Language models |
| **Vector DB** | ChromaDB | Semantic search |
| **Embeddings** | HuggingFace | Text embeddings |

---

## 📊 API Endpoints

### Backend (Port 8000)

```
GET  /                      # Health check
GET  /api/health           # Detailed health status
GET  /api/data-status      # Check if data loaded

POST /api/upload           # Upload CSV file
POST /api/chat             # Chat with AI agent
GET  /api/sentiment        # Get sentiment analysis
GET  /api/analytics        # Get analytics data
```

### Frontend (Port 3000)

```
/                          # Main application
├── Upload Data            # CSV upload tab
├── AI Chat                # Chat interface
└── Analytics              # Dashboard & charts
```

---

## 🧪 Usage Example

### 1. Upload CSV Data
```javascript
// Upload file qua UI hoặc API
POST http://localhost:8000/api/upload
Content-Type: multipart/form-data

file: your_reviews.csv
```

### 2. Chat với AI
```javascript
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "Có bao nhiêu review tích cực?"
}
```

### 3. Vẽ Chart
```javascript
// Trong chat, gửi:
"Vẽ biểu đồ phân bố sentiment"
"Vẽ scatter chart rating vs độ dài review"
"Vẽ area chart xu hướng theo tháng"
```

---

## 🚀 Deployment

### Option 1: Docker (Recommended)
```bash
docker-compose up -d
```
→ Access: http://localhost

### Option 2: Railway (Free Cloud)
1. Push code lên GitHub
2. Vào https://railway.app
3. Deploy from GitHub repo
4. Thêm environment variables
5. Nhận public URL

### Option 3: VPS Ubuntu
```bash
./deploy.sh vps
```

📖 **Chi tiết**: Xem file [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork repo
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👤 Author

**Quan Ho**
- GitHub: [@quanho114](https://github.com/quanho114)
- Repository: [amazon-feedback-ai-agent](https://github.com/quanho114/amazon-feedback-ai-agent)

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) - AI framework
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend library
- [Recharts](https://recharts.org/) - Chart library
- [ChromaDB](https://www.trychroma.com/) - Vector database

---

## 📞 Support

Có vấn đề? Tạo [Issue](https://github.com/quanho114/amazon-feedback-ai-agent/issues) trên GitHub!

---

**⭐ Star repo nếu thấy hữu ích!**
