import os
import sys
import pandas as pd
import nltk

# --- NLTK Setup: download stopwords into venv/nltk_data ---
NLTK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../venv/nltk_data"))
os.makedirs(NLTK_DIR, exist_ok=True)
nltk.data.path.append(NLTK_DIR)

try:
    from nltk.corpus import stopwords
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords", download_dir=NLTK_DIR)
    nltk.data.path.append(NLTK_DIR)

# --- Import clean_text from utils ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(PROJECT_ROOT)
from utils.text_cleaning import clean_text


# --- Main Preprocessing Function ---
def preprocess_text(df: pd.DataFrame, text_col: str = "Review Text") -> pd.DataFrame:
    df["clean_review"] = df[text_col].apply(clean_text)
    return df


# --- Script Execution ---
if __name__ == "__main__":
    csv_path = "data/processed/reviews_clean.csv"

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} not found.")

    df = pd.read_csv(csv_path)
    df = preprocess_text(df)

    print(df[["Review Text", "clean_review"]].head())
