"""
Test script to verify sentiment analysis accuracy
Compares SVM predictions with actual ratings
"""
import pandas as pd
import re
import sys
import os

def extract_rating_from_text(text):
    """Extract numeric rating from text like 'Rated 5 out of 5 stars'"""
    match = re.search(r'Rated (\d+) out of', str(text))
    if match:
        return int(match.group(1))
    return None

def rating_to_sentiment(rating):
    """Convert rating to expected sentiment"""
    if rating >= 4:
        return 'positive'
    elif rating <= 2:
        return 'negative'
    else:
        return 'neutral'

def main():
    # Ask for CSV file path
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        print("📁 Enter CSV file path (or drag & drop file here):")
        csv_path = input().strip().strip('"')
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return
    
    print(f"📂 Loading CSV: {csv_path}")
    
    # Try reading with different strategies (same as api.py)
    df = None
    
    # Strategy 1: TAB delimiter
    try:
        df = pd.read_csv(csv_path, sep='\t', encoding='utf-8', on_bad_lines='skip', engine='python')
        if len(df.columns) > 5:  # Valid if has multiple columns
            print(f"✅ CSV loaded successfully! ({len(df.columns)} columns)")
        else:
            df = None
    except:
        pass
    
    # Strategy 2: Comma delimiter
    if df is None:
        try:
            df = pd.read_csv(csv_path, sep=',', encoding='utf-8', on_bad_lines='skip', engine='python')
            if len(df.columns) > 5:
                print(f"✅ CSV loaded successfully! ({len(df.columns)} columns)")
            else:
                df = None
        except:
            pass
    
    # Strategy 3: Auto-detect
    if df is None:
        try:
            df = pd.read_csv(csv_path, sep=None, encoding='utf-8', on_bad_lines='skip', engine='python')
            print(f"✅ CSV loaded successfully! ({len(df.columns)} columns)")
        except Exception as e:
            print(f"❌ Failed to load CSV: {e}")
            return
    
    if df is None:
        print("❌ Failed to parse CSV with any delimiter")
        return
    
    # Run sentiment analysis
    print("🔄 Running SVM sentiment analysis...")
    try:
        from src.analytics.sentiment_model import analyze_dataframe
        
        # Find text column
        text_col = None
        for col in df.columns:
            if 'review' in col.lower() and 'text' in col.lower():
                text_col = col
                break
        
        if not text_col:
            text_col = 'Review Text'  # Default
        
        df = analyze_dataframe(df, text_col=text_col)
        print("✅ Sentiment analysis completed!")
    except Exception as e:
        print(f"❌ Sentiment analysis failed: {e}")
        return
    
    print(f"📊 Total reviews: {len(df):,}")
    print(f"Columns: {df.columns.tolist()}\n")
    
    # Extract numeric rating
    if 'Rating' in df.columns:
        df['numeric_rating'] = df['Rating'].apply(extract_rating_from_text)
        df['expected_sentiment'] = df['numeric_rating'].apply(
            lambda x: rating_to_sentiment(x) if pd.notna(x) else None
        )
    else:
        print("❌ No 'Rating' column found!")
        return
    
    # Compare with SVM sentiment
    if 'ai_sentiment' not in df.columns:
        print("❌ No 'ai_sentiment' column found. Run sentiment analysis first!")
        return
    
    # Calculate accuracy
    valid_rows = df[df['expected_sentiment'].notna()]
    matches = valid_rows[valid_rows['ai_sentiment'] == valid_rows['expected_sentiment']]
    accuracy = len(matches) / len(valid_rows) * 100
    
    print("=" * 80)
    print("SENTIMENT ANALYSIS ACCURACY TEST")
    print("=" * 80)
    print(f"\n📈 Overall Accuracy: {accuracy:.2f}%")
    print(f"   Matches: {len(matches):,} / {len(valid_rows):,}\n")
    
    # Show distribution
    print("📊 SVM Sentiment Distribution:")
    svm_dist = df['ai_sentiment'].value_counts()
    for sentiment, count in svm_dist.items():
        pct = count / len(df) * 100
        print(f"   {sentiment.capitalize()}: {count:,} ({pct:.1f}%)")
    
    print("\n📊 Rating-Based Expected Distribution:")
    expected_dist = df['expected_sentiment'].value_counts()
    for sentiment, count in expected_dist.items():
        pct = count / len(valid_rows) * 100
        print(f"   {sentiment.capitalize()}: {count:,} ({pct:.1f}%)")
    
    # Sample 10 random reviews for manual inspection
    print("\n" + "=" * 80)
    print("🔍 RANDOM SAMPLE (10 reviews)")
    print("=" * 80)
    
    sample = df.sample(n=min(10, len(df)))
    
    for idx, row in sample.iterrows():
        rating = row.get('numeric_rating', 'N/A')
        expected = row.get('expected_sentiment', 'N/A')
        svm = row.get('ai_sentiment', 'N/A')
        text = str(row.get('Review Text', ''))[:150]
        
        match_icon = "✅" if expected == svm else "❌"
        
        print(f"\n{match_icon} Review #{idx}")
        print(f"   Rating: {rating} stars → Expected: {expected}")
        print(f"   SVM Predicted: {svm}")
        print(f"   Text: {text}...")
    
    # Show mismatches
    print("\n" + "=" * 80)
    print("❌ MISMATCHES (first 5)")
    print("=" * 80)
    
    mismatches = valid_rows[valid_rows['ai_sentiment'] != valid_rows['expected_sentiment']]
    
    if len(mismatches) > 0:
        print(f"\nTotal mismatches: {len(mismatches):,}\n")
        
        for idx, row in mismatches.head(5).iterrows():
            rating = row.get('numeric_rating', 'N/A')
            expected = row.get('expected_sentiment', 'N/A')
            svm = row.get('ai_sentiment', 'N/A')
            text = str(row.get('Review Text', ''))[:200]
            
            print(f"Review #{idx}")
            print(f"   Rating: {rating} stars → Expected: {expected}")
            print(f"   SVM Predicted: {svm}")
            print(f"   Text: {text}...")
            print()
    else:
        print("\n✅ No mismatches found! Perfect accuracy!")
    
    print("=" * 80)
    print("\n💡 Interpretation:")
    if accuracy >= 85:
        print("   ✅ SVM model is performing well and aligns with ratings!")
    elif accuracy >= 70:
        print("   ⚠️  SVM model has moderate accuracy. Some text-rating mismatches.")
    else:
        print("   ❌ SVM model has low accuracy. Consider using rating-based method.")
    
    print(f"\n   Note: Mismatches can occur when:")
    print(f"   - User gives high rating but writes negative text (or vice versa)")
    print(f"   - Sarcasm or complex sentiment in text")
    print(f"   - SVM model captures nuances that rating doesn't")

if __name__ == "__main__":
    main()
