"""
Statistics Module - Accurate Statistical Calculations
Data Analyst (DA) Territory

CRITICAL: All calculations must use Python code, NOT LLM estimation
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_stats(df: pd.DataFrame, rating_col: str = None) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for review data
    
    Args:
        df: DataFrame containing review data
        rating_col: Name of rating column (auto-detect if None)
        
    Returns:
        dict: Dictionary of statistical metrics
    """
    stats = {}
    
    # Auto-detect rating column
    if rating_col is None:
        rating_col = next(
            (col for col in df.columns if col in ['rating', 'star', 'stars', 'score']),
            None
        )
    
    # Basic counts
    stats['total_reviews'] = len(df)
    stats['unique_values'] = df.nunique().to_dict()
    
    # Rating statistics
    if rating_col and rating_col in df.columns:
        stats['rating_mean'] = float(df[rating_col].mean())
        stats['rating_median'] = float(df[rating_col].median())
        stats['rating_std'] = float(df[rating_col].std())
        stats['rating_min'] = float(df[rating_col].min())
        stats['rating_max'] = float(df[rating_col].max())
        stats['rating_mode'] = float(df[rating_col].mode()[0]) if not df[rating_col].mode().empty else None
    
    # Sentiment statistics
    if 'ai_sentiment' in df.columns:
        sentiment_stats = get_sentiment_distribution(df)
        stats.update(sentiment_stats)
    
    # Percentiles
    if rating_col and rating_col in df.columns:
        stats['rating_percentiles'] = {
            '25th': float(df[rating_col].quantile(0.25)),
            '50th': float(df[rating_col].quantile(0.50)),
            '75th': float(df[rating_col].quantile(0.75)),
            '90th': float(df[rating_col].quantile(0.90))
        }
    
    return stats


def get_sentiment_distribution(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate sentiment distribution metrics
    
    Args:
        df: DataFrame with 'ai_sentiment' column
        
    Returns:
        dict: Sentiment statistics
    """
    if 'ai_sentiment' not in df.columns:
        return {}
    
    sentiment_counts = df['ai_sentiment'].value_counts()
    sentiment_pct = df['ai_sentiment'].value_counts(normalize=True) * 100
    
    return {
        'sentiment_counts': sentiment_counts.to_dict(),
        'sentiment_percentages': {
            k: round(v, 2) for k, v in sentiment_pct.to_dict().items()
        },
        'positive_count': int(sentiment_counts.get('positive', 0)),
        'negative_count': int(sentiment_counts.get('negative', 0)),
        'neutral_count': int(sentiment_counts.get('neutral', 0)),
        'positive_pct': round(sentiment_pct.get('positive', 0), 2),
        'negative_pct': round(sentiment_pct.get('negative', 0), 2),
        'neutral_pct': round(sentiment_pct.get('neutral', 0), 2)
    }


def calculate_correlation(df: pd.DataFrame, col1: str, col2: str) -> float:
    """
    Calculate correlation between two numeric columns
    
    Args:
        df: DataFrame
        col1: First column name
        col2: Second column name
        
    Returns:
        float: Correlation coefficient
    """
    if col1 not in df.columns or col2 not in df.columns:
        return None
    
    # Filter numeric values
    df_filtered = df[[col1, col2]].select_dtypes(include=[np.number])
    
    if df_filtered.empty:
        return None
    
    corr = df_filtered[col1].corr(df_filtered[col2])
    
    return float(corr)


def get_top_keywords(df: pd.DataFrame, text_col: str = None, top_n: int = 10) -> list:
    """
    Extract top N keywords from review text
    
    Args:
        df: DataFrame
        text_col: Name of text column (auto-detect if None)
        top_n: Number of top keywords to return
        
    Returns:
        list: List of (keyword, count) tuples
    """
    if text_col is None:
        text_col = next(
            (col for col in df.columns if 'review' in col.lower() or 'text' in col.lower()),
            None
        )
    
    if text_col is None:
        return []
    
    # Combine all text
    all_text = ' '.join(df[text_col].astype(str).str.lower().tolist())
    
    # Simple word frequency count (can be enhanced with NLP)
    words = all_text.split()
    
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'it', 'this', 'that'}
    words = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Count frequencies
    word_freq = pd.Series(words).value_counts().head(top_n)
    
    return list(word_freq.items())


def calculate_rating_by_sentiment(df: pd.DataFrame, rating_col: str = None) -> Dict[str, float]:
    """
    Calculate average rating for each sentiment category
    
    Args:
        df: DataFrame
        rating_col: Name of rating column
        
    Returns:
        dict: Average ratings by sentiment
    """
    if 'ai_sentiment' not in df.columns:
        return {}
    
    if rating_col is None:
        rating_col = next(
            (col for col in df.columns if col in ['rating', 'star', 'stars', 'score']),
            None
        )
    
    if rating_col is None or rating_col not in df.columns:
        return {}
    
    avg_ratings = df.groupby('ai_sentiment')[rating_col].mean()
    
    return {k: round(v, 2) for k, v in avg_ratings.to_dict().items()}
