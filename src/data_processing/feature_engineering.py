def add_features(df):
    # Number of exclamations
    df['num_exclamations'] = df['clean_review'].apply(lambda x: x.count('!') if isinstance(x, str) else 0)

    # Number of questions
    df['num_questions'] = df['clean_review'].apply(lambda x: x.count('?') if isinstance(x, str) else 0)

    # Has uppercase words
    df['has_uppercase'] = df['clean_review'].apply(lambda x: any(ch.isupper() for ch in x) if isinstance(x, str) else False)

    # Extract day, month, year
    df['day'] = df['Review Date'].dt.day
    df['month'] = df['Review Date'].dt.month
    df['year'] = df['Review Date'].dt.year

    return df
