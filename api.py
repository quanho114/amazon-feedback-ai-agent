"""
FastAPI Backend for Amazon Feedback AI Agent
Exposes REST API endpoints for React frontend
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import os
from dotenv import load_dotenv

# Import existing logic
from src.agents.graph import app as agent_graph
from src.agents.tools import SESSION_DATA
from src.rag.vector_search import ingest_data
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

# Initialize FastAPI app
fastapi_app = FastAPI(
    title="Amazon Feedback AI API",
    description="Multi-agent AI system for customer feedback analysis",
    version="1.0.0"
)

# Configure CORS for React frontend
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
agent_app = agent_graph
conversation_history: List[Dict[str, str]] = []

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    node: str
    execution_time: float

class UploadResponse(BaseModel):
    success: bool
    message: str
    rows: int
    columns: List[str]

# --- API Endpoints ---

# Startup message removed - agent graph auto-compiles on import

@fastapi_app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Amazon Feedback AI Agent",
        "version": "1.0.0"
    }

def run_rag_background(df: pd.DataFrame, text_col: str):
    """Run RAG ingestion in background to avoid blocking upload"""
    try:
        print(f"[BACKGROUND] Starting RAG ingestion with column: {text_col}")
        ingest_data(df, text_column=text_col)
        print("[BACKGROUND] RAG ingestion completed!")
    except Exception as e:
        print(f"[BACKGROUND] RAG ingestion failed: {e}")


@fastapi_app.post("/api/upload", response_model=UploadResponse)
async def upload_csv(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload CSV file and process data
    Performs sentiment analysis and RAG ingestion
    """
    try:
        # Read CSV with safe options
        contents = await file.read()
        file_size_mb = len(contents) / (1024 * 1024)
        print(f"[INFO] File size: {file_size_mb:.2f} MB")
        
        # Try multiple strategies to read CSV
        df = None
        errors = []
        
        # Strategy 1: Standard UTF-8 with C engine (comma delimiter)
        try:
            print("[INFO] Trying Strategy 1: UTF-8 comma delimiter...")
            df = pd.read_csv(
                io.BytesIO(contents),
                encoding='utf-8',
                low_memory=False
            )
            # Validate: Should have multiple columns
            if len(df.columns) > 3:
                print(f"[OK] Strategy 1 succeeded! ({len(df.columns)} columns)")
            else:
                print(f"[WARNING] Strategy 1: Only {len(df.columns)} columns, trying other methods...")
                df = None
        except Exception as e1:
            errors.append(f"Strategy 1: {str(e1)[:100]}")
            print(f"[WARNING] Strategy 1 failed: {str(e1)[:100]}")
            
            # Strategy 2: TAB delimiter (TSV files)
            if df is None:
                try:
                    print("[INFO] Trying Strategy 2: TAB delimiter (TSV)...")
                    df = pd.read_csv(
                        io.BytesIO(contents),
                        encoding='utf-8',
                        sep='\t',
                        on_bad_lines='skip',
                        engine='python'
                    )
                    if len(df.columns) > 3:
                        print(f"[OK] Strategy 2 succeeded! ({len(df.columns)} columns)")
                    else:
                        df = None
                except Exception as e2:
                    errors.append(f"Strategy 2: {str(e2)[:100]}")
                    print(f"[WARNING] Strategy 2 failed: {str(e2)[:100]}")
            
            # Strategy 3: Auto-detect delimiter
            if df is None:
                try:
                    print("[INFO] Trying Strategy 3: Auto-detect delimiter...")
                    df = pd.read_csv(
                        io.BytesIO(contents),
                        encoding='utf-8',
                        sep=None,
                        engine='python',
                        on_bad_lines='skip'
                    )
                    if len(df.columns) > 3:
                        print(f"[OK] Strategy 3 succeeded! ({len(df.columns)} columns)")
                    else:
                        df = None
                except Exception as e3:
                    errors.append(f"Strategy 3: {str(e3)[:100]}")
                    print(f"[WARNING] Strategy 3 failed: {str(e3)[:100]}")
            
            # Strategy 4: Latin-1 encoding
            if df is None:
                try:
                    print("[INFO] Trying Strategy 4: Latin-1 encoding...")
                    df = pd.read_csv(
                        io.BytesIO(contents),
                        encoding='latin-1',
                        on_bad_lines='skip',
                        engine='python'
                    )
                    if len(df.columns) > 3:
                        print(f"[OK] Strategy 4 succeeded! ({len(df.columns)} columns)")
                    else:
                        df = None
                except Exception as e4:
                    errors.append(f"Strategy 4: {str(e4)[:100]}")
                    print(f"[WARNING] Strategy 4 failed: {str(e4)[:100]}")
            
            if df is None:
                print(f"[ERROR] All strategies failed!")
        
        if df is None:
            error_msg = "Failed to parse CSV file. Tried multiple strategies:\n" + "\n".join(errors)
            raise HTTPException(status_code=400, detail=error_msg)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        print(f"✅ CSV loaded: {len(df)} rows, {len(df.columns)} columns")
        print(f"Columns: {df.columns.tolist()}")
        
        # Auto-detect columns
        rating_col = next((col for col in df.columns if 'rating' in col.lower()), None)
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if not text_cols:
            raise HTTPException(status_code=400, detail="No text columns found in CSV")
        
        # Sentiment analysis - Try ML model first, fallback to rating/TextBlob
        print("Running sentiment analysis...")
        text_col = text_cols[0]
        
        try:
            # Try ML model (SVM - 90% accuracy)
            from src.analytics.sentiment_model import analyze_dataframe
            df = analyze_dataframe(df, text_col=text_col)
            print(f"[OK] Sentiment from SVM model (90% accuracy)")
        except FileNotFoundError:
            # Fallback: Use rating if available
            if rating_col:
                # Check if rating is numeric
                if df[rating_col].dtype in ['int64', 'float64']:
                    df['ai_sentiment'] = df[rating_col].apply(
                        lambda x: 'positive' if x >= 4 else ('negative' if x <= 2 else 'neutral')
                    )
                    print(f"[OK] Sentiment from numeric rating column: {rating_col}")
                else:
                    # Try to extract rating from text (e.g., "Rated 5 out of 5 stars")
                    import re
                    def extract_rating(text):
                        match = re.search(r'Rated (\d+) out of', str(text))
                        if match:
                            return int(match.group(1))
                        return None
                    
                    df['numeric_rating'] = df[rating_col].apply(extract_rating)
                    
                    if df['numeric_rating'].notna().sum() > 0:
                        df['ai_sentiment'] = df['numeric_rating'].apply(
                            lambda x: 'positive' if pd.notna(x) and x >= 4 
                            else ('negative' if pd.notna(x) and x <= 2 
                            else 'neutral')
                        )
                        # Debug: Show sentiment distribution
                        sentiment_counts = df['ai_sentiment'].value_counts()
                        print(f"[OK] Sentiment from parsed rating text: {rating_col}")
                        print(f"[DEBUG] Sentiment distribution: {sentiment_counts.to_dict()}")
                    else:
                        # Fallback to TextBlob if parsing fails
                        from textblob import TextBlob
                        df['ai_sentiment'] = df[text_col].apply(
                            lambda x: 'positive' if TextBlob(str(x)).sentiment.polarity > 0.1 
                            else ('negative' if TextBlob(str(x)).sentiment.polarity < -0.1 else 'neutral')
                        )
                        print(f"[OK] Sentiment from TextBlob on column: {text_col}")
            else:
                # Last fallback: TextBlob
                from textblob import TextBlob
                df['ai_sentiment'] = df[text_col].apply(
                    lambda x: 'positive' if TextBlob(str(x)).sentiment.polarity > 0.1 
                    else ('negative' if TextBlob(str(x)).sentiment.polarity < -0.1 else 'neutral')
                )
                print(f"[OK] Sentiment from TextBlob on column: {text_col}")
        
        # Store in session
        SESSION_DATA['default'] = df
        print("✅ Data stored in SESSION_DATA")
        
        # RAG ingestion - Smart column detection
        try:
            # Smart detect review text column (not username/id columns)
            text_col_for_rag = None
            
            # Priority 1: Look for exact matches first
            for col in df.columns:
                if col.lower() in ['review text', 'review_text', 'text', 'comment', 'review']:
                    text_col_for_rag = col
                    break
            
            # Priority 2: Look for partial matches
            if not text_col_for_rag:
                for col in df.columns:
                    col_lower = col.lower()
                    # Look for review/text/content/comment columns
                    if any(keyword in col_lower for keyword in ['review', 'text', 'content', 'comment', 'feedback', 'description']):
                        # Skip if it's a name/user column
                        if not any(skip in col_lower for skip in ['name', 'user', 'author', 'reviewer name']):
                            text_col_for_rag = col
                            break
            
            # Fallback: Use first object column that's not user/name/id
            if not text_col_for_rag:
                for col in text_cols:
                    col_lower = col.lower()
                    if not any(skip in col_lower for skip in ['user', 'name', 'id', 'author', 'email']):
                        text_col_for_rag = col
                        break
            
            # Last fallback: Use first object column (risky but better than crash)
            if not text_col_for_rag and text_cols:
                text_col_for_rag = text_cols[0]
            
            if text_col_for_rag:
                print(f"[INFO] Scheduling RAG ingestion in background: {text_col_for_rag}")
                # Run RAG in background to avoid blocking upload response
                background_tasks.add_task(run_rag_background, df.copy(), text_col_for_rag)
                print("[INFO] RAG will process in background")
            else:
                print("[WARNING] No suitable text column found for RAG ingestion")
        except Exception as rag_error:
            print(f"[WARNING] RAG scheduling failed: {str(rag_error)}")
        
        return UploadResponse(
            success=True,
            message=f"Successfully processed {len(df):,} reviews. RAG indexing in background...",
            rows=len(df),
            columns=df.columns.tolist()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Upload failed: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - Routes message through multi-agent system
    """
    import time
    start_time = time.time()
    
    try:
        # Add user message to history
        conversation_history.append({"role": "user", "content": request.message})
        
        # Build messages for agent
        messages = []
        for msg in conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Invoke agent
        inputs = {
            "messages": messages,
            "loop_step": 0,
            "data_info": {},
            "current_node": "",
            "analysis_data": {}
        }
        
        response_text = ""
        current_node = "CHAT"
        
        for event in agent_app.stream(inputs):
            for node_name, value in event.items():
                current_node = node_name
                if "messages" in value and value["messages"]:
                    last_msg = value["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        response_text = last_msg.content
        
        if not response_text:
            response_text = "Xin lỗi, tôi không thể tạo câu trả lời."
        
        # Add to history
        conversation_history.append({"role": "assistant", "content": response_text})
        
        execution_time = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            node=current_node,
            execution_time=round(execution_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@fastapi_app.get("/api/sentiment")
async def get_sentiment_stats():
    """
    Get sentiment distribution statistics
    """
    df = SESSION_DATA.get('default')
    
    if df is None:
        raise HTTPException(status_code=400, detail="No data uploaded")
    
    sentiment_counts = df['ai_sentiment'].value_counts().to_dict()
    total = len(df)
    
    return {
        "total_reviews": total,
        "distribution": {
            "positive": sentiment_counts.get('positive', 0),
            "negative": sentiment_counts.get('negative', 0),
            "neutral": sentiment_counts.get('neutral', 0)
        },
        "percentages": {
            "positive": round(sentiment_counts.get('positive', 0) / total * 100, 1),
            "negative": round(sentiment_counts.get('negative', 0) / total * 100, 1),
            "neutral": round(sentiment_counts.get('neutral', 0) / total * 100, 1)
        }
    }

@fastapi_app.get("/api/analytics")
async def get_analytics():
    """
    Get comprehensive analytics data for dashboard
    """
    df = SESSION_DATA.get('default')
    
    if df is None:
        raise HTTPException(status_code=400, detail="No data uploaded")
    
    # Basic stats
    stats = {
        "total_reviews": len(df),
        "columns": df.columns.tolist(),
        "sentiment_distribution": df['ai_sentiment'].value_counts().to_dict()
    }
    
    # Rating stats if available
    rating_col = next((col for col in df.columns if 'rating' in col.lower()), None)
    
    if rating_col:
        # Extract numeric ratings if text format
        import re
        def extract_rating(text):
            match = re.search(r'Rated (\d+) out of', str(text))
            if match:
                return int(match.group(1))
            # Try direct conversion
            try:
                return int(float(text))
            except:
                return None
        
        df['numeric_rating'] = df[rating_col].apply(extract_rating)
        valid_ratings = df[df['numeric_rating'].notna()]
        
        if len(valid_ratings) > 0:
            stats["rating_stats"] = {
                "mean": round(valid_ratings['numeric_rating'].mean(), 2),
                "median": float(valid_ratings['numeric_rating'].median()),
                "min": int(valid_ratings['numeric_rating'].min()),
                "max": int(valid_ratings['numeric_rating'].max())
            }
            
            # Rating distribution
            rating_dist = valid_ratings['numeric_rating'].value_counts().to_dict()
            stats["rating_distribution"] = {str(k): int(v) for k, v in rating_dist.items()}
            
            # Sentiment by rating
            sentiment_by_rating = {}
            for rating in sorted(valid_ratings['numeric_rating'].unique()):
                rating_df = valid_ratings[valid_ratings['numeric_rating'] == rating]
                sentiment_counts = rating_df['ai_sentiment'].value_counts().to_dict()
                sentiment_by_rating[str(int(rating))] = {
                    'positive': sentiment_counts.get('positive', 0),
                    'negative': sentiment_counts.get('negative', 0),
                    'neutral': sentiment_counts.get('neutral', 0)
                }
            stats["sentiment_by_rating"] = sentiment_by_rating
    
    # Date-based trends if date column exists
    date_col = next((col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()), None)
    if date_col:
        try:
            df['parsed_date'] = pd.to_datetime(df[date_col], errors='coerce')
            valid_dates = df[df['parsed_date'].notna()]
            
            if len(valid_dates) > 0:
                # Group by month
                valid_dates['month'] = valid_dates['parsed_date'].dt.to_period('M')
                monthly_counts = valid_dates.groupby('month').size().to_dict()
                stats["monthly_trends"] = {str(k): int(v) for k, v in monthly_counts.items()}
        except:
            pass
    
    return stats

@fastapi_app.delete("/api/conversation")
async def clear_conversation():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return {"message": "Conversation history cleared"}

@fastapi_app.delete("/api/reset")
async def reset_data():
    """Reset all data - clear uploaded data, conversation, and RAG index"""
    global conversation_history
    
    try:
        # Clear session data
        SESSION_DATA.clear()
        
        # Clear conversation history
        conversation_history = []
        
        # Clear RAG vector store
        try:
            from src.rag.vector_search import clear_vector_store
            clear_vector_store()
            print("[INFO] Vector store cleared")
        except Exception as e:
            print(f"[WARNING] Failed to clear vector store: {e}")
        
        return {
            "success": True,
            "message": "All data reset successfully. You can upload a new file."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@fastapi_app.get("/api/health")
async def health_check():
    """Detailed health check"""
    df = SESSION_DATA.get('default')
    return {
        "status": "healthy",
        "agent_loaded": agent_app is not None,
        "data_loaded": df is not None,
        "conversation_length": len(conversation_history),
        "total_rows": len(df) if df is not None else 0
    }

@fastapi_app.get("/api/data-status")
async def data_status():
    """Check if data is loaded in session"""
    df = SESSION_DATA.get('default')
    if df is None:
        return {
            "loaded": False,
            "message": "No data uploaded yet"
        }
    
    return {
        "loaded": True,
        "rows": len(df),
        "columns": df.columns.tolist(),
        "has_sentiment": 'ai_sentiment' in df.columns
    }

# Expose app for uvicorn
app = fastapi_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)  # Disable reload for debugging
