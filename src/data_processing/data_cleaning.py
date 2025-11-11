import pandas as pd
import os

def load_and_clean(raw_file, cols, text_col, clean_func):
    """
    Load raw CSV, select columns, drop missing, clean text
    """
    if not os.path.exists(raw_file):
        raise FileNotFoundError(f"Raw file not found: {raw_file}")

    # Load CSV
    try:
        df = pd.read_csv(raw_file, quotechar='"', encoding='utf-8', on_bad_lines='skip')
    except:
        import csv
        rows = []
        with open(raw_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, quotechar='"')
            for row in reader:
                rows.append(row)
        df = pd.DataFrame(rows)

    # Select columns
    df = df[cols]

    # Drop missing text
    df = df.dropna(subset=[text_col])

    # Clean text column
    df['clean_review'] = df[text_col].apply(clean_func)

    # Convert Rating to int
    df['Rating'] = df['Rating'].str.extract(r'(\d)').astype(int)

    # Convert Review Date
    df['Review Date'] = pd.to_datetime(df['Review Date'], errors='coerce')

    # Add review length
    df['review_length'] = df['clean_review'].apply(lambda x: len(x.split()))

    return df
