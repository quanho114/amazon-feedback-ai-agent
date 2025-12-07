"""
Production Sentiment Model
Uses trained Linear SVM with TF-IDF (Winner from benchmark)
Accuracy: 90.10%, F1: 0.8877, Speed: ~3.5ms/review
"""
import os
import re
import pickle
from typing import List, Dict, Optional
import pandas as pd

# Paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'sentiment_svm.pkl')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'sentiment_vectorizer.pkl')

# Global cache
_model = None
_vectorizer = None


def preprocess_text(text: str) -> str:
    """Preprocess text for ML model"""
    if not isinstance(text, str):
        return ""
    
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML
    text = re.sub(r'http\S+|www\S+', '', text)  # Remove URLs
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)  # Keep only letters
    text = ' '.join(text.split())  # Normalize whitespace
    
    return text


def load_model():
    """Load trained model and vectorizer"""
    global _model, _vectorizer
    
    if _model is not None and _vectorizer is not None:
        return _model, _vectorizer
    
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECTORIZER_PATH):
        raise FileNotFoundError(
            f"Model not found. Run benchmark first to train: python scripts/run_benchmark.py"
        )
    
    with open(MODEL_PATH, 'rb') as f:
        _model = pickle.load(f)
    
    with open(VECTORIZER_PATH, 'rb') as f:
        _vectorizer = pickle.load(f)
    
    print("[INFO] Sentiment model loaded (SVM + TF-IDF)")
    return _model, _vectorizer


def predict_sentiment(text: str) -> str:
    """
    Predict sentiment for a single text
    
    Args:
        text: Review text
        
    Returns:
        str: 'positive', 'negative', or 'neutral'
    """
    model, vectorizer = load_model()
    
    processed = preprocess_text(text)
    vec = vectorizer.transform([processed])
    prediction = model.predict(vec)[0]
    
    return prediction


def predict_batch(texts: List[str]) -> List[str]:
    """
    Predict sentiment for multiple texts (faster)
    
    Args:
        texts: List of review texts
        
    Returns:
        List of sentiment labels
    """
    model, vectorizer = load_model()
    
    processed = [preprocess_text(t) for t in texts]
    vec = vectorizer.transform(processed)
    predictions = model.predict(vec)
    
    return predictions.tolist()


def analyze_dataframe(df: pd.DataFrame, text_col: str = 'Review Text') -> pd.DataFrame:
    """
    Add sentiment column to DataFrame
    
    Args:
        df: DataFrame with text column
        text_col: Name of text column
        
    Returns:
        DataFrame with 'ai_sentiment' column added
    """
    texts = df[text_col].fillna('').astype(str).tolist()
    sentiments = predict_batch(texts)
    df['ai_sentiment'] = sentiments
    
    return df


def get_sentiment_stats(df: pd.DataFrame) -> Dict:
    """Get sentiment distribution statistics"""
    if 'ai_sentiment' not in df.columns:
        return {}
    
    counts = df['ai_sentiment'].value_counts()
    total = len(df)
    
    return {
        'total': total,
        'positive': int(counts.get('positive', 0)),
        'negative': int(counts.get('negative', 0)),
        'neutral': int(counts.get('neutral', 0)),
        'positive_pct': round(counts.get('positive', 0) / total * 100, 1),
        'negative_pct': round(counts.get('negative', 0) / total * 100, 1),
        'neutral_pct': round(counts.get('neutral', 0) / total * 100, 1)
    }


# Quick test
if __name__ == "__main__":
    # Test predictions
    test_texts = [
        "This product is amazing! Best purchase ever!",
        "Terrible quality, broke after one day. Waste of money.",
        "It's okay, nothing special but works fine.",
        "I love it! Highly recommend to everyone!",
        "Worst customer service, never buying again."
    ]
    
    print("Testing sentiment predictions:")
    print("-" * 50)
    
    for text in test_texts:
        sentiment = predict_sentiment(text)
        print(f"[{sentiment.upper():8}] {text[:50]}...")
