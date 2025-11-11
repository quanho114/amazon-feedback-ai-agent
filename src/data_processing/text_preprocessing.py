import re

def clean_text(text):
    """Basic text cleaning for review"""
    text = str(text)
    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s,.!?']", "", text)
    text = text.lower()
    return text
