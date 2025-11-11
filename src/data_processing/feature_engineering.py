def add_features(df):
    """Add metadata / text features"""
    # Number of exclamations
    df['num_exclamations'] = df['clean_review'].str.count('!')
    # Number of questions
    df['num_questions'] = df['clean_review'].str.count('\?')
    # Has uppercase words
    df['has_uppercase'] = df['clean_review'].apply(lambda x: any(c.isupper() for c in x))
    # Day of week
    df['day_of_week'] = df['Review Date'].dt.day_name()
    return df
