"""
API endpoints for alert management
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional
import logging
from datetime import datetime

from models.alert import (
    Alert, AlertCreate, AlertUpdate, AlertResponse, AlertListResponse,
    AlertSearchRequest, AlertSimilarityRequest, SeverityLevel, AlertStatus
)
from services.alert_grouper import get_alert_grouper
from services.vector_store import get_vector_store
from services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for demo purposes
# In production, use a proper database
alerts_storage: dict[str, Alert] = {}

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    background_tasks: BackgroundTasks
):
    """Create a new alert and process it for grouping"""
    try:
        # Create alert object
        alert = Alert(**alert_data.dict())
        
        # Store alert
        alerts_storage[alert.id] = alert
        
        # Process alert for grouping in background
        background_tasks.add_task(process_alert_for_grouping, alert)
        
        logger.info(f"Created alert: {alert.id}")
        
        return AlertResponse(
            success=True,
            message="Alert created successfully",
            data=alert
        )
        
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str):
    """Get alert by ID"""
    try:
        if alert_id not in alerts_storage:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = alerts_storage[alert_id]
        
        return AlertResponse(
            success=True,
            message="Alert retrieved successfully",
            data=alert
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: str, alert_update: AlertUpdate):
    """Update an existing alert"""
    try:
        if alert_id not in alerts_storage:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = alerts_storage[alert_id]
        
        # Update alert fields
        update_data = alert_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alert, field, value)
        
        alert.updated_at = datetime.utcnow()
        
        logger.info(f"Updated alert: {alert_id}")
        
        return AlertResponse(
            success=True,
            message="Alert updated successfully",
            data=alert
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert"""
    try:
        if alert_id not in alerts_storage:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Remove from storage
        del alerts_storage[alert_id]
        
        # Remove from vector store
        vector_store = await get_vector_store()
        await vector_store.remove_alert(alert_id)
        
        logger.info(f"Deleted alert: {alert_id}")
        
        return {"success": True, "message": "Alert deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    severity: Optional[List[SeverityLevel]] = Query(None),
    status: Optional[List[AlertStatus]] = Query(None),
    service_name: Optional[str] = Query(None),
    environment: Optional[str] = Query(None)
):
    """List alerts with optional filtering"""
    try:
        alerts = list(alerts_storage.values())
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity in severity]
        
        if status:
            alerts = [a for a in alerts if a.status in status]
        
        if service_name:
            alerts = [a for a in alerts if a.service_name == service_name]
        
        if environment:
            alerts = [a for a in alerts if a.environment == environment]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        total = len(alerts)
        alerts = alerts[offset:offset + limit]
        
        return AlertListResponse(
            success=True,
            message=f"Retrieved {len(alerts)} alerts",
            data=alerts,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=AlertListResponse)
async def search_alerts(search_request: AlertSearchRequest):
    """Search alerts with advanced filtering"""
    try:
        alerts = list(alerts_storage.values())
        
        # Apply text search if query provided
        if search_request.query:
            query_lower = search_request.query.lower()
            alerts = [
                a for a in alerts 
                if (query_lower in a.title.lower() or 
                    query_lower in a.description.lower() or
                    any(query_lower in tag.lower() for tag in a.tags))
            ]
        
        # Apply filters
        if search_request.severity:
            alerts = [a for a in alerts if a.severity in search_request.severity]
        
        if search_request.status:
            alerts = [a for a in alerts if a.status in search_request.status]
        
        if search_request.source_system:
            alerts = [a for a in alerts if a.source_system in search_request.source_system]
        
        if search_request.service_name:
            alerts = [a for a in alerts if a.service_name == search_request.service_name]
        
        if search_request.environment:
            alerts = [a for a in alerts if a.environment == search_request.environment]
        
        if search_request.tags:
            alerts = [
                a for a in alerts 
                if any(tag in a.tags for tag in search_request.tags)
            ]
        
        # Apply date filters
        if search_request.start_date:
            alerts = [a for a in alerts if a.timestamp >= search_request.start_date]
        
        if search_request.end_date:
            alerts = [a for a in alerts if a.timestamp <= search_request.end_date]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        total = len(alerts)
        alerts = alerts[search_request.offset:search_request.offset + search_request.limit]
        
        return AlertListResponse(
            success=True,
            message=f"Found {total} alerts matching criteria",
            data=alerts,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Failed to search alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/similar")
async def find_similar_alerts(alert_id: str, similarity_request: AlertSimilarityRequest):
    """Find alerts similar to the specified alert"""
    try:
        if alert_id not in alerts_storage:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Use the alert_id from the request if provided, otherwise use path parameter
        target_alert_id = similarity_request.alert_id if similarity_request.alert_id != alert_id else alert_id
        
        vector_store = await get_vector_store()
        similar_alerts = await vector_store.find_similar_by_id(
            target_alert_id,
            threshold=similarity_request.threshold,
            limit=similarity_request.limit
        )
        
        # Convert to response format
        similar_alert_data = []
        for similar_alert in similar_alerts:
            alert_id_similar = similar_alert["alert_id"]
            if alert_id_similar in alerts_storage:
                alert_data = alerts_storage[alert_id_similar]
                similar_alert_data.append({
                    "alert": alert_data,
                    "similarity_score": similar_alert["similarity"],
                    "distance": similar_alert["distance"]
                })
        
        return {
            "success": True,
            "message": f"Found {len(similar_alert_data)} similar alerts",
            "data": similar_alert_data,
            "target_alert_id": target_alert_id,
            "threshold": similarity_request.threshold
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find similar alerts for {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{alert_id}/group")
async def get_alert_group(alert_id: str):
    """Get the group that an alert belongs to"""
    try:
        if alert_id not in alerts_storage:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = alerts_storage[alert_id]
        
        if not alert.group_id:
            return {
                "success": True,
                "message": "Alert is not assigned to any group",
                "data": None
            }
        
        # Get group information from grouper
        alert_grouper = await get_alert_grouper()
        group = await alert_grouper.get_group(alert.group_id)
        
        if not group:
            return {
                "success": True,
                "message": "Alert group not found",
                "data": None
            }
        
        return {
            "success": True,
            "message": "Alert group retrieved successfully",
            "data": {
                "alert_id": alert_id,
                "group": group
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get group for alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{alert_id}/classify")
async def classify_alert(alert_id: str):
    """Classify an alert using AI"""
    try:
        if alert_id not in alerts_storage:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert = alerts_storage[alert_id]
        llm_service = await get_llm_service()
        
        # Generate AI-powered classification
        alert_text = f"{alert.title} {alert.description}"
        
        # Get category
        category = await llm_service.classify_alert_category(alert_text)
        
        # Get keywords
        keywords = await llm_service.extract_alert_keywords(alert_text)
        
        # Get summary
        summary = await llm_service.generate_alert_summary(alert_text)
        
        return {
            "success": True,
            "message": "Alert classified successfully",
            "data": {
                "alert_id": alert_id,
                "category": category,
                "keywords": keywords,
                "summary": summary
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to classify alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_alert_stats():
    """Get alert statistics summary"""
    try:
        alerts = list(alerts_storage.values())
        
        # Calculate statistics
        total_alerts = len(alerts)
        
        status_counts = {}
        severity_counts = {}
        source_counts = {}
        
        for alert in alerts:
            # Count by status
            status_counts[alert.status] = status_counts.get(alert.status, 0) + 1
            
            # Count by severity
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
            
            # Count by source
            source_counts[alert.source_system] = source_counts.get(alert.source_system, 0) + 1
        
        # Recent alerts (last 24 hours)
        now = datetime.utcnow()
        recent_alerts = [
            a for a in alerts 
            if (now - a.timestamp).total_seconds() < 86400
        ]
        
        return {
            "success": True,
            "message": "Alert statistics retrieved successfully",
            "data": {
                "total_alerts": total_alerts,
                "recent_alerts_24h": len(recent_alerts),
                "status_distribution": status_counts,
                "severity_distribution": severity_counts,
                "source_distribution": source_counts
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get alert stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for processing alerts
async def process_alert_for_grouping(alert: Alert):
    """Background task to process alert for grouping"""
    try:
        logger.info(f"Processing alert {alert.id} for grouping")
        
        alert_grouper = await get_alert_grouper()
        group_id = await alert_grouper.process_new_alert(alert)
        
        if group_id:
            alert.group_id = group_id
            alert.processed = True
            alert.embedding_generated = True
            alert.updated_at = datetime.utcnow()
            
            logger.info(f"Alert {alert.id} assigned to group {group_id}")
        else:
            logger.warning(f"Failed to assign alert {alert.id} to any group")
            
    except Exception as e:
        logger.error(f"Failed to process alert {alert.id} for grouping: {e}")
