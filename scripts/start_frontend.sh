#!/bin/bash

# Frontend startup script for Alert Monitoring System
# This script starts the Streamlit frontend server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎨 Starting Alert Monitoring System Frontend${NC}"
echo "==============================================="

# Check if we're in the right directory
if [[ ! -f "frontend/app.py" ]]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    echo "Expected to find: frontend/app.py"
    exit 1
fi

# Change to frontend directory
cd frontend

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
if ! python -c "import streamlit" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Dependencies not found. Installing...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Set environment variables
export API_BASE_URL=${API_BASE_URL:-http://localhost:8000}
export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-8501}
export STREAMLIT_SERVER_ADDRESS=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}

# Check if backend is running
echo -e "${BLUE}🔗 Checking backend connection...${NC}"
if curl -s -f "$API_BASE_URL/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running at $API_BASE_URL${NC}"
    # Get backend info
    BACKEND_INFO=$(curl -s "$API_BASE_URL/info" 2>/dev/null || echo "{}")
    if [[ "$BACKEND_INFO" != "{}" ]]; then
        echo -e "${GREEN}   Backend version: $(echo $BACKEND_INFO | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('version', 'unknown'))" 2>/dev/null || echo 'unknown')${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Backend not responding at $API_BASE_URL${NC}"
    echo -e "${YELLOW}   The frontend will start but some features may not work${NC}"
    echo -e "${YELLOW}   Please start the backend with: ./start_backend.sh${NC}"
fi

# Create Streamlit config directory
mkdir -p ~/.streamlit

# Create Streamlit configuration
cat > ~/.streamlit/config.toml << EOF
[server]
headless = true
port = $STREAMLIT_SERVER_PORT
address = "$STREAMLIT_SERVER_ADDRESS"
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
showErrorDetails = true

[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[logger]
level = "info"
EOF

echo -e "${GREEN}✅ Streamlit configuration created${NC}"
echo ""
echo -e "${BLUE}🌐 Starting Streamlit server...${NC}"
echo -e "${YELLOW}   Frontend: http://localhost:$STREAMLIT_SERVER_PORT${NC}"
echo -e "${YELLOW}   Backend API: $API_BASE_URL${NC}"
echo ""
echo -e "${BLUE}💡 Press Ctrl+C to stop the server${NC}"
echo -e "${BLUE}💡 The app will automatically open in your browser${NC}"
echo ""

# Start the Streamlit server
exec streamlit run app.py \
    --server.port $STREAMLIT_SERVER_PORT \
    --server.address $STREAMLIT_SERVER_ADDRESS \
    --server.headless true \
    --browser.gatherUsageStats false
