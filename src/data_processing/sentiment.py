import os
import pandas as pd
from sklearn.model_selection import train_test_split

def map_sentiment(row):
    """Map numeric rating to sentiment label"""
    if row['Rating'] in [4, 5]:
        return 'Positive'
    elif row['Rating'] == 3:
        return 'Neutral'
    elif row['Rating'] in [1, 2]:
        return 'Negative'
    else: 
        return None
    
# Load data
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
CSV_FILE = os.path.join(BASE_DIR, "data/processed/reviews_clean.csv")

if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(f"{CSV_FILE} not found. Run data_cleaned.py first.")

df = pd.read_csv(CSV_FILE)

df['sentiment'] = df.apply(map_sentiment, axis=1)

# Select columns
columns_to_keep = [
    'clean_review', 'review_length', 'num_exclamations',
    'num_questions', 'has_uppercase', 'day', 'month', 'year',
    'sentiment'
]
df = df[columns_to_keep]

# split data for training
train_df, test_df = train_test_split(
    df,
    test_size=0.2,
    stratify=df['sentiment'],
    random_state=42
)

train_path = os.path.join(BASE_DIR, "data/processed/train.csv")
test_path = os.path.join(BASE_DIR, "data/processed/test.csv")

train_df.to_csv(train_path, index=False)
test_df.to_csv(test_path, index=False)

print(f"Train/test data saved to:\n{train_path}\n{test_path}")
