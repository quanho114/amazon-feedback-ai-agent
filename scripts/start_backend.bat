@echo off
cd /d C:\Users\Admin\OneDrive\Desktop\Amazon\amazon-feedback-ai-agent
echo Starting FastAPI Backend...
python -m uvicorn api:app --reload --port 8000
pause
