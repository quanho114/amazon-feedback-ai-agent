# 🏗️ KIẾN TRÚC HỆ THỐNG - Amazon Feedback AI Agent

> **Sơ đồ kiến trúc chi tiết và luồng xử lý**

---

## 📊 KIẾN TRÚC TỔNG QUAN (High-Level)

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                           │
│              React + Vite + Tailwind CSS                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ File Upload  │  │  AI Chat     │  │  Dashboard   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP REST API
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY                              │
│                   FastAPI (api.py)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  POST /api/upload    → Upload CSV + ML Processing   │  │
│  │  POST /api/chat      → Multi-agent routing          │  │
│  │  GET  /api/sentiment → Sentiment statistics         │  │
│  │  GET  /api/analytics → Dashboard data               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              ORCHESTRATION LAYER                            │
│           LangGraph Supervisor (graph.py)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Pattern Matching → Fast routing (no LLM)           │  │
│  │  LLM Routing      → Fallback for complex queries    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
