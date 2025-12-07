# 🤖 Amazon Feedback AI Agent

> Multi-Agent AI System for Automated Customer Feedback Analysis

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent multi-agent system powered by LangGraph, Machine Learning, and RAG for automated analysis of Amazon customer feedback. Achieves **90% sentiment classification accuracy** on 21,000+ reviews.

![Dashboard Preview](docs/screenshots/dashboard.png)

---

## ✨ Features

### 🤖 **Multi-Agent AI System**
- **6 Specialized Agents:** Chat, Sentiment, Analyst, RAG, Insight, Summarize
- **Intelligent Routing:** Supervisor agent with pattern matching + LLM classification
- **State Management:** Shared state across agents using LangGraph

### 🧠 **Machine Learning**
- **SVM Sentiment Model:** 90% accuracy, F1-score: 0.8877
- **Model Benchmarking:** Compared SVM vs Rating-based vs TextBlob
- **Real-time Processing:** <3.5ms per prediction

### 🔍 **Retrieval-Augmented Generation (RAG)**
- **Vector Search:** ChromaDB with Sentence Transformers
- **Semantic Search:** Context-aware document retrieval
- **Hybrid Search:** Keyword + semantic similarity

### 📊 **Interactive Dashboard**
- **5 Visualizations:** Pie, Bar, Stacked Bar charts
- **Real-time Analytics:** KPI tracking, trend analysis
- **Business Intelligence:** Actionable insights generation

### 💬 **Natural Language Interface**
- **Chat History:** Multi-session support with sidebar
- **Tutorial System:** Sample prompts and examples
- **Dark/Light Mode:** Customizable UI theme

---

## 🏗️ Architecture

```
┌─────────────┐
│   React UI  │ (Frontend)
└──────┬──────┘
       │
┌──────▼──────┐
│  FastAPI    │ (REST API)
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│     LangGraph Supervisor        │
│  (Intelligent Query Routing)    │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│        6 AI Agents              │
│  ┌────────────────────────────┐ │
│  │ Chat    │ Sentiment │ RAG  │ │
│  │ Analyst │ Insight   │ Sum. │ │
│  └────────────────────────────┘ │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   Data Layer                    │
│  - SVM Model (90% accuracy)     │
│  - Vector Store (ChromaDB)      │
│  - Session Management           │
└─────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- OpenAI API Key (or compatible LLM API)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/amazon-feedback-ai-agent.git
cd amazon-feedback-ai-agent
```

2. **Backend Setup**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API keys
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

4. **Run the Application**

Terminal 1 (Backend):
```bash
python api.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

5. **Open Browser**
```
http://localhost:5173
```

---

## 📖 Usage

### 1. Upload Data
- Click **"Upload Data"** tab
- Upload CSV file with customer reviews
- System automatically analyzes sentiment (SVM model)

### 2. Chat with AI
- Click **"AI Chat"** tab
- Ask questions like:
  - "Analyze sentiment distribution"
  - "Draw a pie chart for ratings"
  - "Find reviews about delivery problems"
  - "Give me business insights"

### 3. View Dashboard
- Click **"Analytics"** tab
- Explore 5 interactive visualizations
- View real-time KPIs and insights

### 4. Examples
- Click **"Examples"** button for sample prompts
- Click any prompt to auto-fill input

---

## 🛠️ Tech Stack

### Backend
- **Python 3.13**
- **FastAPI** - REST API framework
- **LangGraph** - Multi-agent orchestration
- **Scikit-learn** - SVM sentiment model
- **ChromaDB** - Vector database
- **Sentence Transformers** - Text embeddings
- **Pandas** - Data processing

### Frontend
- **React 18** - UI framework
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization
- **Lucide Icons** - Icon library
- **Vite** - Build tool

### AI/ML
- **OpenAI API** - LLM integration
- **Linear SVM** - Sentiment classification (90% accuracy)
- **TF-IDF** - Text vectorization
- **RAG** - Retrieval-augmented generation

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Sentiment Accuracy | 90.10% |
| F1-Score | 0.8877 |
| Processing Speed | ~3.5ms/review |
| Dataset Size | 21,055 reviews |
| API Response Time | <2s average |
| Agents | 6 specialized |

---

## 📁 Project Structure

```
amazon-feedback-ai-agent/
├── api.py                      # FastAPI backend
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
│
├── src/
│   ├── agents/
│   │   ├── graph.py           # LangGraph supervisor
│   │   ├── state.py           # Agent state management
│   │   ├── tools.py           # Shared tools
│   │   └── nodes/             # 6 AI agent nodes
│   │       ├── chat_node.py
│   │       ├── sentiment_node.py
│   │       ├── analyst_node.py
│   │       ├── rag_node.py
│   │       ├── insight_node.py
│   │       └── summarize_node.py
│   │
│   ├── analytics/
│   │   └── sentiment_model.py # SVM sentiment classifier
│   │
│   └── rag/
│       ├── vector_search.py   # RAG implementation
│       └── advanced_rag.py    # Advanced RAG features
│
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── FileUpload.jsx
│   │   │   └── ChartDisplay.jsx
│   │   ├── services/
│   │   │   └── api.js         # API client
│   │   └── App.jsx            # Main app
│   │
│   ├── package.json
│   └── vite.config.js
│
├── models/
│   ├── sentiment_svm.pkl      # Trained SVM model
│   └── sentiment_vectorizer.pkl
│
├── data/
│   ├── raw/                   # Raw CSV files
│   ├── processed/             # Processed data
│   └── vector_store/          # ChromaDB storage
│
└── docs/
    ├── ARCHITECTURE.md        # System architecture
    ├── DEPLOYMENT.md          # Deployment guide
    └── PROJECT_OVERVIEW.md    # Project documentation
```

---

## 🎯 Use Cases

### Business Intelligence
- Automated sentiment analysis
- Customer feedback monitoring
- Trend detection and alerts
- Actionable insights generation

### Customer Service
- Quick issue identification
- Common complaint analysis
- Response prioritization
- Service improvement recommendations

### Product Management
- Feature feedback analysis
- User satisfaction tracking
- Competitive analysis
- Product roadmap planning

---

## 🔮 Future Enhancements

- [ ] Export features (PDF, CSV, PNG)
- [ ] Advanced filtering (date, rating, keywords)
- [ ] Keyword/Topic extraction (Word cloud)
- [ ] Multi-language support
- [ ] Real-time collaboration
- [ ] Scheduled reports
- [ ] API access for developers

---

## 👥 Authors

**Ho Minh Quan** - DS/AIE  
Final Year Student, HCMUS  
[GitHub](https://github.com/YOUR_GITHUB) | [Email](mailto:your.email@example.com)

**Tran Nguyen Thanh Phong** - DA/DS  
Final Year Student, HCMUS  
[GitHub](https://github.com/PHONG_GITHUB) | [Email](mailto:phong.email@example.com)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangGraph** - Multi-agent framework
- **OpenAI** - LLM API
- **ChromaDB** - Vector database
- **Sentence Transformers** - Text embeddings
- **HCMUS** - Academic support

---

## 📞 Contact

For questions or feedback, please contact us via:
- GitHub Issues
- Email: [your.email@example.com](mailto:your.email@example.com)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by Quan & Phong

</div>
