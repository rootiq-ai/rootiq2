#!/bin/bash

# Docker startup script for Alert Monitoring System
# This script starts the entire system using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Starting Alert Monitoring System with Docker${NC}"
echo "=================================================="

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "docker-compose.yml" ]]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    echo "Expected to find: docker-compose.yml"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are available${NC}"

# Create necessary directories
echo -e "${BLUE}📁 Creating data directories...${NC}"
mkdir -p data/chromadb
mkdir -p data/uploads
mkdir -p logs
chmod 755 data logs
chmod 755 data/chromadb data/uploads

# Stop any existing containers
echo -e "${BLUE}🛑 Stopping any existing containers...${NC}"
docker-compose down --remove-orphans >/dev/null 2>&1 || true

# Pull latest images if they exist
echo -e "${BLUE}📥 Pulling latest images...${NC}"
docker-compose pull || echo -e "${YELLOW}⚠️ Could not pull some images, will build locally${NC}"

# Build and start services
echo -e "${BLUE}🔨 Building and starting services...${NC}"
docker-compose up -d --build

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${CYAN}   Checking $service_name...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}   ✅ $service_name is ready${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}   ⏳ Attempt $attempt/$max_attempts - waiting for $service_name...${NC}"
        sleep 5
        ((attempt++))
    done
    
    echo -e "${RED}   ❌ $service_name failed to start within $(($max_attempts * 5)) seconds${NC}"
    return 1
}

# Check Ollama service
echo -e "${PURPLE}🤖 Checking Ollama service...${NC}"
if check_service "Ollama" "http://localhost:11434/api/tags"; then
    echo -e "${BLUE}📥 Pulling required Ollama models...${NC}"
    
    # Pull Llama3 model
    echo -e "${CYAN}   Pulling llama3 model (this may take several minutes)...${NC}"
    docker-compose exec -T ollama ollama pull llama3 || {
        echo -e "${YELLOW}   ⚠️ Failed to pull llama3, will download on first use${NC}"
    }
    
    # Pull embedding model
    echo -e "${CYAN}   Pulling nomic-embed-text model...${NC}"
    docker-compose exec -T ollama ollama pull nomic-embed-text || {
        echo -e "${YELLOW}   ⚠️ Failed to pull nomic-embed-text, will download on first use${NC}"
    }
    
    echo -e "${GREEN}   ✅ Ollama models ready${NC}"
else
    echo -e "${RED}   ❌ Ollama service failed to start${NC}"
fi

# Check Backend service
echo -e "${PURPLE}🔧 Checking Backend service...${NC}"
check_service "Backend" "http://localhost:8000/health"

# Check Frontend service
echo -e "${PURPLE}🎨 Checking Frontend service...${NC}"
check_service "Frontend" "http://localhost:8501/_stcore/health"

# Show service status
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo "=================="
docker-compose ps

# Show service logs (last 10 lines)
echo ""
echo -e "${BLUE}📋 Recent Service Logs:${NC}"
echo "======================="
echo -e "${CYAN}Backend logs:${NC}"
docker-compose logs --tail=5 backend || true
echo ""
echo -e "${CYAN}Frontend logs:${NC}"
docker-compose logs --tail=5 frontend || true

# System information
echo ""
echo -e "${GREEN}🎉 Alert Monitoring System is ready!${NC}"
echo "========================================"
echo ""
echo -e "${YELLOW}📱 Access URLs:${NC}"
echo -e "   🌐 Frontend (Streamlit): ${CYAN}http://localhost:8501${NC}"
echo -e "   🔧 Backend API:          ${CYAN}http://localhost:8000${NC}"
echo -e "   📚 API Documentation:    ${CYAN}http://localhost:8000/docs${NC}"
echo -e "   🤖 Ollama API:           ${CYAN}http://localhost:11434${NC}"
echo ""
echo -e "${YELLOW}🛠️ Management Commands:${NC}"
echo -e "   View logs:     ${CYAN}docker-compose logs -f${NC}"
echo -e "   Stop system:   ${CYAN}docker-compose down${NC}"
echo -e "   Restart:       ${CYAN}docker-compose restart${NC}"
echo -e "   Status:        ${CYAN}docker-compose ps${NC}"
echo ""
echo -e "${YELLOW}🧪 Next Steps:${NC}"
echo -e "   1. Visit the frontend at http://localhost:8501"
echo -e "   2. Create some sample alerts to test the system"
echo -e "   3. Run the demo: ${CYAN}python demo.py${NC}"
echo ""

# Check if we should run the demo
if [[ "$1" == "--demo" ]]; then
    echo -e "${BLUE}🚀 Running demo automatically...${NC}"
    sleep 5
    python demo.py --no-cleanup
fi

# Optional: Show real-time logs
if [[ "$1" == "--logs" ]] || [[ "$2" == "--logs" ]]; then
    echo -e "${BLUE}📋 Showing real-time logs (Ctrl+C to exit):${NC}"
    docker-compose logs -f
fi

echo -e "${GREEN}✨ System startup completed successfully!${NC}"
