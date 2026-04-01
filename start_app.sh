#!/bin/bash

# Learning App Startup Script
# This script starts backend and frontend using ports from .env (default 8000/3000)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"

# Load .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Print with color
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        print_warning "Killing existing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

# Cleanup function
cleanup() {
    print_info "Shutting down services..."

    # Kill backend process
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        print_info "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi

    # Kill frontend process
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        print_info "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    # Also kill by port as fallback
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT

    print_success "Services stopped"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    print_warning "Virtual environment not found. Creating it now..."
    python3 -m venv "$PROJECT_ROOT/venv"

    if [ $? -eq 0 ]; then
        print_success "Virtual environment created"
        print_info "Installing backend dependencies..."
        source "$PROJECT_ROOT/venv/bin/activate"
        pip install -r "$PROJECT_ROOT/backend/requirements.txt"

        if [ $? -eq 0 ]; then
            print_success "Backend dependencies installed"
        else
            print_error "Failed to install backend dependencies"
            exit 1
        fi
    else
        print_error "Failed to create virtual environment"
        exit 1
    fi
fi

# Check if frontend node_modules exists
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    print_warning "Frontend node modules not found. Installing dependencies..."
    cd "$PROJECT_ROOT/frontend"
    npm install
    if [ $? -eq 0 ]; then
        print_success "Frontend dependencies installed"
    else
        print_error "Failed to install frontend dependencies"
        exit 1
    fi
fi

# Check if .env exists in project root
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    print_warning ".env file not found in project root."
    print_error "Please create .env file in the project root directory"
    exit 1
fi

echo ""
print_info "${PURPLE}===================================================${NC}"
print_info "${PURPLE}  Learning App${NC}"
print_info "${PURPLE}===================================================${NC}"
print_info "Backend Port:      $BACKEND_PORT"
print_info "Frontend Port:     $FRONTEND_PORT"
print_info "==================================================="
echo ""

# Kill any existing processes on the ports
kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT

# Start Backend
print_info "Starting backend server on port $BACKEND_PORT..."
cd "$PROJECT_ROOT/backend"

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Start backend with uvicorn
uvicorn src.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload 2>&1 | tee "$LOGS_DIR/backend.log" &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if kill -0 $BACKEND_PID 2>/dev/null; then
    print_success "Backend started (PID: $BACKEND_PID)"
    print_info "Backend URL: http://localhost:$BACKEND_PORT"
    print_info "Backend API: http://localhost:$BACKEND_PORT/api"
else
    print_error "Backend failed to start. Check logs/backend.log for details"
    cat "$LOGS_DIR/backend.log"
    exit 1
fi

# Start Frontend
print_info "Starting frontend server on port $FRONTEND_PORT..."
cd "$PROJECT_ROOT/frontend"

PORT=$FRONTEND_PORT npm start 2>&1 | tee "$LOGS_DIR/frontend.log" &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

# Check if frontend started successfully
if kill -0 $FRONTEND_PID 2>/dev/null; then
    print_success "Frontend started (PID: $FRONTEND_PID)"
    print_info "Frontend URL: http://localhost:$FRONTEND_PORT"
else
    print_error "Frontend failed to start. Check logs/frontend.log for details"
    cat "$LOGS_DIR/frontend.log"
    cleanup
    exit 1
fi

# Print access information
echo ""
print_success "==================================================="
print_success "  Application is ready!"
print_success "==================================================="
print_success "Frontend:        http://localhost:$FRONTEND_PORT"
print_success "Backend:         http://localhost:$BACKEND_PORT"
print_success "API Docs:        http://localhost:$BACKEND_PORT/docs"
print_success "==================================================="
echo ""
print_info "Press Ctrl+C to stop all services"
echo ""
print_info "Log files:"
print_info "  Backend:       logs/backend.log"
print_info "  Frontend:      logs/frontend.log"
echo ""

# Monitor processes
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process died. Check logs/backend.log"
        tail -n 20 "$LOGS_DIR/backend.log"
        cleanup
        exit 1
    fi

    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend process died. Check logs/frontend.log"
        tail -n 20 "$LOGS_DIR/frontend.log"
        cleanup
        exit 1
    fi

    sleep 5
done
