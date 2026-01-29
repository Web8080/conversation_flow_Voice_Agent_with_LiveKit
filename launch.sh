#!/bin/bash

echo "🚀 Launching Voice Agent System"
echo "================================"

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env file not found!"
    echo "Please copy backend/.env.example to backend/.env and configure your API keys"
    echo "See services/SERVICES_SETUP.md for instructions"
    exit 1
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "⚠️  Warning: frontend/.env.local not found"
    echo "Creating from .env.example..."
    cp frontend/.env.example frontend/.env.local 2>/dev/null || true
    echo "Please configure frontend/.env.local with your LiveKit URL"
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check for Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 20+"
    exit 1
fi

echo ""
echo "Starting services..."
echo ""

# Start Ollama in background if available
if command -v ollama &> /dev/null; then
    echo "🦙 Starting Ollama (local LLM)..."
    ollama serve > /dev/null 2>&1 &
    OLLAMA_PID=$!
    sleep 2
    ollama pull llama3.2 > /dev/null 2>&1 &
    echo "   Ollama started (PID: $OLLAMA_PID)"
else
    echo "⚠️  Ollama not found. Install from https://ollama.ai/ for local LLM"
fi

# Start Backend
echo "🐍 Starting Python backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt > /dev/null 2>&1

python main.py dev &
BACKEND_PID=$!
cd ..
echo "   Backend started (PID: $BACKEND_PID)"

# Wait a bit for backend to initialize
sleep 3

# Start Frontend
echo "⚛️  Starting Next.js frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install > /dev/null 2>&1
fi

npm run dev &
FRONTEND_PID=$!
cd ..
echo "   Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "✅ All services started!"
echo ""
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend logs: Check terminal output"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID $OLLAMA_PID 2>/dev/null; exit" INT

wait


