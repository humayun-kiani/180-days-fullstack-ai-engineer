#!/bin/bash
# Start all microservices

echo "Starting all microservices..."
echo ""

# Activate venv
source venv/bin/activate

# Start each service in background
uvicorn auth_service.main:app --port 8001 --log-level warning &
PID_AUTH=$!
echo "✅ Auth Service started (PID $PID_AUTH) → http://localhost:8001"

sleep 0.5

uvicorn ai_service.main:app --port 8003 --log-level warning &
PID_AI=$!
echo "✅ AI Service started (PID $PID_AI)   → http://localhost:8003"

sleep 0.5

uvicorn task_service.main:app --port 8002 --log-level warning &
PID_TASK=$!
echo "✅ Task Service started (PID $PID_TASK) → http://localhost:8002"

sleep 0.5

uvicorn gateway.main:app --port 8000 --log-level warning &
PID_GW=$!
echo "✅ API Gateway started (PID $PID_GW)  → http://localhost:8000"

echo ""
echo "All services running!"
echo ""
echo "Test with:"
echo "  curl http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait and handle Ctrl+C
trap "kill $PID_AUTH $PID_AI $PID_TASK $PID_GW; echo 'All stopped.'" INT
wait