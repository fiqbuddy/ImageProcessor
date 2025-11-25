#!/bin/bash
# Start all services in separate terminal windows

echo "🚀 Starting all Image Processing services..."

# Start services in background
echo "Starting Resize Service..."
python services/resize_service.py &
RESIZE_PID=$!

echo "Starting Filter Service..."
python services/filter_service.py &
FILTER_PID=$!

echo "Starting Watermark Service..."
python services/watermark_service.py &
WATERMARK_PID=$!

echo "Starting Orchestrator Service..."
python services/orchestrator_service.py &
ORCH_PID=$!

echo ""
echo "✅ All services started!"
echo ""
echo "Service Ports:"
echo "  - Resize Service:      50052"
echo "  - Filter Service:      50053"
echo "  - Watermark Service:   50054"
echo "  - Orchestrator:        50055"
echo ""
echo "To run the demo:"
echo "  python client/pipeline_demo.py"
echo ""
echo "To stop all services, press Ctrl+C"

# Wait for Ctrl+C
trap "kill $RESIZE_PID $FILTER_PID $WATERMARK_PID $ORCH_PID; exit" INT
wait
