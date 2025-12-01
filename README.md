# 🛒 Amazon AI System Agent
### Intelligent Product Analysis & Insight Generation Platform

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-LangGraph-orange.svg)
![Model](https://img.shields.io/badge/LLM-Gemini%20Pro-green.svg)
![App](https://img.shields.io/badge/Frontend-Streamlit-red.svg)

## 📖 Giới thiệu (Overview)

**Amazon AI System Agent** là một hệ thống đa tác vụ (Multi-Agent System) được thiết kế để tự động hóa quy trình phân tích hàng nghìn đánh giá sản phẩm trên Amazon. Dự án không chỉ dừng lại ở việc tóm tắt văn bản, mà còn đóng vai trò như một "Nhà phân tích dữ liệu" ảo, có khả năng tra cứu thông tin kỹ thuật (RAG), phân tích cảm xúc sâu (Aspect-based Sentiment) và đưa ra các Insight kinh doanh chiến lược.

Điểm đặc biệt của hệ thống là kiến trúc **Hybrid AI** (kết hợp Machine Learning truyền thống và GenAI) để tối ưu hóa chi phí, cùng cơ chế **Human-in-the-loop** cho phép con người can thiệp vào các quyết định quan trọng.

---

## 🚀 Tính năng nổi bật (Key Features)

### 1. 🤖 Supervisor Multi-Agent Architecture (LangGraph)
Sử dụng mô hình Supervisor để điều phối đội ngũ nhân viên ảo:
- **Sentiment Agent:** Chuyên gia phân tích tâm lý khách hàng.
- **RAG Agent:** Chuyên gia tra cứu thông số kỹ thuật và chính sách từ tài liệu PDF.
- **Insight Agent:** Tổng hợp báo cáo và xu hướng.

### 2. ⚡ Hybrid Intelligence Pipeline
Kết hợp sức mạnh của NLP truyền thống và LLM:
- **Lớp 1 (Fast & Free):** Sử dụng model ML nhẹ (Logistic Regression/TF-IDF) để lọc spam và phân loại sơ bộ hàng nghìn review trong tích tắc.
- **Lớp 2 (Deep & Smart):** Chỉ những review quan trọng hoặc phức tạp mới được gửi đến **Gemini Pro** để phân tích sâu, giúp tiết kiệm đến 90% chi phí Token.

### 3. 🛑 Human-in-the-loop (HITL) Workflow
Cơ chế an toàn (Safety Guardrail) tích hợp trong LangGraph:
- Khi Agent gặp review nhập nhằng (độ tin cậy thấp), hệ thống sẽ **tự động TẠM DỪNG**.
- Gửi yêu cầu duyệt (Approve/Edit) cho người dùng (Admin).
- Sau khi người dùng phản hồi, Agent tiếp tục quy trình từ điểm dừng với trạng thái bộ nhớ (State) đã được cập nhật.

### 4. 📚 Advanced RAG (Retrieval-Augmented Generation)
- Hỗ trợ chat với tài liệu hướng dẫn sử dụng, chính sách bảo hành.
- Kỹ thuật **Metadata Filtering**: Kết hợp tìm kiếm vector với các nhãn (Sentiment, Topic) đã được phân loại trước đó.

---

## 🏗️ Kiến trúc hệ thống (System Architecture)

```mermaid
graph TD
    User[User Question] --> Supervisor[Supervisor Agent LLM]
    Supervisor -->|Routing| Sentiment[Sentiment Node]
    Supervisor -->|Routing| RAG[RAG Node]
    
    subgraph Sentiment Node
    ML[Traditional ML Filter] -->|High Confidence| Result
    ML -->|Low Confidence/Complex| LLM[Gemini Pro Analysis]
    end
    
    subgraph RAG Node
    Query --> VectorDB[(ChromaDB)]
    VectorDB --> Context
    Context --> LLM_RAG[Gemini Answer]
    end
    
    Sentiment --> Supervisor
    RAG --> Supervisor
    Supervisor --> Final[Final Response]