# Amazon Feedback AI Agent - React Frontend

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

Frontend sẽ chạy tại: **http://localhost:3000**

---

## 📦 Tech Stack

- **React 18** - UI library
- **Vite** - Build tool (siêu nhanh!)
- **Tailwind CSS** - Styling
- **Axios** - API calls
- **Recharts** - Charts & visualizations
- **React Markdown** - Render markdown từ AI
- **Lucide React** - Icons

---

## 🎨 Features

### ✅ Chat Interface
- ChatGPT-like UI mượt mà
- Markdown rendering cho AI responses
- Loading states & animations
- Auto-scroll to latest message

### ✅ File Upload
- Drag & drop CSV files
- Progress bar
- Upload status feedback

### ✅ Analytics Dashboard
- Sentiment distribution pie chart
- Stats cards (Total, Positive, Negative, Neutral)
- Real-time data từ backend

---

## 🔌 API Integration

Frontend gọi FastAPI backend tại `http://localhost:8000`:

- `POST /api/chat` - Send message
- `POST /api/upload` - Upload CSV
- `GET /api/sentiment` - Get sentiment stats
- `GET /api/analytics` - Get analytics data

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.jsx    # Chat UI
│   │   ├── Dashboard.jsx        # Analytics dashboard
│   │   └── FileUpload.jsx       # CSV upload
│   ├── services/
│   │   └── api.js               # API calls
│   ├── App.jsx                  # Main app
│   ├── main.jsx                 # Entry point
│   └── index.css                # Global styles
├── package.json
├── vite.config.js
└── tailwind.config.js
```

---

## 🎯 Next Steps

1. **Customize UI**: Edit Tailwind classes trong components
2. **Add features**: Thêm streaming responses, export data, etc.
3. **Deploy**: Build production với `npm run build`

---

## 🐛 Troubleshooting

**CORS errors?**
→ Check backend CORS settings trong `api.py`

**API not responding?**
→ Ensure backend đang chạy: `python api.py`

**Charts không hiện?**
→ Check console logs, verify API response format
