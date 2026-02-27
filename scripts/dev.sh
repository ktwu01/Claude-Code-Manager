#!/bin/bash
# Start both backend and frontend dev servers

cd "$(dirname "$0")/.."

echo "Starting Claude Code Manager..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""

# Start backend
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
cd frontend && npx vite --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

# Handle Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

echo ""
echo "Both servers started. Press Ctrl+C to stop."
wait
