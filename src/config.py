# File: src/config.py
import os
from dotenv import load_dotenv

# 1. Load .env file
load_dotenv()

# 2. Main LLM Config (for heavy tasks: analysis, insights, RAG)
MEGALLM_API_KEY = os.getenv("MEGALLM_API_KEY")
MEGALLM_BASE_URL = os.getenv("MEGALLM_BASE_URL")
MEGALLM_MODEL = os.getenv("MEGALLM_MODEL")

# 3. Fast Chat LLM Config (optional - for quick conversations)
# If not set, will use main config
CHAT_API_KEY = os.getenv("CHAT_API_KEY", MEGALLM_API_KEY)
CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", MEGALLM_BASE_URL)
CHAT_MODEL = os.getenv("CHAT_MODEL", MEGALLM_MODEL)  # Default to same model

# 4. Verification block (Only runs when executing this file directly)
if __name__ == "__main__":
    print("--- CONFIGURATION CHECK ---")
    
    print("\n🔧 Main LLM (Heavy Tasks):")
    if MEGALLM_API_KEY:
        print(f"  API Key: Found ({MEGALLM_API_KEY[:10]}...)")
    else:
        print("  ❌ API Key: NOT FOUND!")
    print(f"  Base URL: {MEGALLM_BASE_URL}")
    print(f"  Model: {MEGALLM_MODEL}")
    
    print("\n⚡ Chat LLM (Fast Responses):")
    if CHAT_API_KEY:
        print(f"  API Key: Found ({CHAT_API_KEY[:10]}...)")
    else:
        print("  ❌ API Key: NOT FOUND!")
    print(f"  Base URL: {CHAT_BASE_URL}")
    print(f"  Model: {CHAT_MODEL}")