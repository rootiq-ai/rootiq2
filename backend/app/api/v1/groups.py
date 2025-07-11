"""
API endpoints for alert group management
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional
import logging
from datetime import datetime

from models.group import (
    AlertGroup, AlertGroupCreate, AlertGroupUpdate, GroupResponse, GroupListResponse,
    GroupSearchRequest, GroupStatistics, RCARequest, RCAResponse, GroupWithAlerts,
    GroupStatus, GroupPriority, RCAStatus
)
from models.alert import Alert
from services.alert_grouper import get_alert_grouper
from services.rca_generator import get_rca_generator

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=GroupListResponse)
async def list_groups(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[List[GroupStatus]] = Query(None),
    priority: Optional[List[GroupPriority]] = Query(None),
    rca_status: Optional[List[RCAStatus]] = Query(None)
):
    """List alert groups with optional filtering"""
    try:
        alert_grouper = await get_alert_grouper()
        all_groups = await alert_grouper.get_all_groups()
        
        # Apply filters
        filtered_groups = all_groups
        
        if status:
            filtered_groups = [g for g in filtered_groups if g.status in status]
        
        if priority:
            filtered_groups = [g for g in filtered_groups if g.priority in priority]
        
        if rca_status:
            filtered_groups = [g for g in filtered_groups if g.rca_status in rca_status]
        
        # Sort by created_at (newest first)
        filtered_groups.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total = len(filtered_groups)
        paginated_groups = filtered_groups[offset:offset + limit]
        
        return GroupListResponse(
            success=True,
            message=f"Retrieved {len(paginated_groups)} groups",
            data=paginated_groups,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Failed to list groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: str):
    """Get group by ID"""
    try:
        alert_grouper = await get_alert_grouper()
        group = await alert_grouper.get_group(group_id)
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        return GroupResponse(
            success=True,
            message="Group retrieved successfully",
            data=group
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/with-alerts")
async def get_group_with_alerts(group_id: str):
    """Get group with full alert details"""
    try:
        alert_grouper = await get_alert_grouper()
        group = await alert_grouper.get_group(group_id)
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Get alert details from storage (import here to avoid circular import)
        from api.v1.alerts import alerts_storage
        
        alerts = []
        for alert_id in group.alert_ids:
            if alert_id in alerts_storage:
                alerts.append(alerts_storage[alert_id])
        
        group_with_alerts = GroupWithAlerts(
            **group.dict(),
            alerts=alerts
        )
        
        return {
            "success": True,
            "message": "Group with alerts retrieved successfully",
            "data": group_with_alerts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get group with alerts {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: str, group_update: AlertGroupUpdate):
    """Update an existing group"""
    try:
        alert_grouper = await get_alert_grouper()
        group = await alert_grouper.get_group(group_id)
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Update group fields
        update_data = group_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(group, field, value)
        
        group.updated_at = datetime.utcnow()
        
        # Update status if provided
        if group_update.status:
            await alert_grouper.update_group_status(group_id, group_update.status)
        
        logger.info(f"Updated group: {group_id}")
        
        return GroupResponse(
            success=True,
            message="Group updated successfully",
            data=group
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=GroupListResponse)
async def search_groups(search_request: GroupSearchRequest):
    """Search groups with advanced filtering"""
    try:
        alert_grouper = await get_alert_grouper()
        all_groups = await alert_grouper.get_all_groups()
        
        # Apply text search if query provided
        filtered_groups = all_groups
        if search_request.query:
            query_lower = search_request.query.lower()
            filtered_groups = [
                g for g in filtered_groups 
                if (query_lower in g.title.lower() or 
                    query_lower in g.description.lower() or
                    any(query_lower in tag.lower() for tag in g.tags))
            ]
        
        # Apply filters
        if search_request.status:
            filtered_groups = [g for g in filtered_groups if g.status in search_request.status]
        
        if search_request.priority:
            filtered_groups = [g for g in filtered_groups if g.priority in search_request.priority]
        
        if search_request.rca_status:
            filtered_groups = [g for g in filtered_groups if g.rca_status in search_request.rca_status]
        
        if search_request.category:
            filtered_groups = [g for g in filtered_groups if g.category == search_request.category]
        
        if search_request.assigned_to:
            filtered_groups = [g for g in filtered_groups if g.assigned_to == search_request.assigned_to]
        
        if search_request.tags:
            filtered_groups = [
                g for g in filtered_groups 
                if any(tag in g.tags for tag in search_request.tags)
            ]
        
        # Apply date filters
        if search_request.start_date:
            filtered_groups = [g for g in filtered_groups if g.created_at >= search_request.start_date]
        
        if search_request.end_date:
            filtered_groups = [g for g in filtered_groups if g.created_at <= search_request.end_date]
        
        # Sort by created_at (newest first)
        filtered_groups.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total = len(filtered_groups)
        paginated_groups = filtered_groups[search_request.offset:search_request.offset + search_request.limit]
        
        return GroupListResponse(
            success=True,
            message=f"Found {total} groups matching criteria",
            data=paginated_groups,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Failed to search groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/rca", response_model=RCAResponse)
async def generate_rca(
    group_id: str, 
    rca_request: RCARequest,
    background_tasks: BackgroundTasks
):
    """Generate Root Cause Analysis for a group"""
    try:
        alert_grouper = await get_alert_grouper()
        group = await alert_grouper.get_group(group_id)
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Check if RCA already exists and force_regenerate is False
        if group.rca_content and not rca_request.force_regenerate:
            return RCAResponse(
                success=True,
                message="RCA already exists",
                group_id=group_id,
                rca_content=group.rca_content,
                confidence=group.rca_confidence,
                generated_at=group.rca_generated_at
            )
        
        # Start RCA generation in background
        background_tasks.add_task(generate_rca_background, group_id, rca_request.include_context)
        
        return RCAResponse(
            success=True,
            message="RCA generation started",
            group_id=group_id,
            rca_content=None,
            confidence=None,
            generated_at=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start RCA generation for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/rca")
async def get_rca(group_id: str):
    """Get RCA for a group"""
    try:
        alert_grouper = await get_alert_grouper()
        group = await alert_grouper.get_group(group_id)
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        if not group.rca_content:
            return {
                "success": True,
                "message": "No RCA available for this group",
                "data": {
                    "group_id": group_id,
                    "rca_status": group.rca_status,
                    "rca_content": None,
                    "confidence": None,
                    "generated_at": None
                }
            }
        
        return {
            "success": True,
            "message": "RCA retrieved successfully",
            "data": {
                "group_id": group_id,
                "rca_status": group.rca_status,
                "rca_content": group.rca_content,
                "confidence": group.rca_confidence,
                "generated_at": group.rca_generated_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get RCA for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{group_id}/resolve")
async def resolve_group(group_id: str, resolution_notes: Optional[str] = None):
    """Mark a group as resolved"""
    try:
        alert_grouper = await get_alert_grouper()
        group = await alert_grouper.get_group(group_id)
        
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Update group status
        success = await alert_grouper.update_group_status(group_id, GroupStatus.RESOLVED)
        
        if success and resolution_notes:
            group.resolution_notes = resolution_notes
            group.resolved_at = datetime.utcnow()
            
            # Update RCA with resolution if available
            if group.rca_content:
                rca_generator = await get_rca_generator()
                await rca_generator.update_rca_with_resolution(group, resolution_notes)
        
        return {
            "success": success,
            "message": "Group resolved successfully" if success else "Failed to resolve group",
            "data": {
                "group_id": group_id,
                "status": GroupStatus.RESOLVED,
                "resolved_at": group.resolved_at,
                "resolution_notes": resolution_notes
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_group_stats():
    """Get group statistics summary"""
    try:
        alert_grouper = await get_alert_grouper()
        all_groups = await alert_grouper.get_all_groups()
        
        # Calculate statistics
        total_groups = len(all_groups)
        
        status_counts = {}
        priority_counts = {}
        rca_status_counts = {}
        
        active_groups = 0
        resolved_groups = 0
        groups_with_rca = 0
        total_resolution_time = 0
        resolved_count = 0
        
        for group in all_groups:
            # Count by status
            status_counts[group.status] = status_counts.get(group.status, 0) + 1
            
            # Count by priority
            priority_counts[group.priority] = priority_counts.get(group.priority, 0) + 1
            
            # Count by RCA status
            rca_status_counts[group.rca_status] = rca_status_counts.get(group.rca_status, 0) + 1
            
            # Active/resolved counts
            if group.status == GroupStatus.ACTIVE:
                active_groups += 1
            elif group.status == GroupStatus.RESOLVED:
                resolved_groups += 1
                
                # Calculate resolution time
                if group.resolved_at and group.created_at:
                    resolution_time = (group.resolved_at - group.created_at).total_seconds() / 3600  # in hours
                    total_resolution_time += resolution_time
                    resolved_count += 1
            
            # RCA completion
            if group.rca_status == RCAStatus.COMPLETED:
                groups_with_rca += 1
        
        # Calculate average resolution time
        avg_resolution_time = None
        if resolved_count > 0:
            avg_resolution_time = total_resolution_time / resolved_count
        
        statistics = GroupStatistics(
            total_groups=total_groups,
            active_groups=active_groups,
            resolved_groups=resolved_groups,
            groups_with_rca=groups_with_rca,
            average_resolution_time=avg_resolution_time,
            priority_distribution=priority_counts,
            status_distribution=status_counts
        )
        
        return {
            "success": True,
            "message": "Group statistics retrieved successfully",
            "data": statistics
        }
        
    except Exception as e:
        logger.error(f"Failed to get group stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merge")
async def merge_groups(source_group_ids: List[str], target_group_id: str, merge_reason: Optional[str] = None):
    """Merge multiple groups into one"""
    try:
        alert_grouper = await get_alert_grouper()
        
        # Validate that all groups exist
        target_group = await alert_grouper.get_group(target_group_id)
        if not target_group:
            raise HTTPException(status_code=404, detail="Target group not found")
        
        for group_id in source_group_ids:
            group = await alert_grouper.get_group(group_id)
            if not group:
                raise HTTPException(status_code=404, detail=f"Source group {group_id} not found")
        
        # Perform merge
        success = await alert_grouper.merge_groups(source_group_ids, target_group_id)
        
        if success:
            logger.info(f"Merged groups {source_group_ids} into {target_group_id}")
        
        return {
            "success": success,
            "message": "Groups merged successfully" if success else "Failed to merge groups",
            "data": {
                "target_group_id": target_group_id,
                "merged_group_ids": source_group_ids,
                "merge_reason": merge_reason
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to merge groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for RCA generation
async def generate_rca_background(group_id: str, include_context: bool = True):
    """Background task to generate RCA"""
    try:
        logger.info(f"Starting RCA generation for group {group_id}")
        
        alert_grouper = await get_alert_grouper()
        group = await alert_grouper.get_group(group_id)
        
        if not group:
            logger.error(f"Group {group_id} not found for RCA generation")
            return
        
        # Get alerts from storage
        from api.v1.alerts import alerts_storage
        
        alerts = []
        for alert_id in group.alert_ids:
            if alert_id in alerts_storage:
                alerts.append(alerts_storage[alert_id])
        
        if not alerts:
            logger.warning(f"No alerts found for group {group_id}")
            return
        
        # Generate RCA
        rca_generator = await get_rca_generator()
        result = await rca_generator.generate_rca(group, alerts)
        
        if result["success"]:
            logger.info(f"RCA generated successfully for group {group_id}")
        else:
            logger.error(f"RCA generation failed for group {group_id}: {result['message']}")
            
    except Exception as e:
        logger.error(f"Background RCA generation failed for group {group_id}: {e}")
