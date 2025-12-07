"""
Save the best model from benchmark for production use
Run after: python scripts/run_benchmark.py
"""
import sys
import os
import pickle

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analytics.sentiment_benchmark import run_sentiment_benchmark

# Create models directory
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

if __name__ == "__main__":
    csv_path = "data/raw/Amazon_Reviews.csv"
    
    print("Training and saving best sentiment model...")
    print("=" * 60)
    
    # Run benchmark
    benchmark = run_sentiment_benchmark(csv_path=csv_path)
    
    # Get best model
    best = benchmark.get_best_model()
    
    if best['type'] in ['logistic', 'svm', 'lightgbm']:
        # Save model
        model_path = os.path.join(MODEL_DIR, 'sentiment_svm.pkl')
        vectorizer_path = os.path.join(MODEL_DIR, 'sentiment_vectorizer.pkl')
        
        with open(model_path, 'wb') as f:
            pickle.dump(best['model'], f)
        
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(best['vectorizer'], f)
        
        print("\n" + "=" * 60)
        print("MODEL SAVED SUCCESSFULLY")
        print("=" * 60)
        print(f"Model type: {best['type'].upper()}")
        print(f"Accuracy: {best['accuracy']:.2%}")
        print(f"F1 Score: {best['f1_score']:.4f}")
        print(f"Model path: {model_path}")
        print(f"Vectorizer path: {vectorizer_path}")
        
    else:
        print(f"\nBest model is {best['type']} - no model file to save")
        print("VADER is rule-based, RoBERTa requires transformers library")
