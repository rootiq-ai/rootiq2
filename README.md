# 🚨 AI Alert Monitoring System

An intelligent alert monitoring system that uses AI to automatically group similar alerts and generate Root Cause Analysis (RCA) reports. Built with FastAPI, Streamlit, Ollama (Llama3), and ChromaDB.

![System Architecture](https://via.placeholder.com/800x400/667eea/FFFFFF?text=AI+Alert+Monitoring+System)

## ✨ Features

### 🤖 **AI-Powered Alert Grouping**
- Automatic clustering of similar alerts using semantic similarity
- Machine learning-based pattern recognition
- Configurable similarity thresholds
- Support for multiple monitoring systems

### 📊 **Root Cause Analysis (RAG)**
- AI-generated RCA reports using Retrieval-Augmented Generation
- Historical incident analysis
- Knowledge base integration
- Confidence scoring for analysis quality

### 🎯 **Smart Monitoring**
- Real-time alert processing
- Multi-source alert ingestion (Prometheus, Grafana, Nagios, etc.)
- Advanced filtering and search capabilities
- Interactive dashboards and visualizations

### 🔧 **Enterprise Ready**
- RESTful API with OpenAPI documentation
- Containerized deployment with Docker
- Scalable vector database with ChromaDB
- Comprehensive logging and monitoring

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Monitoring    │    │   Monitoring    │
│   System 1      │    │   System 2      │    │   System N      │
│  (Prometheus)   │    │   (Grafana)     │    │   (Nagios)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼──────────────┐
                    │      FastAPI Backend       │
                    │   ┌─────────────────────┐  │
                    │   │  Alert Grouper      │  │
                    │   │  (AI Clustering)    │  │
                    │   └─────────────────────┘  │
                    │   ┌─────────────────────┐  │
                    │   │   RCA Generator     │  │
                    │   │  (RAG with Llama3)  │  │
                    │   └─────────────────────┘  │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │     Data Layer             │
                    │  ┌─────────┐ ┌─────────┐   │
                    │  │ChromaDB │ │ Ollama  │   │
                    │  │(Vectors)│ │(Llama3) │   │
                    │  └─────────┘ └─────────┘   │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Streamlit Frontend       │
                    │ ┌─────────────────────────┐│
                    │ │    Alert Dashboard      ││
                    │ └─────────────────────────┘│
                    │ ┌─────────────────────────┐│
                    │ │    Group Viewer         ││
                    │ └─────────────────────────┘│
                    │ ┌─────────────────────────┐│
                    │ │    RCA Display          ││
                    │ └─────────────────────────┘│
                    └────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Ubuntu 20.04+ (tested)
- Python 3.10+
- Docker & Docker Compose
- 8GB+ RAM (for Ollama models)
- 10GB+ free disk space

### 1. Clone Repository
```bash
git clone <repository-url>
cd alert-monitoring-system
chmod +x setup.sh
```

### 2. Automated Setup (Recommended)
```bash
./setup.sh
```

The setup script will:
- Install Python 3.10, Docker, and Docker Compose
- Create virtual environments
- Download required dependencies
- Set up directory structure
- Create startup scripts

### 3. Start the System

#### Option A: Docker (Recommended)
```bash
docker-compose up -d
```

#### Option B: Manual Development Setup
```bash
# Terminal 1 - Backend
./start_backend.sh

# Terminal 2 - Frontend  
./start_frontend.sh
```

### 4. Access the System
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

## 📁 Project Structure

```
alert-monitoring-system/
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/v1/             # API endpoints
│   │   │   ├── alerts.py       # Alert management
│   │   │   └── groups.py       # Group management
│   │   ├── core/               # Core configuration
│   │   │   ├── config.py       # Settings
│   │   │   └── database.py     # ChromaDB setup
│   │   ├── models/             # Pydantic models
│   │   │   ├── alert.py        # Alert schemas
│   │   │   └── group.py        # Group schemas
│   │   ├── services/           # Business logic
│   │   │   ├── alert_grouper.py    # AI grouping
│   │   │   ├── llm_service.py      # Ollama integration
│   │   │   ├── rca_generator.py    # RCA generation
│   │   │   └── vector_store.py     # Vector operations
│   │   └── main.py             # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # Streamlit frontend
│   ├── components/             # UI components
│   │   ├── alert_dashboard.py  # Main dashboard
│   │   ├── group_viewer.py     # Group management
│   │   └── rca_display.py      # RCA viewer
│   ├── utils/
│   │   └── api_client.py       # Backend API client
│   ├── app.py                  # Main Streamlit app
│   ├── requirements.txt
│   └── Dockerfile
├── data/                       # Data directory
│   ├── chromadb/              # Vector database
│   └── uploads/               # File uploads
├── logs/                      # Application logs
├── docker-compose.yml         # Docker configuration
├── setup.sh                  # Setup script
└── README.md
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
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

# Alert Processing
SIMILARITY_THRESHOLD=0.8
MAX_GROUP_SIZE=50
RCA_MAX_TOKENS=2000
```

### Supported Monitoring Systems
- Prometheus
- Grafana
- Nagios
- Zabbix
- DataDog
- New Relic
- PagerDuty
- Custom webhooks

## 📚 API Documentation

### Alert Endpoints
```bash
POST   /api/v1/alerts/              # Create alert
GET    /api/v1/alerts/{id}          # Get alert
PUT    /api/v1/alerts/{id}          # Update alert
DELETE /api/v1/alerts/{id}          # Delete alert
GET    /api/v1/alerts/              # List alerts
POST   /api/v1/alerts/search        # Search alerts
POST   /api/v1/alerts/{id}/similar  # Find similar alerts
```

### Group Endpoints
```bash
GET    /api/v1/groups/              # List groups
GET    /api/v1/groups/{id}          # Get group
PUT    /api/v1/groups/{id}          # Update group
POST   /api/v1/groups/search        # Search groups
POST   /api/v1/groups/{id}/rca      # Generate RCA
GET    /api/v1/groups/{id}/rca      # Get RCA
POST   /api/v1/groups/{id}/resolve  # Resolve group
```

### Example: Create Alert
```bash
curl -X POST "http://localhost:8000/api/v1/alerts/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "High CPU Usage",
    "description": "CPU usage exceeded 90% on web-server-01",
    "severity": "High",
    "source_system": "Prometheus",
    "service_name": "web-api",
    "host_name": "web-server-01",
    "environment": "production",
    "tags": ["cpu", "performance"],
    "metrics": {"cpu_usage": 95.2}
  }'
```

## 🎯 Usage Examples

### 1. Alert Creation and Processing
```python
import requests

# Create an alert
alert_data = {
    "title": "Database Connection Timeout",
    "description": "Database connections timing out after 30 seconds",
    "severity": "Critical",
    "source_system": "Nagios",
    "service_name": "user-db",
    "host_name": "db-primary",
    "environment": "production"
}

response = requests.post(
    "http://localhost:8000/api/v1/alerts/",
    json=alert_data
)
```

### 2. Find Similar Alerts
```python
# Find alerts similar to a specific alert
similarity_request = {
    "alert_id": "alert-123",
    "threshold": 0.8,
    "limit": 10
}

response = requests.post(
    "http://localhost:8000/api/v1/alerts/alert-123/similar",
    json=similarity_request
)
```

### 3. Generate RCA
```python
# Generate RCA for a group
rca_request = {
    "group_id": "group-456",
    "force_regenerate": False,
    "include_context": True
}

response = requests.post(
    "http://localhost:8000/api/v1/groups/group-456/rca",
    json=rca_request
)
```

## 🔍 Monitoring and Troubleshooting

### Health Checks
```bash
# Check API health
curl http://localhost:8000/health

# Check system info
curl http://localhost:8000/info

# Check Ollama
curl http://localhost:11434/api/tags
```

### Logs
```bash
# Backend logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama
```

### Common Issues

#### Ollama Models Not Found
```bash
docker-compose exec ollama ollama pull llama3
docker-compose exec ollama ollama pull nomic-embed-text
```

#### Port Conflicts
```bash
# Check port usage
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :8501
sudo netstat -tulpn | grep :11434
```

#### ChromaDB Permission Issues
```bash
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

## 🚀 Production Deployment

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml alert-monitoring
```

### Kubernetes
```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alert-monitoring-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: alert-monitoring-backend
  template:
    metadata:
      labels:
        app: alert-monitoring-backend
    spec:
      containers:
      - name: backend
        image: alert-monitoring-backend:latest
        ports:
        - containerPort: 8000
```

### Environment-Specific Settings

#### Production (.env.production)
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
SIMILARITY_THRESHOLD=0.85
MAX_GROUP_SIZE=100
```

#### Staging (.env.staging)
```bash
ENVIRONMENT=staging
DEBUG=true
LOG_LEVEL=INFO
SIMILARITY_THRESHOLD=0.8
MAX_GROUP_SIZE=50
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Code formatting
black .
isort .

# Linting
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM inference
- [ChromaDB](https://www.trychroma.com/) for vector database
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Streamlit](https://streamlit.io/) for the frontend framework
- [Llama3](https://ai.meta.com/blog/meta-llama-3/) for the language model

## 📞 Support

- 📧 Email: support@alertmonitoring.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📖 Documentation: [Wiki](https://github.com/your-repo/wiki)

---

**Made with ❤️ for better incident management**
