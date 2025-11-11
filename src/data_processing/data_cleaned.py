import os
from text_preprocessing import clean_text
from data_cleaning import load_and_clean
from feature_engineering import add_features

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
RAW_FILE = os.path.join(BASE_DIR, "data/raw/Amazon_Reviews.csv")
PROCESSED_FILE = os.path.join(BASE_DIR, "data/processed/reviews_clean.csv")

def main():
    cols = ["Review Count","Review Date", "Rating", "Review Title", "Review Text"]
    df = load_and_clean(RAW_FILE, cols, text_col="Review Text", clean_func=clean_text)
    df = add_features(df)

    # Ensure processed folder exists
    os.makedirs(os.path.dirname(PROCESSED_FILE), exist_ok=True)

    # Save cleaned + features data
    df.to_csv(PROCESSED_FILE, index=False, encoding='utf-8')
    print(f"Cleaned data with features saved to: {PROCESSED_FILE}")

if __name__ == "__main__":
    main()
