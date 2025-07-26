#!/bin/bash

echo "🚀 Starting VibeCorp Autonomous Startup Simulation..."

# Kill any existing processes
echo "🛑 Stopping existing servers..."
pkill -f "python -m api.main" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null

# Wait a moment for processes to stop
sleep 2

echo "🔧 Starting backend server..."
# Start backend in background
source venv/bin/activate && python -m api.main &
BACKEND_PID=$!

echo "🎨 Starting frontend server..."
# Start frontend in background
cd startup-simulator-ui && npm run dev &
FRONTEND_PID=$!

echo "✅ Servers started!"
echo "📡 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:5173"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 To stop servers, run: kill $BACKEND_PID $FRONTEND_PID"
echo "💡 Or use: pkill -f 'python -m api.main' && pkill -f 'npm run dev'"

# Keep script running to show logs
wait 