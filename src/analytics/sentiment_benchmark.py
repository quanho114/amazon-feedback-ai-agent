"""
Sentiment Analysis Benchmark Suite (v2.0)
Compare: Logistic Regression, SVM, RoBERTa, VADER, LightGBM
Optimized with: Batch processing, N-grams, proper preprocessing, fair evaluation
"""
import pandas as pd
import numpy as np
import time
import re
import pickle
import os
from typing import Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# VADER
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    print("[WARNING] VADER not installed. Run: pip install vaderSentiment")

# LightGBM
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("[WARNING] LightGBM not installed. Run: pip install lightgbm")

# RoBERTa
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    ROBERTA_AVAILABLE = True
except ImportError:
    ROBERTA_AVAILABLE = False
    print("[WARNING] Transformers not installed. Run: pip install transformers torch")


class TextPreprocessor:
    """Separate preprocessing strategies for ML vs DL models"""
    
    @staticmethod
    def preprocess_for_ml(text: str) -> str:
        """
        Heavy preprocessing for ML models (SVM, Logistic, LightGBM)
        - Lowercase, remove punctuation, clean HTML
        """
        if not isinstance(text, str):
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def preprocess_for_dl(text: str) -> str:
        """
        Light preprocessing for Deep Learning models (RoBERTa)
        - Keep punctuation, case (they carry meaning)
        """
        if not isinstance(text, str):
            return ""
        
        # Only remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text


class SentimentBenchmark:
    """
    Production-ready benchmark suite for sentiment analysis models
    """
    
    def __init__(
        self, 
        df: pd.DataFrame, 
        text_col: str = 'Review Text', 
        rating_col: str = 'Rating',
        test_size: float = 0.2,
        holdout_size: int = 1000,
        cache_dir: str = 'models/cache'
    ):
        self.text_col = text_col
        self.rating_col = rating_col
        self.cache_dir = cache_dir
        self.preprocessor = TextPreprocessor()
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Clean and prepare data
        df = df.copy()
        df[text_col] = df[text_col].fillna('').astype(str)
        df = df[df[text_col].str.strip() != '']
        df['true_sentiment'] = df[rating_col].apply(self._rating_to_sentiment)
        
        # Create preprocessed columns
        df['text_ml'] = df[text_col].apply(self.preprocessor.preprocess_for_ml)
        df['text_dl'] = df[text_col].apply(self.preprocessor.preprocess_for_dl)
        
        # Split: Train/Val and Holdout Test (fixed for fair comparison)
        self.df_train, self.df_holdout = train_test_split(
            df, 
            test_size=min(holdout_size, int(len(df) * 0.15)),
            random_state=42,
            stratify=df['true_sentiment']
        )
        
        print(f"[INFO] Total samples: {len(df)}")
        print(f"[INFO] Training set: {len(self.df_train)}")
        print(f"[INFO] Holdout test set: {len(self.df_holdout)} (fixed for fair comparison)")
        print(f"[INFO] Distribution: {df['true_sentiment'].value_counts().to_dict()}")
        
        self.results = {}
        self.confusion_matrices = {}
    
    def _rating_to_sentiment(self, rating) -> str:
        """Convert rating to sentiment label"""
        try:
            if isinstance(rating, str):
                match = re.search(r'(\d+)', rating)
                if match:
                    rating = int(match.group(1))
                else:
                    return 'neutral'
            
            rating = float(rating)
            if rating >= 4:
                return 'positive'
            elif rating <= 2:
                return 'negative'
            else:
                return 'neutral'
        except:
            return 'neutral'
    
    def _save_cache(self, name: str, obj):
        """Save object to cache"""
        path = os.path.join(self.cache_dir, f"{name}.pkl")
        with open(path, 'wb') as f:
            pickle.dump(obj, f)
    
    def _load_cache(self, name: str):
        """Load object from cache"""
        path = os.path.join(self.cache_dir, f"{name}.pkl")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def benchmark_vader(self) -> Dict:
        """Benchmark VADER sentiment analyzer"""
        if not VADER_AVAILABLE:
            return {"error": "VADER not available"}
        
        print("\n[BENCHMARK] Running VADER...")
        analyzer = SentimentIntensityAnalyzer()
        
        start_time = time.time()
        predictions = []
        
        # Run on holdout set for fair comparison
        for text in self.df_holdout[self.text_col]:
            scores = analyzer.polarity_scores(str(text))
            compound = scores['compound']
            
            if compound >= 0.05:
                predictions.append('positive')
            elif compound <= -0.05:
                predictions.append('negative')
            else:
                predictions.append('neutral')
        
        elapsed = time.time() - start_time
        
        y_true = self.df_holdout['true_sentiment'].tolist()
        accuracy = accuracy_score(y_true, predictions)
        f1 = f1_score(y_true, predictions, average='weighted')
        
        # Confusion matrix
        cm = confusion_matrix(y_true, predictions, labels=['positive', 'neutral', 'negative'])
        self.confusion_matrices['vader'] = cm
        
        result = {
            "model": "VADER",
            "accuracy": round(accuracy, 4),
            "f1_score": round(f1, 4),
            "time_seconds": round(elapsed, 2),
            "speed_per_review_ms": round(elapsed / len(self.df_holdout) * 1000, 3),
            "test_samples": len(self.df_holdout)
        }
        
        self.results['vader'] = result
        print(f"[RESULT] VADER: Accuracy={accuracy:.2%}, F1={f1:.4f}, Time={elapsed:.2f}s")
        
        return result

    def benchmark_logistic(self, max_features: int = 10000, ngram_range: Tuple = (1, 2)) -> Dict:
        """
        Benchmark Logistic Regression with TF-IDF
        Optimized with N-grams for better context capture
        """
        print(f"\n[BENCHMARK] Running Logistic Regression (ngrams={ngram_range})...")
        
        # Use preprocessed ML text
        X_train = self.df_train['text_ml']
        y_train = self.df_train['true_sentiment']
        X_test = self.df_holdout['text_ml']
        y_test = self.df_holdout['true_sentiment']
        
        # TF-IDF with N-grams
        vectorizer = TfidfVectorizer(
            max_features=max_features, 
            stop_words='english',
            ngram_range=ngram_range,  # Capture "not good" vs "good"
            min_df=2,
            max_df=0.95
        )
        
        start_time = time.time()
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)
        
        # Train model
        model = LogisticRegression(
            max_iter=1000, 
            random_state=42,
            C=1.0,
            solver='lbfgs',
            multi_class='multinomial'
        )
        model.fit(X_train_vec, y_train)
        
        # Predict on holdout
        predictions = model.predict(X_test_vec)
        elapsed = time.time() - start_time
        
        accuracy = accuracy_score(y_test, predictions)
        f1 = f1_score(y_test, predictions, average='weighted')
        
        # Confusion matrix
        cm = confusion_matrix(y_test, predictions, labels=['positive', 'neutral', 'negative'])
        self.confusion_matrices['logistic'] = cm
        
        # Cache for reuse
        self._save_cache('logistic_model', model)
        self._save_cache('logistic_vectorizer', vectorizer)
        
        result = {
            "model": "Logistic Regression",
            "accuracy": round(accuracy, 4),
            "f1_score": round(f1, 4),
            "time_seconds": round(elapsed, 2),
            "speed_per_review_ms": round(elapsed / len(X_test) * 1000, 3),
            "test_samples": len(X_test),
            "vectorizer": vectorizer,
            "trained_model": model,
            "ngram_range": ngram_range
        }
        
        self.results['logistic'] = result
        print(f"[RESULT] Logistic: Accuracy={accuracy:.2%}, F1={f1:.4f}, Time={elapsed:.2f}s")
        
        return result
    
    def benchmark_svm(self, max_features: int = 10000, ngram_range: Tuple = (1, 2)) -> Dict:
        """
        Benchmark Linear SVM with TF-IDF
        Optimized with N-grams
        """
        print(f"\n[BENCHMARK] Running Linear SVM (ngrams={ngram_range})...")
        
        X_train = self.df_train['text_ml']
        y_train = self.df_train['true_sentiment']
        X_test = self.df_holdout['text_ml']
        y_test = self.df_holdout['true_sentiment']
        
        vectorizer = TfidfVectorizer(
            max_features=max_features, 
            stop_words='english',
            ngram_range=ngram_range,
            min_df=2,
            max_df=0.95
        )
        
        start_time = time.time()
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)
        
        model = LinearSVC(
            max_iter=2000, 
            random_state=42,
            C=1.0,
            dual=True
        )
        model.fit(X_train_vec, y_train)
        
        predictions = model.predict(X_test_vec)
        elapsed = time.time() - start_time
        
        accuracy = accuracy_score(y_test, predictions)
        f1 = f1_score(y_test, predictions, average='weighted')
        
        cm = confusion_matrix(y_test, predictions, labels=['positive', 'neutral', 'negative'])
        self.confusion_matrices['svm'] = cm
        
        self._save_cache('svm_model', model)
        self._save_cache('svm_vectorizer', vectorizer)
        
        result = {
            "model": "Linear SVM",
            "accuracy": round(accuracy, 4),
            "f1_score": round(f1, 4),
            "time_seconds": round(elapsed, 2),
            "speed_per_review_ms": round(elapsed / len(X_test) * 1000, 3),
            "test_samples": len(X_test),
            "vectorizer": vectorizer,
            "trained_model": model,
            "ngram_range": ngram_range
        }
        
        self.results['svm'] = result
        print(f"[RESULT] SVM: Accuracy={accuracy:.2%}, F1={f1:.4f}, Time={elapsed:.2f}s")
        
        return result
    
    def benchmark_lightgbm(self, max_features: int = 10000, ngram_range: Tuple = (1, 2)) -> Dict:
        """Benchmark LightGBM with TF-IDF"""
        if not LIGHTGBM_AVAILABLE:
            return {"error": "LightGBM not available"}
        
        print(f"\n[BENCHMARK] Running LightGBM (ngrams={ngram_range})...")
        
        X_train = self.df_train['text_ml']
        y_train = self.df_train['true_sentiment']
        X_test = self.df_holdout['text_ml']
        y_test = self.df_holdout['true_sentiment']
        
        # Encode labels
        label_map = {'negative': 0, 'neutral': 1, 'positive': 2}
        y_train_enc = y_train.map(label_map)
        y_test_enc = y_test.map(label_map)
        
        vectorizer = TfidfVectorizer(
            max_features=max_features, 
            stop_words='english',
            ngram_range=ngram_range,
            min_df=2,
            max_df=0.95
        )
        
        start_time = time.time()
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)
        
        model = lgb.LGBMClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=10,
            num_leaves=31,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        model.fit(X_train_vec, y_train_enc)
        
        predictions_enc = model.predict(X_test_vec)
        elapsed = time.time() - start_time
        
        # Decode predictions
        reverse_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
        predictions = [reverse_map[p] for p in predictions_enc]
        
        accuracy = accuracy_score(y_test, predictions)
        f1 = f1_score(y_test, predictions, average='weighted')
        
        cm = confusion_matrix(y_test, predictions, labels=['positive', 'neutral', 'negative'])
        self.confusion_matrices['lightgbm'] = cm
        
        self._save_cache('lightgbm_model', model)
        self._save_cache('lightgbm_vectorizer', vectorizer)
        
        result = {
            "model": "LightGBM",
            "accuracy": round(accuracy, 4),
            "f1_score": round(f1, 4),
            "time_seconds": round(elapsed, 2),
            "speed_per_review_ms": round(elapsed / len(X_test) * 1000, 3),
            "test_samples": len(X_test),
            "vectorizer": vectorizer,
            "trained_model": model,
            "label_map": label_map
        }
        
        self.results['lightgbm'] = result
        print(f"[RESULT] LightGBM: Accuracy={accuracy:.2%}, F1={f1:.4f}, Time={elapsed:.2f}s")
        
        return result

    def benchmark_roberta(self, batch_size: int = 16, use_distil: bool = False) -> Dict:
        """
        Benchmark RoBERTa with BATCH PROCESSING for speed
        Option to use DistilRoBERTa for faster inference
        """
        if not ROBERTA_AVAILABLE:
            return {"error": "RoBERTa not available"}
        
        model_name = "distilroberta-base" if use_distil else "cardiffnlp/twitter-roberta-base-sentiment"
        print(f"\n[BENCHMARK] Running {'DistilRoBERTa' if use_distil else 'RoBERTa'} (batch_size={batch_size})...")
        
        # Use DL-preprocessed text on holdout set
        texts = self.df_holdout['text_dl'].tolist()
        y_test = self.df_holdout['true_sentiment'].tolist()
        
        # Load model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.to(device)
        model.eval()
        
        label_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
        
        start_time = time.time()
        predictions = []
        
        # BATCH PROCESSING - much faster than single inference
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            inputs = tokenizer(
                batch_texts, 
                return_tensors="pt", 
                truncation=True, 
                max_length=256,
                padding=True
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model(**inputs)
                preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
                predictions.extend([label_map[p] for p in preds])
        
        elapsed = time.time() - start_time
        
        accuracy = accuracy_score(y_test, predictions)
        f1 = f1_score(y_test, predictions, average='weighted')
        
        cm = confusion_matrix(y_test, predictions, labels=['positive', 'neutral', 'negative'])
        self.confusion_matrices['roberta'] = cm
        
        result = {
            "model": "DistilRoBERTa" if use_distil else "RoBERTa",
            "accuracy": round(accuracy, 4),
            "f1_score": round(f1, 4),
            "time_seconds": round(elapsed, 2),
            "speed_per_review_ms": round(elapsed / len(texts) * 1000, 3),
            "test_samples": len(texts),
            "batch_size": batch_size,
            "device": str(device)
        }
        
        self.results['roberta'] = result
        print(f"[RESULT] {'DistilRoBERTa' if use_distil else 'RoBERTa'}: Accuracy={accuracy:.2%}, F1={f1:.4f}, Time={elapsed:.2f}s")
        
        return result
    
    def run_all_benchmarks(
        self, 
        weight_accuracy: float = 0.5,
        weight_f1: float = 0.3,
        weight_speed: float = 0.2
    ) -> pd.DataFrame:
        """
        Run all benchmarks and return comparison table
        
        Args:
            weight_accuracy: Weight for accuracy in final score (default 0.5)
            weight_f1: Weight for F1 in final score (default 0.3)
            weight_speed: Weight for speed in final score (default 0.2)
        """
        self.weights = {
            'accuracy': weight_accuracy,
            'f1': weight_f1,
            'speed': weight_speed
        }
        
        print("=" * 70)
        print("SENTIMENT ANALYSIS BENCHMARK SUITE v2.0")
        print("=" * 70)
        print(f"Scoring weights: Accuracy={weight_accuracy}, F1={weight_f1}, Speed={weight_speed}")
        
        # Run all benchmarks
        self.benchmark_vader()
        self.benchmark_logistic()
        self.benchmark_svm()
        self.benchmark_lightgbm()
        self.benchmark_roberta()
        
        # Create comparison table
        comparison = []
        for name, result in self.results.items():
            if 'error' not in result:
                comparison.append({
                    'Model': result['model'],
                    'Accuracy': f"{result['accuracy']:.2%}",
                    'F1 Score': f"{result['f1_score']:.4f}",
                    'Time (s)': result['time_seconds'],
                    'Speed (ms)': result['speed_per_review_ms'],
                    'Samples': result['test_samples']
                })
        
        df_comparison = pd.DataFrame(comparison)
        
        print("\n" + "=" * 70)
        print("BENCHMARK RESULTS (All models tested on same holdout set)")
        print("=" * 70)
        print(df_comparison.to_string(index=False))
        
        # Print confusion matrices
        self._print_confusion_matrices()
        
        # Pick winner
        best_model = self._pick_best_model()
        print("\n" + "=" * 70)
        print(f"WINNER: {best_model}")
        print("=" * 70)
        
        return df_comparison
    
    def _print_confusion_matrices(self):
        """Print confusion matrices for error analysis"""
        print("\n" + "-" * 70)
        print("CONFUSION MATRICES (rows=actual, cols=predicted)")
        print("Labels: [positive, neutral, negative]")
        print("-" * 70)
        
        for name, cm in self.confusion_matrices.items():
            print(f"\n{name.upper()}:")
            print(cm)
    
    def _pick_best_model(self) -> str:
        """Pick best model based on configurable weighted score"""
        scores = {}
        
        for name, result in self.results.items():
            if 'error' in result:
                continue
            
            acc = result['accuracy']
            f1_val = result['f1_score']
            speed_ms = result['speed_per_review_ms']
            
            # Normalize speed (lower is better, cap at 100ms)
            speed_score = 1 / (1 + speed_ms / 10)
            
            total_score = (
                self.weights['accuracy'] * acc + 
                self.weights['f1'] * f1_val + 
                self.weights['speed'] * speed_score
            )
            
            scores[result['model']] = round(total_score, 4)
        
        print(f"\n[SCORES] Weighted scores: {scores}")
        best_model = max(scores, key=scores.get)
        return best_model
    
    def get_best_model(self):
        """Return the best trained model for production use"""
        best_name = self._pick_best_model()
        
        name_map = {
            'VADER': 'vader',
            'Logistic Regression': 'logistic',
            'Linear SVM': 'svm',
            'LightGBM': 'lightgbm',
            'RoBERTa': 'roberta',
            'DistilRoBERTa': 'roberta'
        }
        
        internal_name = name_map.get(best_name)
        
        if internal_name in ['logistic', 'svm', 'lightgbm']:
            return {
                'model': self.results[internal_name]['trained_model'],
                'vectorizer': self.results[internal_name]['vectorizer'],
                'type': internal_name,
                'accuracy': self.results[internal_name]['accuracy'],
                'f1_score': self.results[internal_name]['f1_score']
            }
        else:
            return {
                'type': internal_name,
                'accuracy': self.results.get(internal_name, {}).get('accuracy'),
                'f1_score': self.results.get(internal_name, {}).get('f1_score')
            }


def run_sentiment_benchmark(
    csv_path: str = None, 
    df: pd.DataFrame = None,
    weight_accuracy: float = 0.5,
    weight_f1: float = 0.3,
    weight_speed: float = 0.2
):
    """
    Run benchmark on CSV file or DataFrame
    
    Args:
        csv_path: Path to CSV file
        df: DataFrame (if already loaded)
        weight_accuracy: Weight for accuracy (default 0.5)
        weight_f1: Weight for F1 score (default 0.3)
        weight_speed: Weight for speed (default 0.2)
    
    Returns:
        SentimentBenchmark instance with results
    """
    if df is None and csv_path:
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            try:
                df = pd.read_csv(csv_path, on_bad_lines='skip', engine='python')
            except Exception:
                df = pd.read_csv(csv_path, on_bad_lines='skip', engine='python', encoding='utf-8', quoting=3)
    elif df is None:
        raise ValueError("Must provide either csv_path or df")
    
    benchmark = SentimentBenchmark(df)
    benchmark.run_all_benchmarks(weight_accuracy, weight_f1, weight_speed)
    
    return benchmark


if __name__ == "__main__":
    import sys
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/Amazon_Reviews.csv"
    
    print(f"Loading data from: {csv_path}")
    benchmark = run_sentiment_benchmark(csv_path=csv_path)
    
    best = benchmark.get_best_model()
    print(f"\nBest model: {best['type']} (Accuracy: {best.get('accuracy', 'N/A')}, F1: {best.get('f1_score', 'N/A')})")
