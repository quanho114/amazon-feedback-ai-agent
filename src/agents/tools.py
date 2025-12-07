"""
Tools and utilities for data processing
Handles DataFrame registration and sentiment analysis

NOTE: This module provides FALLBACK sentiment analysis only.
The primary sentiment analysis uses SVM model (90% accuracy) in api.py.
These functions are only used if SVM model is not available.
"""
import pandas as pd
from textblob import TextBlob

# Global data storage - Shared across all nodes
SESSION_DATA = {}


def analyze_sentiment_from_rating(score):
    """
    Convert rating score to sentiment label
    
    Args:
        score: Rating value (1-5)
        
    Returns:
        str: Sentiment label (positive/negative/neutral)
    """
    try:
        score = float(score)
        if score >= 4:
            return "positive"
        elif score <= 2:
            return "negative"
        else:
            return "neutral"
    except:
        return "neutral"


def analyze_sentiment_from_text(text):
    """
    Analyze sentiment from text using TextBlob (fallback)
    
    Args:
        text: Review text
        
    Returns:
        str: Sentiment label
    """
    if not isinstance(text, str):
        return "neutral"
    
    score = TextBlob(text).sentiment.polarity
    
    if score > 0.1:
        return "positive"
    elif score < -0.1:
        return "negative"
    else:
        return "neutral"


def process_data(df: pd.DataFrame):
    """
    Process DataFrame: add sentiment labels (FALLBACK ONLY)
    
    NOTE: This is a fallback method. The primary sentiment analysis
    should use SVM model (90% accuracy) in api.py during upload.
    
    Priority:
    1. Rating-based (fast, ~80% accuracy)
    2. TextBlob (slow, ~70% accuracy)
    3. Default to 'neutral'
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: Processed DataFrame with 'ai_sentiment' column
    """
    print("⏳ Processing data...")
    
    # Find rating column
    rating_col = next(
        (col for col in df.columns if col.lower() in ['rating', 'star', 'stars', 'score']),
        None
    )
    
    # Find text column
    text_col = next(
        (col for col in df.columns if 'review' in col.lower() or 'text' in col.lower()),
        None
    )
    
    # Add sentiment based on rating (fast) or text (slower)
    if rating_col:
        print(f"[INFO] Using {rating_col} column for sentiment (Fast, ~80% accuracy)")
        df['ai_sentiment'] = df[rating_col].apply(analyze_sentiment_from_rating)
    elif text_col:
        print("[WARNING] Using TextBlob for sentiment analysis (Slow, ~70% accuracy)")
        df['ai_sentiment'] = df[text_col].apply(analyze_sentiment_from_text)
    else:
        print("[WARNING] No rating or text column found, defaulting to 'neutral'")
        df['ai_sentiment'] = 'neutral'
    
    print("[INFO] Sentiment analysis completed!")
    
    return df


def register_dataframe(df: pd.DataFrame, session_id: str = 'default'):
    """
    Register DataFrame in session storage and process it
    
    Args:
        df: DataFrame to register
        session_id: Session identifier
        
    Returns:
        pd.DataFrame: Processed DataFrame
    """
    # Normalize column names
    df.columns = [c.lower().replace(" ", "_").strip() for c in df.columns]
    
    # Process data (add sentiment)
    processed_df = process_data(df)
    
    # Store in session
    SESSION_DATA[session_id] = processed_df
    
    # Also ingest into vector database for RAG
    from src.rag.vector_search import ingest_data
    ingest_data(processed_df, session_id=session_id)
    
    return processed_df
