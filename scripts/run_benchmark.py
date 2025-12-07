"""
Quick script to run sentiment benchmark
Usage: python scripts/run_benchmark.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analytics.sentiment_benchmark import run_sentiment_benchmark
import pandas as pd

if __name__ == "__main__":
    # Load data
    csv_path = "data/raw/Amazon_Reviews.csv"
    
    print("Starting Sentiment Analysis Benchmark...")
    print(f"Loading: {csv_path}\n")
    
    # Run benchmark
    benchmark = run_sentiment_benchmark(csv_path=csv_path)
    
    # Get best model
    best = benchmark.get_best_model()
    
    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    
    if best['type'] in ['logistic', 'svm']:
        print(f"Use {best['type'].upper()} for production")
        print(f"   - Model and vectorizer are trained and ready")
        print(f"   - Can be saved with pickle/joblib")
        print(f"   - Fast inference: ~{benchmark.results[best['type']]['speed_per_review_ms']:.2f}ms per review")
    elif best['type'] == 'vader':
        print("Use VADER for production")
        print("   - No training needed")
        print("   - Ultra-fast: instant inference")
        print("   - Good for real-time applications")
    elif best['type'] == 'roberta':
        print("Use RoBERTa for production")
        print("   - Highest accuracy")
        print("   - Slower inference (~100-500ms per review)")
        print("   - Best for batch processing")
    
    print("\nNext steps:")
    print("1. Integrate best model into sentiment_node.py")
    print("2. Replace TextBlob with chosen model")
    print("3. Save trained model (if ML-based)")
    print("4. Update API to use new model")
