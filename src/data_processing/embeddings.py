import pandas as pd
import os
from sentence_transformers import SentenceTransformer

# Load cleaned data
df = pd.read_csv("data/processed/reviews_clean.csv")
texts = df['clean_review'].tolist()

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Tạo embeddings
embeddings = model.encode(texts, show_progress_bar=True)

# Lưu embeddings riêng
os.makedirs("data/embeddings", exist_ok=True)
import pickle
with open("data/embeddings/reviews_embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)

print("Saved embeddings separately in data/embeddings/")
