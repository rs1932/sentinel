#!/bin/bash

# Sentinel Platform Stop Script
# Usage: ./stop.sh [backend|frontend|both]
# This script stops backend API and/or frontend services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default ports
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Parse command line arguments
SERVICE_TO_STOP="$1"
STOP_BACKEND=true
STOP_FRONTEND=true

if [ "$SERVICE_TO_STOP" = "backend" ]; then
    STOP_FRONTEND=false
elif [ "$SERVICE_TO_STOP" = "frontend" ]; then
    STOP_BACKEND=false
elif [ ! -z "$SERVICE_TO_STOP" ] && [ "$SERVICE_TO_STOP" != "both" ]; then
    echo -e "${RED}Error: Invalid argument '$SERVICE_TO_STOP'${NC}"
    echo -e "${YELLOW}Usage: $0 [backend|frontend|both]${NC}"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0              # Stop both services"
    echo "  $0 both         # Stop both services"
    echo "  $0 backend      # Stop only backend"
    echo "  $0 frontend     # Stop only frontend"
    exit 1
fi

# Function to find and kill processes by port
kill_by_port() {
    local port=$1
    local service_name=$2
    
    echo -e "${YELLOW}Looking for processes on port $port ($service_name)...${NC}"
    
    # Find processes listening on the port
    local pids=$(lsof -t -i:$port 2>/dev/null)
    
    if [ -z "$pids" ]; then
        echo -e "${BLUE}No processes found on port $port${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Found processes: $pids${NC}"
    
    # Try graceful shutdown first (SIGTERM)
    echo -e "${YELLOW}Attempting graceful shutdown...${NC}"
    for pid in $pids; do
        if kill -TERM $pid 2>/dev/null; then
            echo -e "${GREEN}Sent SIGTERM to PID $pid${NC}"
        fi
    done
    
    # Wait a few seconds for graceful shutdown
    sleep 3
    
    # Check if processes are still running
    local remaining_pids=$(lsof -t -i:$port 2>/dev/null)
    
    if [ ! -z "$remaining_pids" ]; then
        echo -e "${YELLOW}Some processes still running, forcing shutdown...${NC}"
        # Force kill remaining processes
        for pid in $remaining_pids; do
            if kill -KILL $pid 2>/dev/null; then
                echo -e "${GREEN}Force killed PID $pid${NC}"
            fi
        done
        sleep 1
    fi
    
    # Final check
    local final_check=$(lsof -t -i:$port 2>/dev/null)
    if [ -z "$final_check" ]; then
        echo -e "${GREEN}✓ Successfully stopped $service_name on port $port${NC}"
    else
        echo -e "${RED}✗ Failed to stop some processes on port $port${NC}"
        return 1
    fi
}

# Function to kill processes by name pattern
kill_by_pattern() {
    local pattern=$1
    local service_name=$2
    
    echo -e "${YELLOW}Looking for $service_name processes...${NC}"
    
    # Find processes by pattern
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -z "$pids" ]; then
        echo -e "${BLUE}No $service_name processes found${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Found $service_name processes: $pids${NC}"
    
    # Try graceful shutdown first
    echo -e "${YELLOW}Attempting graceful shutdown of $service_name...${NC}"
    for pid in $pids; do
        if kill -TERM $pid 2>/dev/null; then
            echo -e "${GREEN}Sent SIGTERM to $service_name PID $pid${NC}"
        fi
    done
    
    # Wait for graceful shutdown
    sleep 3
    
    # Check if processes are still running
    local remaining_pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ ! -z "$remaining_pids" ]; then
        echo -e "${YELLOW}Some $service_name processes still running, forcing shutdown...${NC}"
        for pid in $remaining_pids; do
            if kill -KILL $pid 2>/dev/null; then
                echo -e "${GREEN}Force killed $service_name PID $pid${NC}"
            fi
        done
        sleep 1
    fi
    
    # Final check
    local final_check=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ -z "$final_check" ]; then
        echo -e "${GREEN}✓ Successfully stopped all $service_name processes${NC}"
    else
        echo -e "${RED}✗ Failed to stop some $service_name processes${NC}"
        return 1
    fi
}

echo -e "${BLUE}========================================${NC}"
if [ "$STOP_BACKEND" = true ] && [ "$STOP_FRONTEND" = true ]; then
    echo -e "${BLUE}   Sentinel Platform Stop Script${NC}"
elif [ "$STOP_BACKEND" = true ]; then
    echo -e "${BLUE}   Sentinel Backend Stop Script${NC}"
else
    echo -e "${BLUE}   Sentinel Frontend Stop Script${NC}"
fi
echo -e "${BLUE}========================================${NC}"
echo ""

SUCCESS=true

# Stop Backend
if [ "$STOP_BACKEND" = true ]; then
    echo -e "${GREEN}Stopping Backend API...${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"
    
    # Try multiple approaches to stop backend
    # 1. Kill by port
    if ! kill_by_port $BACKEND_PORT "Backend API"; then
        SUCCESS=false
    fi
    
    # 2. Kill by process pattern (uvicorn with our app)
    if ! kill_by_pattern "uvicorn.*src.main:app" "Backend (uvicorn)"; then
        SUCCESS=false
    fi
    
    # 3. Kill by process pattern (python main.py)
    if ! kill_by_pattern "python.*src/main.py" "Backend (main.py)"; then
        SUCCESS=false
    fi
    
    echo ""
fi

# Stop Frontend
if [ "$STOP_FRONTEND" = true ]; then
    echo -e "${GREEN}Stopping Frontend...${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"
    
    # Try multiple approaches to stop frontend
    # 1. Kill by port
    if ! kill_by_port $FRONTEND_PORT "Frontend"; then
        SUCCESS=false
    fi
    
    # 2. Kill by process pattern (Next.js)
    if ! kill_by_pattern "node.*next.*dev" "Frontend (Next.js)"; then
        SUCCESS=false
    fi
    
    # 3. Kill by process pattern (npm run dev)
    if ! kill_by_pattern "npm.*run.*dev" "Frontend (npm)"; then
        SUCCESS=false
    fi
    
    echo ""
fi

# Final summary
echo -e "${BLUE}========================================${NC}"
if [ "$SUCCESS" = true ]; then
    echo -e "${GREEN}✓ Stop completed successfully!${NC}"
else
    echo -e "${YELLOW}⚠ Stop completed with some warnings${NC}"
    echo -e "${YELLOW}Some processes may not have stopped cleanly${NC}"
fi
echo -e "${BLUE}========================================${NC}"
echo ""

# Show remaining processes on our ports (for verification)
echo -e "${BLUE}Verification:${NC}"
if [ "$STOP_BACKEND" = true ]; then
    local backend_check=$(lsof -t -i:$BACKEND_PORT 2>/dev/null || true)
    if [ -z "$backend_check" ]; then
        echo -e "${GREEN}✓ Port $BACKEND_PORT (backend) is free${NC}"
    else
        echo -e "${RED}✗ Port $BACKEND_PORT (backend) still in use by: $backend_check${NC}"
    fi
fi

if [ "$STOP_FRONTEND" = true ]; then
    local frontend_check=$(lsof -t -i:$FRONTEND_PORT 2>/dev/null || true)
    if [ -z "$frontend_check" ]; then
        echo -e "${GREEN}✓ Port $FRONTEND_PORT (frontend) is free${NC}"
    else
        echo -e "${RED}✗ Port $FRONTEND_PORT (frontend) still in use by: $frontend_check${NC}"
    fi
fi

echo ""
echo -e "${YELLOW}Tip: Use './start.sh' to restart services${NC}"