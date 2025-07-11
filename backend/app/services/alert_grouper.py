"""
Alert Grouper Service - AI-powered alert grouping based on similarity
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import uuid
from collections import defaultdict

from models.alert import Alert, AlertStatus
from models.group import AlertGroup, GroupStatus, GroupPriority, SeverityLevel
from services.vector_store import get_vector_store
from services.llm_service import get_llm_service
from core.config import settings

logger = logging.getLogger(__name__)

class AlertGrouper:
    """AI-powered alert grouping service"""
    
    def __init__(self):
        self.vector_store = None
        self.llm_service = None
        self.active_groups: Dict[str, AlertGroup] = {}
        self.alert_to_group_mapping: Dict[str, str] = {}
        
    async def initialize(self):
        """Initialize the alert grouper"""
        try:
            self.vector_store = await get_vector_store()
            self.llm_service = await get_llm_service()
            logger.info("Alert grouper initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize alert grouper: {e}")
            raise
    
    async def process_new_alert(self, alert: Alert) -> Optional[str]:
        """Process a new alert and assign it to a group"""
        try:
            logger.info(f"Processing new alert: {alert.id}")
            
            # Add alert to vector store
            await self.vector_store.add_alert(alert)
            
            # Find similar alerts
            similar_alerts = await self.vector_store.find_similar_alerts(
                alert, 
                threshold=settings.SIMILARITY_THRESHOLD,
                limit=20
            )
            
            if similar_alerts:
                # Check if any similar alerts belong to existing groups
                candidate_groups = await self._find_candidate_groups(similar_alerts)
                
                if candidate_groups:
                    # Select the best group to join
                    target_group_id = await self._select_best_group(alert, candidate_groups)
                    if target_group_id:
                        await self._add_alert_to_group(alert, target_group_id)
                        return target_group_id
            
            # No suitable group found, create a new one
            group_id = await self._create_new_group(alert, similar_alerts)
            return group_id
            
        except Exception as e:
            logger.error(f"Failed to process alert {alert.id}: {e}")
            return None
    
    async def _find_candidate_groups(self, similar_alerts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Find candidate groups from similar alerts"""
        candidate_groups = defaultdict(list)
        
        for similar_alert in similar_alerts:
            alert_id = similar_alert["alert_id"]
            
            # Check if this alert belongs to an existing group
            if alert_id in self.alert_to_group_mapping:
                group_id = self.alert_to_group_mapping[alert_id]
                candidate_groups[group_id].append(similar_alert)
        
        return dict(candidate_groups)
    
    async def _select_best_group(self, alert: Alert, candidate_groups: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
        """Select the best group for the alert"""
        try:
            best_group_id = None
            best_score = 0.0
            
            for group_id, similar_alerts in candidate_groups.items():
                if group_id not in self.active_groups:
                    continue
                
                group = self.active_groups[group_id]
                
                # Skip if group is at max capacity
                if group.alert_count >= settings.MAX_GROUP_SIZE:
                    continue
                
                # Skip if group is resolved/closed
                if group.status in [GroupStatus.RESOLVED, GroupStatus.CLOSED]:
                    continue
                
                # Calculate group compatibility score
                score = await self._calculate_group_compatibility(alert, group, similar_alerts)
                
                if score > best_score:
                    best_score = score
                    best_group_id = group_id
            
            # Only assign to group if score is above threshold
            if best_score >= settings.SIMILARITY_THRESHOLD:
                return best_group_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to select best group: {e}")
            return None
    
    async def _calculate_group_compatibility(self, alert: Alert, group: AlertGroup, similar_alerts: List[Dict[str, Any]]) -> float:
        """Calculate compatibility score between alert and group"""
        try:
            # Base similarity score (average of similar alerts)
            similarity_scores = [sa["similarity"] for sa in similar_alerts]
            avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            
            # Time proximity factor (alerts closer in time are more likely related)
            time_factor = self._calculate_time_proximity_factor(alert, group)
            
            # Service/host affinity factor
            service_factor = self._calculate_service_affinity_factor(alert, group)
            
            # Severity compatibility factor
            severity_factor = self._calculate_severity_compatibility_factor(alert, group)
            
            # Environment factor
            env_factor = self._calculate_environment_factor(alert, group)
            
            # Weighted combination
            compatibility_score = (
                avg_similarity * 0.4 +
                time_factor * 0.2 +
                service_factor * 0.2 +
                severity_factor * 0.1 +
                env_factor * 0.1
            )
            
            return min(1.0, max(0.0, compatibility_score))
            
        except Exception as e:
            logger.error(f"Failed to calculate group compatibility: {e}")
            return 0.0
    
    def _calculate_time_proximity_factor(self, alert: Alert, group: AlertGroup) -> float:
        """Calculate time proximity factor"""
        try:
            if not group.last_alert_time:
                return 1.0
            
            time_diff = abs((alert.timestamp - group.last_alert_time).total_seconds())
            
            # Full score for alerts within 1 hour
            if time_diff <= 3600:
                return 1.0
            # Linearly decrease for alerts up to 24 hours apart
            elif time_diff <= 86400:
                return 1.0 - (time_diff - 3600) / (86400 - 3600)
            else:
                return 0.1  # Minimum score for very old alerts
                
        except Exception as e:
            logger.error(f"Failed to calculate time proximity: {e}")
            return 0.5
    
    def _calculate_service_affinity_factor(self, alert: Alert, group: AlertGroup) -> float:
        """Calculate service affinity factor"""
        try:
            # Same service gets high score
            if alert.service_name and alert.service_name in group.affected_services:
                return 1.0
            
            # Same host gets medium score
            if alert.host_name and alert.host_name in group.affected_hosts:
                return 0.8
            
            # Different but related services get lower score
            return 0.3
            
        except Exception as e:
            logger.error(f"Failed to calculate service affinity: {e}")
            return 0.5
    
    def _calculate_severity_compatibility_factor(self, alert: Alert, group: AlertGroup) -> float:
        """Calculate severity compatibility factor"""
        try:
            severity_hierarchy = {
                SeverityLevel.CRITICAL: 5,
                SeverityLevel.HIGH: 4,
                SeverityLevel.MEDIUM: 3,
                SeverityLevel.LOW: 2,
                SeverityLevel.INFO: 1
            }
            
            alert_severity = severity_hierarchy.get(alert.severity, 3)
            group_max_severity = severity_hierarchy.get(group.max_severity, 3)
            
            # Similar severities get higher scores
            severity_diff = abs(alert_severity - group_max_severity)
            
            if severity_diff == 0:
                return 1.0
            elif severity_diff == 1:
                return 0.8
            elif severity_diff == 2:
                return 0.6
            else:
                return 0.3
                
        except Exception as e:
            logger.error(f"Failed to calculate severity compatibility: {e}")
            return 0.5
    
    def _calculate_environment_factor(self, alert: Alert, group: AlertGroup) -> float:
        """Calculate environment factor"""
        try:
            if not alert.environment:
                return 0.5
            
            if alert.environment in group.affected_environments:
                return 1.0
            else:
                return 0.2
                
        except Exception as e:
            logger.error(f"Failed to calculate environment factor: {e}")
            return 0.5
    
    async def _add_alert_to_group(self, alert: Alert, group_id: str):
        """Add alert to existing group"""
        try:
            if group_id not in self.active_groups:
                logger.error(f"Group {group_id} not found")
                return
            
            group = self.active_groups[group_id]
            
            # Update group
            group.alert_ids.append(alert.id)
            group.alert_count += 1
            group.last_alert_time = alert.timestamp
            group.updated_at = datetime.utcnow()
            
            # Update severity tracking
            if not group.max_severity or self._is_higher_severity(alert.severity, group.max_severity):
                group.max_severity = alert.severity
            
            # Update severity distribution
            severity_str = str(alert.severity)
            group.severity_distribution[severity_str] = group.severity_distribution.get(severity_str, 0) + 1
            
            # Update affected resources
            if alert.service_name and alert.service_name not in group.affected_services:
                group.affected_services.append(alert.service_name)
            
            if alert.host_name and alert.host_name not in group.affected_hosts:
                group.affected_hosts.append(alert.host_name)
            
            if alert.environment and alert.environment not in group.affected_environments:
                group.affected_environments.append(alert.environment)
            
            # Update duration
            if group.first_alert_time:
                duration = (group.last_alert_time - group.first_alert_time).total_seconds() / 60
                group.duration_minutes = duration
            
            # Update alert mapping
            self.alert_to_group_mapping[alert.id] = group_id
            
            # Update alert with group ID
            alert.group_id = group_id
            
            logger.info(f"Added alert {alert.id} to group {group_id}")
            
        except Exception as e:
            logger.error(f"Failed to add alert {alert.id} to group {group_id}: {e}")
    
    async def _create_new_group(self, alert: Alert, similar_alerts: List[Dict[str, Any]]) -> str:
        """Create a new group for the alert"""
        try:
            group_id = str(uuid.uuid4())
            
            # Generate group title and description using AI
            group_title, group_description = await self._generate_group_metadata(alert, similar_alerts)
            
            # Determine group priority based on alert severity
            priority = self._determine_group_priority(alert.severity)
            
            # Create new group
            group = AlertGroup(
                id=group_id,
                title=group_title,
                description=group_description,
                priority=priority,
                status=GroupStatus.ACTIVE,
                similarity_threshold=settings.SIMILARITY_THRESHOLD,
                alert_count=1,
                alert_ids=[alert.id],
                max_severity=alert.severity,
                severity_distribution={str(alert.severity): 1},
                first_alert_time=alert.timestamp,
                last_alert_time=alert.timestamp,
                duration_minutes=0.0,
                affected_services=[alert.service_name] if alert.service_name else [],
                affected_hosts=[alert.host_name] if alert.host_name else [],
                affected_environments=[alert.environment] if alert.environment else [],
                tags=alert.tags.copy() if alert.tags else [],
                category=await self.llm_service.classify_alert_category(
                    f"{alert.title} {alert.description}"
                ) if self.llm_service else "Other"
            )
            
            # Store group
            self.active_groups[group_id] = group
            self.alert_to_group_mapping[alert.id] = group_id
            
            # Update alert with group ID
            alert.group_id = group_id
            
            logger.info(f"Created new group {group_id} for alert {alert.id}")
            
            return group_id
            
        except Exception as e:
            logger.error(f"Failed to create new group for alert {alert.id}: {e}")
            return str(uuid.uuid4())  # Return a basic group ID on failure
    
    async def _generate_group_metadata(self, alert: Alert, similar_alerts: List[Dict[str, Any]]) -> tuple[str, str]:
        """Generate group title and description using AI"""
        try:
            if not self.llm_service or not similar_alerts:
                # Fallback to basic title/description
                return f"Alert Group - {alert.title}", f"Group containing alerts similar to: {alert.title}"
            
            # Prepare context for AI
            alert_summaries = [alert.title]
            for similar_alert in similar_alerts[:5]:  # Limit to top 5 similar alerts
                metadata = similar_alert.get("metadata", {})
                if metadata.get("title"):
                    alert_summaries.append(metadata["title"])
            
            context = "\n".join([f"- {summary}" for summary in alert_summaries])
            
            # Generate title
            title_prompt = f"""
            Based on these related alerts, create a concise group title (max 60 characters):
            {context}
            
            Group title:
            """
            
            title = await self.llm_service.generate_text(
                title_prompt,
                "You are an expert system administrator creating alert group titles.",
                max_tokens=20
            )
            
            # Generate description
            desc_prompt = f"""
            Based on these related alerts, create a brief group description (max 200 characters):
            {context}
            
            Group description:
            """
            
            description = await self.llm_service.generate_text(
                desc_prompt,
                "You are an expert system administrator creating alert group descriptions.",
                max_tokens=50
            )
            
            return title.strip()[:60], description.strip()[:200]
            
        except Exception as e:
            logger.error(f"Failed to generate group metadata: {e}")
            return f"Alert Group - {alert.title}"[:60], f"Group containing alerts similar to: {alert.title}"[:200]
    
    def _determine_group_priority(self, severity: SeverityLevel) -> GroupPriority:
        """Determine group priority based on alert severity"""
        severity_to_priority = {
            SeverityLevel.CRITICAL: GroupPriority.CRITICAL,
            SeverityLevel.HIGH: GroupPriority.HIGH,
            SeverityLevel.MEDIUM: GroupPriority.MEDIUM,
            SeverityLevel.LOW: GroupPriority.LOW,
            SeverityLevel.INFO: GroupPriority.LOW
        }
        
        return severity_to_priority.get(severity, GroupPriority.MEDIUM)
    
    def _is_higher_severity(self, severity1: SeverityLevel, severity2: SeverityLevel) -> bool:
        """Check if severity1 is higher than severity2"""
        severity_order = {
            SeverityLevel.INFO: 1,
            SeverityLevel.LOW: 2,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.HIGH: 4,
            SeverityLevel.CRITICAL: 5
        }
        
        return severity_order.get(severity1, 3) > severity_order.get(severity2, 3)
    
    async def get_group(self, group_id: str) -> Optional[AlertGroup]:
        """Get group by ID"""
        return self.active_groups.get(group_id)
    
    async def get_all_groups(self) -> List[AlertGroup]:
        """Get all active groups"""
        return list(self.active_groups.values())
    
    async def update_group_status(self, group_id: str, status: GroupStatus) -> bool:
        """Update group status"""
        try:
            if group_id in self.active_groups:
                group = self.active_groups[group_id]
                group.status = status
                group.updated_at = datetime.utcnow()
                
                if status == GroupStatus.RESOLVED:
                    group.resolved_at = datetime.utcnow()
                
                logger.info(f"Updated group {group_id} status to {status}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update group status: {e}")
            return False
    
    async def merge_groups(self, source_group_ids: List[str], target_group_id: str) -> bool:
        """Merge multiple groups into one"""
        try:
            if target_group_id not in self.active_groups:
                logger.error(f"Target group {target_group_id} not found")
                return False
            
            target_group = self.active_groups[target_group_id]
            
            for source_group_id in source_group_ids:
                if source_group_id not in self.active_groups:
                    continue
                
                source_group = self.active_groups[source_group_id]
                
                # Merge alert IDs
                target_group.alert_ids.extend(source_group.alert_ids)
                target_group.alert_count += source_group.alert_count
                
                # Update mappings
                for alert_id in source_group.alert_ids:
                    self.alert_to_group_mapping[alert_id] = target_group_id
                
                # Merge other metadata
                target_group.affected_services.extend(
                    [s for s in source_group.affected_services if s not in target_group.affected_services]
                )
                target_group.affected_hosts.extend(
                    [h for h in source_group.affected_hosts if h not in target_group.affected_hosts]
                )
                target_group.affected_environments.extend(
                    [e for e in source_group.affected_environments if e not in target_group.affected_environments]
                )
                
                # Update severity distribution
                for severity, count in source_group.severity_distribution.items():
                    target_group.severity_distribution[severity] = (
                        target_group.severity_distribution.get(severity, 0) + count
                    )
                
                # Remove source group
                del self.active_groups[source_group_id]
            
            target_group.updated_at = datetime.utcnow()
            
            logger.info(f"Merged {len(source_group_ids)} groups into {target_group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to merge groups: {e}")
            return False

# Global alert grouper instance
alert_grouper = AlertGrouper()

async def get_alert_grouper() -> AlertGrouper:
    """Get alert grouper instance"""
    if alert_grouper.vector_store is None:
        await alert_grouper.initialize()
    return alert_grouper
