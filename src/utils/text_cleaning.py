import re
import string
import emoji
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

stop_words = set(stopwords.words('english'))
stemmer = SnowballStemmer('english')

def lowercase(text: str) -> str:
    return text.lower()

def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans("", "", string.punctuation))

def remove_numbers(text: str) -> str:
    return re.sub(r'\d+', '', text)

def remove_extra_whitespace(text: str) -> str:
    return " ".join(text.split())

def remove_stopwords(text: str) -> str:
    return " ".join([w for w in text.split() if w not in stop_words])

def remove_emoji(text: str) -> str:
    return emoji.replace_emoji(text, replace='')

def stem_text(text: str) -> str:
    return " ".join([stemmer.stem(w) for w in text.split()])

def clean_text(text: str) -> str:
    text = lowercase(text)

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = lowercase(text)
    text = remove_emoji(text)
    text = remove_punctuation(text)
    text = remove_numbers(text)
    text = remove_extra_whitespace(text)
    text = remove_stopwords(text)
    text = stem_text(text)
    return text
