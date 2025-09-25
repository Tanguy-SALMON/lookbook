#!/bin/bash

# Lookbook MPC Complete Restart Script
echo "🚀 Restarting Lookbook MPC System..."

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    echo "🔄 Checking port $port..."
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "   Killing process $pid on port $port"
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
}

# Stop all services
echo "🛑 Stopping all services..."
kill_port 8000  # Main API
kill_port 8001  # Vision Sidecar  
kill_port 3000  # Dashboard
kill_port 11434 # Ollama (optional)

echo "⏳ Waiting for services to stop..."
sleep 3

# Start services in correct order
echo ""
echo "🔧 Starting services in order..."

# Check if Ollama is running, start if not
echo "1. Checking Ollama..."
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "   Starting Ollama server..."
    nohup ollama serve > ollama.log 2>&1 &
    sleep 5
    
    # Pull models if needed
    echo "   Checking vision model..."
    if ! ollama list | grep -q "qwen2.5vl"; then
        echo "   Pulling qwen2.5vl model..."
        ollama pull qwen2.5vl
    fi
else
    echo "   ✅ Ollama already running"
fi

# Start Vision Sidecar
echo ""
echo "2. Starting Vision Sidecar..."
cd "$(dirname "$0")"
nohup python vision_sidecar.py > vision_sidecar.log 2>&1 &
VISION_PID=$!
sleep 3

# Check if Vision Sidecar started successfully
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "   ✅ Vision Sidecar running on port 8001"
else
    echo "   ❌ Vision Sidecar failed to start"
    exit 1
fi

# Start Main API
echo ""
echo "3. Starting Main API..."
nohup python main.py > main_api.log 2>&1 &
MAIN_PID=$!
sleep 3

# Check if Main API started successfully
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Main API running on port 8000"
else
    echo "   ❌ Main API failed to start"
    exit 1
fi

# Start Dashboard
echo ""
echo "4. Starting Dashboard..."
cd shadcn
nohup npm run dev > dashboard.log 2>&1 &
DASHBOARD_PID=$!
cd ..
sleep 5

# Check if Dashboard started successfully
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Dashboard running on port 3000"
else
    echo "   ⚠️  Dashboard may still be starting..."
fi

echo ""
echo "🎉 System Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check all services
if pgrep -f "ollama serve" > /dev/null; then
    echo "✅ Ollama Server: Running (port 11434)"
else
    echo "❌ Ollama Server: Not running"
fi

if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Vision Sidecar: Running (port 8001)"
else
    echo "❌ Vision Sidecar: Not running"
fi

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Main API: Running (port 8000)"
else
    echo "❌ Main API: Not running"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Dashboard: Running (port 3000)"
else
    echo "❌ Dashboard: Not running"
fi

echo ""
echo "🔗 Access Points:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Dashboard:    http://localhost:3000"
echo "🔌 API Docs:     http://localhost:8000/docs"
echo "🎨 Demo UI:      http://localhost:8000/demo.html"
echo "👁️  Vision API:  http://localhost:8001/health"
echo ""
echo "📋 Process IDs saved to:"
echo "   Vision Sidecar: $VISION_PID"
echo "   Main API: $MAIN_PID" 
echo "   Dashboard: $DASHBOARD_PID"
echo ""
echo "📄 Logs available in:"
echo "   ollama.log, vision_sidecar.log, main_api.log, shadcn/dashboard.log"
echo ""
echo "🛑 To stop all services: ./stop-all.sh"
echo "🔄 To restart all services: ./restart-all.sh"
echo ""
echo "✨ System ready! Open http://localhost:3000 for the dashboard"