# File: src/config.py
import os
from dotenv import load_dotenv

# 1. Load .env file
load_dotenv()

# 2. Retrieve environment variables (Export these for other modules to use)
MEGALLM_API_KEY = os.getenv("MEGALLM_API_KEY")
MEGALLM_BASE_URL = os.getenv("MEGALLM_BASE_URL")
MEGALLM_MODEL = os.getenv("MEGALLM_MODEL")

# 3. Verification block (Only runs when executing this file directly)
if __name__ == "__main__":
    print("--- CONFIGURATION CHECK ---")
    
    if MEGALLM_API_KEY:
        # Print only the first 10 characters for security
        print(f"API Key: Found ({MEGALLM_API_KEY[:10]}...)")
    else:
        print("❌ API Key: NOT FOUND! (Please check your .env file name or location)")

    print(f"Base URL: {MEGALLM_BASE_URL}")
    print(f"Model: {MEGALLM_MODEL}")