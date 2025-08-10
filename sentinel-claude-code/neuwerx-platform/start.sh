#!/bin/bash

# Sentinel Platform Startup Script
# Usage: ./start.sh [backend|frontend]
# This script starts backend API and/or frontend services

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default ports
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Parse command line arguments
SERVICE_TO_START="$1"
START_BACKEND=true
START_FRONTEND=true

if [ "$SERVICE_TO_START" = "backend" ]; then
    START_FRONTEND=false
elif [ "$SERVICE_TO_START" = "frontend" ]; then
    START_BACKEND=false
elif [ ! -z "$SERVICE_TO_START" ] && [ "$SERVICE_TO_START" != "both" ]; then
    echo -e "${RED}Error: Invalid argument '$SERVICE_TO_START'${NC}"
    echo -e "${YELLOW}Usage: $0 [backend|frontend|both]${NC}"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0              # Start both services"
    echo "  $0 both         # Start both services"
    echo "  $0 backend      # Start only backend"
    echo "  $0 frontend     # Start only frontend"
    exit 1
fi

# Function to check if port is in use
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}Error: Port $port is already in use (required for $service)${NC}"
        echo -e "${YELLOW}Please stop the service using port $port or use a different port${NC}"
        echo ""
        echo -e "${YELLOW}To see what's using the port:${NC}"
        echo "  lsof -i :$port"
        echo ""
        echo -e "${YELLOW}To kill the process:${NC}"
        echo "  kill \$(lsof -t -i:$port)"
        exit 1
    fi
}

echo -e "${BLUE}========================================${NC}"
if [ "$START_BACKEND" = true ] && [ "$START_FRONTEND" = true ]; then
    echo -e "${BLUE}   Sentinel Platform Startup Script${NC}"
elif [ "$START_BACKEND" = true ]; then
    echo -e "${BLUE}   Sentinel Backend Startup Script${NC}"
else
    echo -e "${BLUE}   Sentinel Frontend Startup Script${NC}"
fi
echo -e "${BLUE}========================================${NC}"
echo ""

# Check ports before starting
if [ "$START_BACKEND" = true ]; then
    echo -e "${YELLOW}Checking backend port $BACKEND_PORT...${NC}"
    check_port $BACKEND_PORT "Backend API"
    echo -e "${GREEN}✓ Port $BACKEND_PORT is available${NC}"
fi

if [ "$START_FRONTEND" = true ]; then
    echo -e "${YELLOW}Checking frontend port $FRONTEND_PORT...${NC}"
    check_port $FRONTEND_PORT "Frontend"
    echo -e "${GREEN}✓ Port $FRONTEND_PORT is available${NC}"
fi

echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    # Kill backend process if it exists
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill frontend process if it exists
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining uvicorn processes
    pkill -f "uvicorn src.main:app" 2>/dev/null || true
    
    echo -e "${GREEN}Services stopped successfully${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${RED}Error: Virtual environment not found at $SCRIPT_DIR/venv${NC}"
    echo -e "${YELLOW}Please create a virtual environment first:${NC}"
    echo "  cd '$SCRIPT_DIR'"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo -e "${YELLOW}Please install Node.js first${NC}"
    exit 1
fi

# Start Backend API
if [ "$START_BACKEND" = true ]; then
    echo -e "${GREEN}Starting Backend API...${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"

    cd "$SCRIPT_DIR"

    # Activate virtual environment and start backend
    (
        source venv/bin/activate
        
        # Check if uvicorn is installed
        if ! python -c "import uvicorn" 2>/dev/null; then
            echo -e "${YELLOW}Installing uvicorn...${NC}"
            pip install uvicorn
        fi
        
        cd api
        
        echo -e "${GREEN}Backend starting on http://localhost:$BACKEND_PORT${NC}"
        echo -e "${GREEN}API Docs available at http://localhost:$BACKEND_PORT/api/v1/sentinel/docs${NC}"
        
        # Start uvicorn with hot reload for development
        uvicorn src.main:app \
            --host 0.0.0.0 \
            --port $BACKEND_PORT \
            --reload \
            --log-level info \
            2>&1 | sed 's/^/[BACKEND] /' &
        
        BACKEND_PID=$!
        echo -e "${GREEN}Backend started with PID: $BACKEND_PID${NC}"
    ) &

    BACKEND_PID=$!

    # Wait a moment for backend to start
    sleep 3
fi

# Start Frontend
if [ "$START_FRONTEND" = true ]; then
    if [ "$START_BACKEND" = true ]; then
        echo -e "\n${GREEN}Starting Frontend...${NC}"
    else
        echo -e "${GREEN}Starting Frontend...${NC}"
    fi
    echo -e "${BLUE}----------------------------------------${NC}"

    cd "$SCRIPT_DIR/sentinel/frontend"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install
    fi

    echo -e "${GREEN}Frontend starting on http://localhost:$FRONTEND_PORT${NC}"

    # Start Next.js development server
    npm run dev 2>&1 | sed 's/^/[FRONTEND] /' &

    FRONTEND_PID=$!
    echo -e "${GREEN}Frontend started with PID: $FRONTEND_PID${NC}"
fi

# Display startup summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Services Started Successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Access Points:${NC}"
if [ "$START_FRONTEND" = true ]; then
    echo -e "  • Frontend:  ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
fi
if [ "$START_BACKEND" = true ]; then
    echo -e "  • Backend:   ${BLUE}http://localhost:$BACKEND_PORT${NC}"
    echo -e "  • API Docs:  ${BLUE}http://localhost:$BACKEND_PORT/api/v1/sentinel/docs${NC}"
fi
echo ""
if [ "$START_BACKEND" = true ]; then
    echo -e "${GREEN}Database:${NC}"
    echo -e "  • PostgreSQL: ${BLUE}sentinel_dev${NC}"
    echo ""
    echo -e "${GREEN}Default Credentials:${NC}"
    echo -e "  • Platform Admin: ${BLUE}admin@sentinel.com / admin123${NC}"
    echo -e "  • Maritime Admin: ${BLUE}maritimeadmin@maritime.com / admin123${NC}"
    echo ""
fi
if [ "$START_BACKEND" = true ] && [ "$START_FRONTEND" = true ]; then
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
elif [ "$START_BACKEND" = true ]; then
    echo -e "${YELLOW}Press Ctrl+C to stop backend service${NC}"
else
    echo -e "${YELLOW}Press Ctrl+C to stop frontend service${NC}"
fi
echo -e "${BLUE}========================================${NC}"
echo ""

# Keep script running and show logs
wait