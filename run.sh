#!/bin/bash
echo "Starting Without® DPP System..."

# Start API
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Start Web UI
cd web
python -m http.server 3000 &
WEB_PID=$!

echo "API Running: http://localhost:8000"
echo "Web UI:     http://localhost:3000"
echo "Press Ctrl+C to stop."

wait $API_PID $WEB_PID
