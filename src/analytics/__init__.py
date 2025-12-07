"""
Analytics module initialization
"""
from .stats import calculate_stats, get_sentiment_distribution
from .forecasting import forecast_ratings, detect_anomalies

__all__ = [
    'calculate_stats',
    'get_sentiment_distribution',
    'forecast_ratings',
    'detect_anomalies'
]
