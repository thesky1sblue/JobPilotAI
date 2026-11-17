#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "      🚀 Launching JobPilot AI (Local Development)        "
echo "=========================================================="

# 1. Start FastAPI Backend in background
echo "-> Starting Backend API on http://localhost:8000..."
cd "$PROJECT_ROOT/backend"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Trap signals to shut down both processes cleanly
cleanup() {
    echo ""
    echo "Shutting down JobPilot AI..."
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 2. Start Next.js Frontend
echo "-> Starting Next.js Dashboard on http://localhost:3000..."
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✨ JobPilot AI is running!"
echo "   Dashboard: http://localhost:3000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   API Base:  http://localhost:8000/api/v1"
echo ""
echo "Press Ctrl+C to stop both servers."

wait
