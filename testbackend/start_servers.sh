#!/bin/bash

# Start the authentication API server
echo "🚀 Starting Authentication API on port 8093..."
python3 auth_api.py &
AUTH_PID=$!

# Wait a moment for the auth server to start
sleep 2

# Start the WebSocket server
echo "🚀 Starting WebSocket Server on port 8092..."
python3 together_ai_backend.py &
WS_PID=$!

echo "✅ Both servers are running!"
echo "📡 Auth API: http://localhost:8093"
echo "🔌 WebSocket: ws://localhost:8092"
echo "⏹️  Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
wait

# Cleanup function
cleanup() {
    echo "🛑 Stopping servers..."
    kill $AUTH_PID $WS_PID 2>/dev/null
    echo "👋 Servers stopped"
    exit 0
}

# Handle Ctrl+C
trap cleanup SIGINT

# Keep script running
while true; do
    sleep 1
done
