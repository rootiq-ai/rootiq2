#!/bin/bash

# Backend startup script for Alert Monitoring System
# This script starts the FastAPI backend server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Alert Monitoring System Backend${NC}"
echo "=============================================="

# Check if we're in the right directory
if [[ ! -f "backend/app/main.py" ]]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    echo "Expected to find: backend/app/main.py"
    exit 1
fi

# Change to backend directory
cd backend

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo -e "${YELLOW}⚠️ Virtual environment not found. Creating...${NC}"
    python3.10 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Dependencies not found. Installing...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating data directories...${NC}"
mkdir -p ../data/chromadb
mkdir -p ../data/uploads
mkdir -p ../logs

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)
export ENVIRONMENT=${ENVIRONMENT:-development}
export OLLAMA_HOST=${OLLAMA_HOST:-http://localhost:11434}
export CHROMADB_PERSIST_DIRECTORY=${CHROMADB_PERSIST_DIRECTORY:-../data/chromadb}
export LOG_FILE=${LOG_FILE:-../logs/app.log}

# Check if Ollama is running
echo -e "${BLUE}🤖 Checking Ollama service...${NC}"
if curl -s -f "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama is running at $OLLAMA_HOST${NC}"
else
    echo -e "${YELLOW}⚠️ Ollama not responding at $OLLAMA_HOST${NC}"
    echo -e "${YELLOW}   Please ensure Ollama is running or start with Docker Compose${NC}"
fi

# Check if ChromaDB directory is writable
if [[ ! -w "../data/chromadb" ]]; then
    echo -e "${RED}❌ ChromaDB directory is not writable: ../data/chromadb${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pre-flight checks completed${NC}"
echo ""
echo -e "${BLUE}🌐 Starting FastAPI server...${NC}"
echo -e "${YELLOW}   Backend API: http://localhost:8000${NC}"
echo -e "${YELLOW}   API Docs: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}   Health: http://localhost:8000/health${NC}"
echo ""
echo -e "${BLUE}💡 Press Ctrl+C to stop the server${NC}"
echo ""

# Start the FastAPI server
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info \
    --access-log \
    --use-colors
