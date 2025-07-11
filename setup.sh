#!/bin/bash

# Alert Monitoring System - Setup Script
# This script sets up the Alert Monitoring System on Ubuntu

set -e

echo "🚨 Alert Monitoring System Setup Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Ubuntu
if [[ ! -f /etc/os-release ]] || ! grep -q "Ubuntu" /etc/os-release; then
    print_error "This script is designed for Ubuntu. Please install manually on other systems."
    exit 1
fi

print_status "Detected Ubuntu system"

# Check Python 3.10
print_status "Checking Python 3.10..."
if ! command -v python3.10 &> /dev/null; then
    print_status "Installing Python 3.10..."
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip
fi

print_success "Python 3.10 is available"

# Check Docker
print_status "Checking Docker..."
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    sudo apt update
    sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    print_warning "Please log out and log back in for Docker permissions to take effect"
fi

print_success "Docker is available"

# Check Docker Compose
print_status "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

print_success "Docker Compose is available"

# Create project directory structure
print_status "Creating project directory structure..."
mkdir -p data/{chromadb,uploads}
mkdir -p logs
mkdir -p config

# Set permissions
chmod 755 data logs config
chmod 755 data/chromadb data/uploads

print_success "Directory structure created"

# Create environment file
print_status "Creating environment configuration..."
if [[ ! -f .env ]]; then
    cat > .env << EOF
# Alert Monitoring System Configuration

# App Settings
ENVIRONMENT=development
DEBUG=true

# Ollama Settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# ChromaDB Settings
CHROMADB_PERSIST_DIRECTORY=./data/chromadb
CHROMADB_COLLECTION=alerts

# API Settings
API_V1_PREFIX=/api/v1

# Security
SECRET_KEY=your-secret-key-change-in-production

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# Alert Processing
SIMILARITY_THRESHOLD=0.8
MAX_GROUP_SIZE=50
RCA_MAX_TOKENS=2000
EOF
    print_success "Environment file created (.env)"
else
    print_warning "Environment file already exists"
fi

# Setup Python virtual environments
print_status "Setting up Python virtual environments..."

# Backend virtual environment
if [[ ! -d backend/venv ]]; then
    print_status "Creating backend virtual environment..."
    cd backend
    python3.10 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cd ..
    print_success "Backend virtual environment created"
else
    print_warning "Backend virtual environment already exists"
fi

# Frontend virtual environment
if [[ ! -d frontend/venv ]]; then
    print_status "Creating frontend virtual environment..."
    cd frontend
    python3.10 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cd ..
    print_success "Frontend virtual environment created"
else
    print_warning "Frontend virtual environment already exists"
fi

# Create startup scripts
print_status "Creating startup scripts..."

# Backend startup script
cat > start_backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF

# Frontend startup script
cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd frontend
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
EOF

# Docker startup script
cat > start_docker.sh << 'EOF'
#!/bin/bash
echo "🚨 Starting Alert Monitoring System with Docker..."

# Check if Ollama models need to be pulled
echo "Checking Ollama models..."
if ! docker-compose exec -T ollama ollama list | grep -q "llama3"; then
    echo "Pulling Ollama models (this may take a while)..."
    docker-compose exec ollama ollama pull llama3
    docker-compose exec ollama ollama pull nomic-embed-text
fi

echo "✅ Alert Monitoring System is ready!"
echo "Frontend: http://localhost:8501"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
EOF

# Make scripts executable
chmod +x start_backend.sh start_frontend.sh start_docker.sh

print_success "Startup scripts created"

# Create systemd service files (optional)
if [[ "$1" == "--systemd" ]]; then
    print_status "Creating systemd service files..."
    
    # Backend service
    sudo tee /etc/systemd/system/alert-monitoring-backend.service > /dev/null << EOF
[Unit]
Description=Alert Monitoring System Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start_backend.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service
    sudo tee /etc/systemd/system/alert-monitoring-frontend.service > /dev/null << EOF
[Unit]
Description=Alert Monitoring System Frontend
After=network.target alert-monitoring-backend.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start_frontend.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    print_success "Systemd services created"
    print_status "Enable services with: sudo systemctl enable alert-monitoring-backend alert-monitoring-frontend"
    print_status "Start services with: sudo systemctl start alert-monitoring-backend alert-monitoring-frontend"
fi

# Final instructions
print_success "🎉 Setup completed successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Quick Start Options:${NC}"
echo ""
echo -e "${BLUE}Option 1 - Docker (Recommended):${NC}"
echo "  docker-compose up -d"
echo "  ./start_docker.sh"
echo ""
echo -e "${BLUE}Option 2 - Manual (Development):${NC}"
echo "  Terminal 1: ./start_backend.sh"
echo "  Terminal 2: ./start_frontend.sh"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "  🌐 Frontend (Streamlit): http://localhost:8501"
echo "  🔧 Backend API: http://localhost:8000"
echo "  📚 API Documentation: http://localhost:8000/docs"
echo "  🤖 Ollama API: http://localhost:11434"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo "  • First startup may take time to download Ollama models (llama3, nomic-embed-text)"
echo "  • Make sure ports 8000, 8501, and 11434 are available"
echo "  • Check logs in ./logs/ directory for troubleshooting"
echo "  • Edit .env file to customize configuration"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if user wants to start immediately
read -p "Would you like to start the system now with Docker? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting Alert Monitoring System..."
    docker-compose up -d
    
    # Wait for Ollama to be ready
    print_status "Waiting for Ollama to start..."
    until docker-compose exec -T ollama ollama --version > /dev/null 2>&1; do
        sleep 2
    done
    
    # Pull models
    print_status "Pulling Ollama models (this may take several minutes)..."
    docker-compose exec ollama ollama pull llama3 || true
    docker-compose exec ollama ollama pull nomic-embed-text || true
    
    print_success "System started! Visit http://localhost:8501 to access the frontend"
fi

print_success "Setup script completed. Enjoy your AI Alert Monitoring System! 🚨"
