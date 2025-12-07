#!/bin/bash

# Amazon Feedback AI Agent - Deploy Script
# Sử dụng: ./deploy.sh [local|vps|docker]

set -e

MODE=${1:-local}

echo "🚀 Deploying Amazon Feedback AI Agent - Mode: $MODE"

case $MODE in
  local)
    echo "📦 Installing dependencies..."
    
    # Backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Frontend
    cd frontend
    npm install
    npm run build
    cd ..
    
    echo "✅ Dependencies installed!"
    echo ""
    echo "🎯 To start the app:"
    echo "   Backend:  python api.py"
    echo "   Frontend: cd frontend && npm run dev"
    ;;
    
  vps)
    echo "🌐 Deploying to VPS..."
    
    # Check if PM2 is installed
    if ! command -v pm2 &> /dev/null; then
        echo "Installing PM2..."
        sudo npm install -g pm2
    fi
    
    # Install dependencies
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    cd frontend
    npm install
    npm run build
    cd ..
    
    # Stop old processes
    pm2 delete backend || true
    pm2 delete frontend || true
    
    # Start new processes
    pm2 start "uvicorn api:app --host 0.0.0.0 --port 8000" --name backend
    pm2 serve frontend/dist 3000 --name frontend --spa
    
    pm2 save
    pm2 startup
    
    echo "✅ Deployed to VPS!"
    echo "📊 Check status: pm2 status"
    echo "📝 View logs: pm2 logs"
    ;;
    
  docker)
    echo "🐳 Deploying with Docker..."
    
    # Build and start containers
    docker-compose down
    docker-compose build
    docker-compose up -d
    
    echo "✅ Docker containers started!"
    echo "📊 Check status: docker-compose ps"
    echo "📝 View logs: docker-compose logs -f"
    ;;
    
  *)
    echo "❌ Unknown mode: $MODE"
    echo "Usage: ./deploy.sh [local|vps|docker]"
    exit 1
    ;;
esac

echo ""
echo "🎉 Deployment complete!"
