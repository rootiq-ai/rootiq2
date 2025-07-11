"""
Alert group data models and schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

from models.alert import Alert, SeverityLevel, AlertStatus

class GroupStatus(str, Enum):
    """Group status"""
    ACTIVE = "Active"
    INVESTIGATING = "Investigating"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class GroupPriority(str, Enum):
    """Group priority based on aggregated alert severity"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class RCAStatus(str, Enum):
    """Root Cause Analysis status"""
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"

class AlertGroupBase(BaseModel):
    """Base alert group model"""
    title: str = Field(..., description="Group title/summary")
    description: str = Field(..., description="Group description")
    priority: GroupPriority = Field(..., description="Group priority")
    status: GroupStatus = Field(default=GroupStatus.ACTIVE, description="Group status")
    
    # Grouping metadata
    similarity_threshold: float = Field(..., description="Similarity threshold used for grouping")
    root_cause_hypothesis: Optional[str] = Field(None, description="Initial root cause hypothesis")
    
    # Tags and categorization
    tags: Optional[List[str]] = Field(default_factory=list, description="Group tags")
    category: Optional[str] = Field(None, description="Group category")
    
    @validator('tags', pre=True)
    def parse_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v or []

class AlertGroupCreate(AlertGroupBase):
    """Schema for creating new alert groups"""
    initial_alert_ids: List[str] = Field(..., description="Initial alert IDs to group")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "High CPU Usage Incidents",
                "description": "Multiple alerts related to high CPU usage across web servers",
                "priority": "High",
                "similarity_threshold": 0.85,
                "initial_alert_ids": ["alert-1", "alert-2", "alert-3"],
                "tags": ["cpu", "performance", "infrastructure"],
                "category": "Infrastructure"
            }
        }

class AlertGroup(AlertGroupBase):
    """Full alert group model with system fields"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique group ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Alert management
    alert_count: int = Field(default=0, description="Number of alerts in group")
    alert_ids: List[str] = Field(default_factory=list, description="List of alert IDs in group")
    
    # Severity aggregation
    max_severity: Optional[SeverityLevel] = Field(None, description="Highest severity in group")
    severity_distribution: Dict[str, int] = Field(default_factory=dict, description="Severity count distribution")
    
    # Time tracking
    first_alert_time: Optional[datetime] = Field(None, description="Timestamp of first alert in group")
    last_alert_time: Optional[datetime] = Field(None, description="Timestamp of last alert in group")
    duration_minutes: Optional[float] = Field(None, description="Duration of incident in minutes")
    
    # Root Cause Analysis
    rca_status: RCAStatus = Field(default=RCAStatus.PENDING, description="RCA status")
    rca_content: Optional[str] = Field(None, description="Generated RCA content")
    rca_confidence: Optional[float] = Field(None, description="RCA confidence score")
    rca_generated_at: Optional[datetime] = Field(None, description="RCA generation timestamp")
    
    # Impact assessment
    affected_services: List[str] = Field(default_factory=list, description="List of affected services")
    affected_hosts: List[str] = Field(default_factory=list, description="List of affected hosts")
    affected_environments: List[str] = Field(default_factory=list, description="List of affected environments")
    
    # Resolution tracking
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    assigned_to: Optional[str] = Field(None, description="Assigned team/person")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "group-123e4567-e89b-12d3-a456-426614174000",
                "title": "High CPU Usage Incidents",
                "description": "Multiple alerts related to high CPU usage across web servers",
                "priority": "High",
                "status": "Active",
                "similarity_threshold": 0.85,
                "alert_count": 5,
                "alert_ids": ["alert-1", "alert-2", "alert-3", "alert-4", "alert-5"],
                "max_severity": "High",
                "severity_distribution": {"High": 3, "Medium": 2},
                "first_alert_time": "2024-01-15T10:30:00Z",
                "last_alert_time": "2024-01-15T10:45:00Z",
                "duration_minutes": 15.0,
                "rca_status": "Completed",
                "affected_services": ["web-api", "user-service"],
                "affected_hosts": ["web-server-01", "web-server-02"],
                "affected_environments": ["production"],
                "tags": ["cpu", "performance", "infrastructure"],
                "category": "Infrastructure"
            }
        }

class AlertGroupUpdate(BaseModel):
    """Schema for updating alert groups"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[GroupStatus] = None
    priority: Optional[GroupPriority] = None
    root_cause_hypothesis: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    resolution_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "Investigating",
                "root_cause_hypothesis": "Memory leak in application causing high CPU usage",
                "assigned_to": "infrastructure-team"
            }
        }

class GroupResponse(BaseModel):
    """API response model for groups"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[AlertGroup] = Field(None, description="Group data")
    
class GroupListResponse(BaseModel):
    """API response model for group lists"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: List[AlertGroup] = Field(..., description="List of groups")
    total: int = Field(..., description="Total number of groups")

class GroupSearchRequest(BaseModel):
    """Request model for group search"""
    query: Optional[str] = Field(None, description="Search query")
    status: Optional[List[GroupStatus]] = Field(None, description="Filter by status")
    priority: Optional[List[GroupPriority]] = Field(None, description="Filter by priority")
    rca_status: Optional[List[RCAStatus]] = Field(None, description="Filter by RCA status")
    category: Optional[str] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    assigned_to: Optional[str] = Field(None, description="Filter by assignee")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    limit: int = Field(default=20, description="Maximum number of results")
    offset: int = Field(default=0, description="Offset for pagination")

class GroupStatistics(BaseModel):
    """Group statistics model"""
    total_groups: int = Field(..., description="Total number of groups")
    active_groups: int = Field(..., description="Number of active groups")
    resolved_groups: int = Field(..., description="Number of resolved groups")
    groups_with_rca: int = Field(..., description="Number of groups with completed RCA")
    average_resolution_time: Optional[float] = Field(None, description="Average resolution time in hours")
    priority_distribution: Dict[str, int] = Field(..., description="Priority distribution")
    status_distribution: Dict[str, int] = Field(..., description="Status distribution")
    
class RCARequest(BaseModel):
    """Request model for RCA generation"""
    group_id: str = Field(..., description="Group ID for RCA generation")
    force_regenerate: bool = Field(default=False, description="Force regenerate even if RCA exists")
    include_context: bool = Field(default=True, description="Include additional context from knowledge base")
    
class RCAResponse(BaseModel):
    """Response model for RCA generation"""
    success: bool = Field(..., description="Whether RCA generation was successful")
    message: str = Field(..., description="Response message")
    group_id: str = Field(..., description="Group ID")
    rca_content: Optional[str] = Field(None, description="Generated RCA content")
    confidence: Optional[float] = Field(None, description="RCA confidence score")
    generated_at: Optional[datetime] = Field(None, description="Generation timestamp")

class GroupWithAlerts(AlertGroup):
    """Group model with embedded alert details"""
    alerts: List[Alert] = Field(..., description="Full alert details for alerts in group")
    
class GroupMergeRequest(BaseModel):
    """Request model for merging groups"""
    source_group_ids: List[str] = Field(..., description="Source group IDs to merge")
    target_group_id: str = Field(..., description="Target group ID to merge into")
    merge_reason: Optional[str] = Field(None, description="Reason for merging")

class GroupSplitRequest(BaseModel):
    """Request model for splitting groups"""
    group_id: str = Field(..., description="Group ID to split")
    alert_ids_to_extract: List[str] = Field(..., description="Alert IDs to extract into new group")
    new_group_title: str = Field(..., description="Title for new group")
    split_reason: Optional[str] = Field(None, description="Reason for splitting")
