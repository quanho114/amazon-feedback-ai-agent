import pandas as pd

# --- Feature from datetime ---
def extract_day(date_series: pd.Series) -> pd.Series:
    return date_series.dt.day

def extract_month(date_series: pd.Series) -> pd.Series:
    return date_series.dt.month

def extract_year(date_series: pd.Series) -> pd.Series:
    return date_series.dt.year

# --- Feature from text ---
def review_length(text_series: pd.Series) -> pd.Series:
    return text_series.apply(lambda x: len(x.split()))

def num_exclamations(text_series: pd.Series) -> pd.Series:
    return text_series.apply(lambda x: x.count('!'))

def num_questions(text_series: pd.Series) -> pd.Series:
    return text_series.apply(lambda x: x.count('?'))

def has_uppercase(text_series: pd.Series) -> pd.Series:
    return text_series.apply(lambda x: any(c.isupper() for c in x))

# --- Encode sentiment from Rating ---
def encode_sentiment(rating_series: pd.Series) -> pd.Series:
    def f(score):
        if score in [4,5]:
            return 'Positive'
        elif score in [1,2]:
            return 'Negative'
        elif score == 3:
            return 'Neutral'
        else:
            return 'Unknown'
    return rating_series.apply(f)
