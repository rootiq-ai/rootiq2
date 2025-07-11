"""
Alert data models and schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class SeverityLevel(str, Enum):
    """Alert severity levels"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"

class AlertStatus(str, Enum):
    """Alert status"""
    OPEN = "Open"
    ACKNOWLEDGED = "Acknowledged"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class MonitoringSystem(str, Enum):
    """Supported monitoring systems"""
    PROMETHEUS = "Prometheus"
    GRAFANA = "Grafana"
    NAGIOS = "Nagios"
    ZABBIX = "Zabbix"
    DATADOG = "DataDog"
    NEWRELIC = "New Relic"
    PAGERDUTY = "PagerDuty"
    CUSTOM = "Custom"

class AlertBase(BaseModel):
    """Base alert model"""
    title: str = Field(..., description="Alert title/summary")
    description: str = Field(..., description="Detailed alert description")
    severity: SeverityLevel = Field(..., description="Alert severity level")
    source_system: MonitoringSystem = Field(..., description="Source monitoring system")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert timestamp")
    
    # Optional fields
    service_name: Optional[str] = Field(None, description="Affected service name")
    host_name: Optional[str] = Field(None, description="Affected host name")
    environment: Optional[str] = Field(None, description="Environment (prod, staging, dev)")
    tags: Optional[List[str]] = Field(default_factory=list, description="Alert tags")
    metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Associated metrics")
    
    @validator('tags', pre=True)
    def parse_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v or []

class AlertCreate(AlertBase):
    """Schema for creating new alerts"""
    external_id: Optional[str] = Field(None, description="External alert ID from source system")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "High CPU Usage Alert",
                "description": "CPU usage exceeded 90% for more than 5 minutes on web-server-01",
                "severity": "High",
                "source_system": "Prometheus",
                "service_name": "web-api",
                "host_name": "web-server-01",
                "environment": "production",
                "tags": ["cpu", "performance", "infrastructure"],
                "metrics": {
                    "cpu_usage": 95.2,
                    "duration_minutes": 7,
                    "threshold": 90
                },
                "external_id": "prometheus-alert-12345"
            }
        }

class Alert(AlertBase):
    """Full alert model with system fields"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique alert ID")
    status: AlertStatus = Field(default=AlertStatus.OPEN, description="Alert status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Grouping information
    group_id: Optional[str] = Field(None, description="Associated group ID")
    similarity_score: Optional[float] = Field(None, description="Similarity score for grouping")
    
    # Processing information
    processed: bool = Field(default=False, description="Whether alert has been processed")
    embedding_generated: bool = Field(default=False, description="Whether embedding has been generated")
    
    # External reference
    external_id: Optional[str] = Field(None, description="External alert ID from source system")
    external_url: Optional[str] = Field(None, description="URL to external alert")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "High CPU Usage Alert",
                "description": "CPU usage exceeded 90% for more than 5 minutes on web-server-01",
                "severity": "High",
                "source_system": "Prometheus",
                "status": "Open",
                "service_name": "web-api",
                "host_name": "web-server-01",
                "environment": "production",
                "tags": ["cpu", "performance", "infrastructure"],
                "metrics": {
                    "cpu_usage": 95.2,
                    "duration_minutes": 7,
                    "threshold": 90
                },
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "group_id": None,
                "processed": False,
                "embedding_generated": False
            }
        }

class AlertUpdate(BaseModel):
    """Schema for updating alerts"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AlertStatus] = None
    severity: Optional[SeverityLevel] = None
    tags: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "Acknowledged",
                "tags": ["cpu", "performance", "infrastructure", "escalated"]
            }
        }

class AlertResponse(BaseModel):
    """API response model for alerts"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Alert] = Field(None, description="Alert data")
    
class AlertListResponse(BaseModel):
    """API response model for alert lists"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: List[Alert] = Field(..., description="List of alerts")
    total: int = Field(..., description="Total number of alerts")
    
class AlertSearchRequest(BaseModel):
    """Request model for alert search"""
    query: Optional[str] = Field(None, description="Search query")
    severity: Optional[List[SeverityLevel]] = Field(None, description="Filter by severity")
    status: Optional[List[AlertStatus]] = Field(None, description="Filter by status")
    source_system: Optional[List[MonitoringSystem]] = Field(None, description="Filter by source system")
    service_name: Optional[str] = Field(None, description="Filter by service name")
    environment: Optional[str] = Field(None, description="Filter by environment")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    limit: int = Field(default=50, description="Maximum number of results")
    offset: int = Field(default=0, description="Offset for pagination")
    
class AlertSimilarityRequest(BaseModel):
    """Request model for finding similar alerts"""
    alert_id: str = Field(..., description="Alert ID to find similarities for")
    threshold: float = Field(default=0.8, description="Similarity threshold")
    limit: int = Field(default=10, description="Maximum number of similar alerts")

class AlertEmbedding(BaseModel):
    """Model for alert embeddings"""
    alert_id: str = Field(..., description="Alert ID")
    embedding: List[float] = Field(..., description="Alert embedding vector")
    metadata: Dict[str, Any] = Field(..., description="Alert metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
