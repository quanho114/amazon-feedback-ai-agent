import pandas as pd
import os

def load_and_clean(raw_file, selected_cols, text_col, clean_func):
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

    df = df.replace({r'[\r\n]+': ' '}, regex=True)
    df = df[selected_cols]
    
    # Drop missing text and Rating
    df = df.dropna(subset=[text_col, 'Rating'])

    # Clean text column, convert non-str to empty string
    df['clean_review'] = df[text_col].apply(lambda x: clean_func(x) if isinstance(x, str) else "")

    # Convert Rating to int
    df['Rating'] = df['Rating'].astype(str).str.extract(r'(\d)').astype(int)

    # Convert Review Date
    df['Review Date'] = pd.to_datetime(df['Review Date'], errors='coerce')
    df = df.dropna(subset=['Review Date'])

    # Add review length safely
    df['review_length'] = df['clean_review'].apply(lambda x: len(x.split()) if isinstance(x, str) else 0)

    return df
