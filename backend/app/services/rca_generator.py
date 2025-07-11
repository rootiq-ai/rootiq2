"""
Root Cause Analysis (RCA) Generator Service using RAG and LLM
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from models.alert import Alert
from models.group import AlertGroup, RCAStatus
from services.llm_service import get_llm_service
from services.vector_store import get_vector_store
from core.config import settings

logger = logging.getLogger(__name__)

class RCAGenerator:
    """AI-powered Root Cause Analysis generator using RAG"""
    
    def __init__(self):
        self.llm_service = None
        self.vector_store = None
        
    async def initialize(self):
        """Initialize the RCA generator"""
        try:
            self.llm_service = await get_llm_service()
            self.vector_store = await get_vector_store()
            logger.info("RCA generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RCA generator: {e}")
            raise
    
    async def generate_rca(self, group: AlertGroup, alerts: List[Alert], force_regenerate: bool = False) -> Dict[str, Any]:
        """Generate RCA for an alert group"""
        try:
            logger.info(f"Generating RCA for group {group.id}")
            
            # Check if RCA already exists and force_regenerate is False
            if group.rca_content and not force_regenerate:
                return {
                    "success": True,
                    "message": "RCA already exists",
                    "rca_content": group.rca_content,
                    "confidence": group.rca_confidence,
                    "generated_at": group.rca_generated_at
                }
            
            # Update group RCA status
            group.rca_status = RCAStatus.IN_PROGRESS
            
            # Gather context for RCA
            context = await self._gather_rca_context(group, alerts)
            
            # Generate RCA using LLM with RAG
            rca_content = await self._generate_rca_content(context)
            
            # Calculate confidence score
            confidence = await self._calculate_rca_confidence(context, rca_content)
            
            # Update group with RCA
            group.rca_content = rca_content
            group.rca_confidence = confidence
            group.rca_status = RCAStatus.COMPLETED
            group.rca_generated_at = datetime.utcnow()
            group.updated_at = datetime.utcnow()
            
            logger.info(f"Successfully generated RCA for group {group.id}")
            
            return {
                "success": True,
                "message": "RCA generated successfully",
                "rca_content": rca_content,
                "confidence": confidence,
                "generated_at": group.rca_generated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to generate RCA for group {group.id}: {e}")
            
            # Update group RCA status to failed
            group.rca_status = RCAStatus.FAILED
            group.updated_at = datetime.utcnow()
            
            return {
                "success": False,
                "message": f"RCA generation failed: {str(e)}",
                "rca_content": None,
                "confidence": None,
                "generated_at": None
            }
    
    async def _gather_rca_context(self, group: AlertGroup, alerts: List[Alert]) -> Dict[str, Any]:
        """Gather comprehensive context for RCA generation"""
        try:
            # Basic group information
            context = {
                "group_info": {
                    "id": group.id,
                    "title": group.title,
                    "description": group.description,
                    "priority": group.priority,
                    "category": group.category,
                    "affected_services": group.affected_services,
                    "affected_hosts": group.affected_hosts,
                    "affected_environments": group.affected_environments,
                    "duration_minutes": group.duration_minutes,
                    "alert_count": group.alert_count,
                    "severity_distribution": group.severity_distribution
                },
                "alerts": [],
                "timeline": [],
                "patterns": {},
                "similar_incidents": [],
                "knowledge_base": settings.RCA_KNOWLEDGE_BASE
            }
            
            # Alert details
            for alert in alerts:
                alert_info = {
                    "id": alert.id,
                    "title": alert.title,
                    "description": alert.description,
                    "severity": alert.severity,
                    "source_system": alert.source_system,
                    "service_name": alert.service_name,
                    "host_name": alert.host_name,
                    "environment": alert.environment,
                    "timestamp": alert.timestamp.isoformat(),
                    "tags": alert.tags,
                    "metrics": alert.metrics
                }
                context["alerts"].append(alert_info)
                
                # Build timeline
                context["timeline"].append({
                    "timestamp": alert.timestamp.isoformat(),
                    "event": f"Alert: {alert.title}",
                    "severity": alert.severity,
                    "source": alert.source_system
                })
            
            # Sort timeline by timestamp
            context["timeline"].sort(key=lambda x: x["timestamp"])
            
            # Analyze patterns
            context["patterns"] = await self._analyze_alert_patterns(alerts)
            
            # Find similar historical incidents using RAG
            context["similar_incidents"] = await self._find_similar_incidents(group, alerts)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to gather RCA context: {e}")
            return {"error": str(e)}
    
    async def _analyze_alert_patterns(self, alerts: List[Alert]) -> Dict[str, Any]:
        """Analyze patterns in the alerts"""
        try:
            patterns = {
                "services_affected": {},
                "hosts_affected": {},
                "error_keywords": {},
                "temporal_pattern": "sequential",  # could be: sequential, simultaneous, cascading
                "geographic_spread": [],
                "severity_progression": []
            }
            
            # Count affected services and hosts
            for alert in alerts:
                if alert.service_name:
                    patterns["services_affected"][alert.service_name] = (
                        patterns["services_affected"].get(alert.service_name, 0) + 1
                    )
                
                if alert.host_name:
                    patterns["hosts_affected"][alert.host_name] = (
                        patterns["hosts_affected"].get(alert.host_name, 0) + 1
                    )
                
                # Track severity progression
                patterns["severity_progression"].append({
                    "timestamp": alert.timestamp.isoformat(),
                    "severity": alert.severity
                })
            
            # Extract common keywords using LLM
            if self.llm_service:
                alert_texts = [f"{alert.title} {alert.description}" for alert in alerts]
                all_text = " | ".join(alert_texts)
                
                keywords = await self.llm_service.extract_alert_keywords(all_text)
                patterns["error_keywords"] = {kw: 1 for kw in keywords}
            
            # Analyze temporal pattern
            if len(alerts) > 1:
                timestamps = [alert.timestamp for alert in alerts]
                timestamps.sort()
                
                # Check if alerts occurred within a short time window (cascading)
                max_gap = max(
                    (timestamps[i+1] - timestamps[i]).total_seconds() 
                    for i in range(len(timestamps)-1)
                )
                
                if max_gap < 300:  # 5 minutes
                    patterns["temporal_pattern"] = "simultaneous"
                elif max_gap < 1800:  # 30 minutes
                    patterns["temporal_pattern"] = "cascading"
                else:
                    patterns["temporal_pattern"] = "sequential"
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze alert patterns: {e}")
            return {}
    
    async def _find_similar_incidents(self, group: AlertGroup, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Find similar historical incidents using vector search"""
        try:
            similar_incidents = []
            
            # Use the group description as query
            query_text = f"{group.title} {group.description}"
            
            # Get embedding for the query
            query_embedding = await self.llm_service.generate_embedding(query_text)
            
            # Search for similar alerts
            similar_alerts = await self.vector_store.db_manager.search_similar_alerts(
                query_embedding, 
                limit=20
            )
            
            # Group similar alerts by common characteristics
            incident_groups = {}
            
            for similar_alert in similar_alerts:
                metadata = similar_alert.get("metadata", {})
                
                # Skip alerts from the current group
                if metadata.get("alert_id") in group.alert_ids:
                    continue
                
                # Group by service or title similarity
                service_key = metadata.get("service_name", "unknown")
                title_key = metadata.get("title", "")[:50]  # First 50 chars
                
                group_key = f"{service_key}_{title_key}"
                
                if group_key not in incident_groups:
                    incident_groups[group_key] = {
                        "alerts": [],
                        "max_similarity": 0.0,
                        "common_service": service_key,
                        "pattern": title_key
                    }
                
                incident_groups[group_key]["alerts"].append(similar_alert)
                incident_groups[group_key]["max_similarity"] = max(
                    incident_groups[group_key]["max_similarity"],
                    similar_alert.get("similarity", 0.0)
                )
            
            # Convert to list and sort by similarity
            for group_key, incident_data in incident_groups.items():
                if len(incident_data["alerts"]) >= 1:  # At least 1 similar alert
                    similar_incidents.append({
                        "incident_id": group_key,
                        "alert_count": len(incident_data["alerts"]),
                        "max_similarity": incident_data["max_similarity"],
                        "common_service": incident_data["common_service"],
                        "pattern": incident_data["pattern"],
                        "sample_alerts": incident_data["alerts"][:3]  # First 3 alerts as examples
                    })
            
            # Sort by similarity and return top 5
            similar_incidents.sort(key=lambda x: x["max_similarity"], reverse=True)
            
            return similar_incidents[:5]
            
        except Exception as e:
            logger.error(f"Failed to find similar incidents: {e}")
            return []
    
    async def _generate_rca_content(self, context: Dict[str, Any]) -> str:
        """Generate RCA content using LLM with RAG context"""
        try:
            # Prepare the prompt with context
            prompt = self._build_rca_prompt(context)
            
            # System prompt for RCA generation
            system_prompt = """
            You are an expert Site Reliability Engineer and incident response specialist. 
            Generate a comprehensive Root Cause Analysis (RCA) based on the provided alert data and context.
            
            Structure your RCA as follows:
            1. **Executive Summary** - Brief overview of the incident
            2. **Timeline** - Chronological sequence of events
            3. **Root Cause** - Primary cause of the incident
            4. **Contributing Factors** - Secondary factors that contributed
            5. **Impact Analysis** - What was affected and how
            6. **Resolution Steps** - What was done to resolve (if resolved)
            7. **Preventive Measures** - Recommendations to prevent recurrence
            8. **Lessons Learned** - Key takeaways
            
            Be specific, technical, and actionable. Use the provided similar incidents and knowledge base to inform your analysis.
            """
            
            # Generate RCA content
            rca_content = await self.llm_service.generate_text(
                prompt,
                system_prompt,
                max_tokens=settings.RCA_MAX_TOKENS
            )
            
            return rca_content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate RCA content: {e}")
            return f"RCA generation failed due to technical error: {str(e)}"
    
    def _build_rca_prompt(self, context: Dict[str, Any]) -> str:
        """Build the RCA generation prompt with context"""
        try:
            prompt_parts = []
            
            # Group information
            group_info = context.get("group_info", {})
            prompt_parts.append(f"""
            **Incident Overview:**
            - Group ID: {group_info.get('id', 'Unknown')}
            - Title: {group_info.get('title', 'Unknown')}
            - Description: {group_info.get('description', 'Unknown')}
            - Priority: {group_info.get('priority', 'Unknown')}
            - Category: {group_info.get('category', 'Unknown')}
            - Duration: {group_info.get('duration_minutes', 0)} minutes
            - Total Alerts: {group_info.get('alert_count', 0)}
            - Affected Services: {', '.join(group_info.get('affected_services', []))}
            - Affected Hosts: {', '.join(group_info.get('affected_hosts', []))}
            - Environments: {', '.join(group_info.get('affected_environments', []))}
            """)
            
            # Alert details
            alerts = context.get("alerts", [])
            if alerts:
                prompt_parts.append("\n**Alert Details:**")
                for i, alert in enumerate(alerts[:10], 1):  # Limit to 10 alerts
                    prompt_parts.append(f"""
                    Alert {i}:
                    - Title: {alert.get('title', 'Unknown')}
                    - Description: {alert.get('description', 'Unknown')}
                    - Severity: {alert.get('severity', 'Unknown')}
                    - Source: {alert.get('source_system', 'Unknown')}
                    - Service: {alert.get('service_name', 'N/A')}
                    - Host: {alert.get('host_name', 'N/A')}
                    - Timestamp: {alert.get('timestamp', 'Unknown')}
                    - Metrics: {json.dumps(alert.get('metrics', {}), indent=2) if alert.get('metrics') else 'None'}
                    """)
            
            # Timeline
            timeline = context.get("timeline", [])
            if timeline:
                prompt_parts.append("\n**Event Timeline:**")
                for event in timeline[:20]:  # Limit to 20 events
                    prompt_parts.append(f"- {event.get('timestamp', 'Unknown')}: {event.get('event', 'Unknown')} ({event.get('severity', 'Unknown')})")
            
            # Patterns
            patterns = context.get("patterns", {})
            if patterns:
                prompt_parts.append(f"\n**Observed Patterns:**")
                prompt_parts.append(f"- Temporal Pattern: {patterns.get('temporal_pattern', 'Unknown')}")
                prompt_parts.append(f"- Services Affected: {json.dumps(patterns.get('services_affected', {}), indent=2)}")
                prompt_parts.append(f"- Hosts Affected: {json.dumps(patterns.get('hosts_affected', {}), indent=2)}")
                
                if patterns.get('error_keywords'):
                    prompt_parts.append(f"- Key Error Terms: {', '.join(patterns.get('error_keywords', {}).keys())}")
            
            # Similar incidents
            similar_incidents = context.get("similar_incidents", [])
            if similar_incidents:
                prompt_parts.append("\n**Similar Historical Incidents:**")
                for incident in similar_incidents[:3]:  # Top 3 similar incidents
                    prompt_parts.append(f"""
                    - Pattern: {incident.get('pattern', 'Unknown')} (Similarity: {incident.get('max_similarity', 0):.2f})
                    - Service: {incident.get('common_service', 'Unknown')}
                    - Alert Count: {incident.get('alert_count', 0)}
                    """)
            
            # Knowledge base context
            knowledge_base = context.get("knowledge_base", "")
            if knowledge_base:
                prompt_parts.append(f"\n**Knowledge Base Reference:**\n{knowledge_base}")
            
            prompt_parts.append("\n**Please generate a comprehensive RCA based on the above information:**")
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Failed to build RCA prompt: {e}")
            return "Unable to build comprehensive prompt due to data processing error."
    
    async def _calculate_rca_confidence(self, context: Dict[str, Any], rca_content: str) -> float:
        """Calculate confidence score for the generated RCA"""
        try:
            confidence_factors = []
            
            # Factor 1: Amount of available data
            alert_count = len(context.get("alerts", []))
            if alert_count >= 5:
                confidence_factors.append(0.9)
            elif alert_count >= 3:
                confidence_factors.append(0.7)
            elif alert_count >= 1:
                confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.2)
            
            # Factor 2: Quality of patterns detected
            patterns = context.get("patterns", {})
            if patterns.get("services_affected") and patterns.get("temporal_pattern"):
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.4)
            
            # Factor 3: Availability of similar incidents
            similar_incidents = context.get("similar_incidents", [])
            if similar_incidents:
                max_similarity = max(incident.get("max_similarity", 0) for incident in similar_incidents)
                confidence_factors.append(max_similarity)
            else:
                confidence_factors.append(0.3)
            
            # Factor 4: RCA content length and structure (basic heuristic)
            if len(rca_content) > 1000 and "Root Cause" in rca_content:
                confidence_factors.append(0.8)
            elif len(rca_content) > 500:
                confidence_factors.append(0.6)
            else:
                confidence_factors.append(0.4)
            
            # Calculate weighted average
            confidence = sum(confidence_factors) / len(confidence_factors)
            
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"Failed to calculate RCA confidence: {e}")
            return 0.5
    
    async def update_rca_with_resolution(self, group: AlertGroup, resolution_notes: str) -> bool:
        """Update RCA with resolution information"""
        try:
            if not group.rca_content:
                logger.warning(f"No RCA content found for group {group.id}")
                return False
            
            # Generate resolution update using LLM
            system_prompt = """
            You are updating an existing RCA with resolution information. 
            Append a "Resolution Update" section to the existing RCA with the provided resolution notes.
            Keep the update concise and professional.
            """
            
            prompt = f"""
            Existing RCA:
            {group.rca_content}
            
            Resolution Notes:
            {resolution_notes}
            
            Please add a resolution update section:
            """
            
            updated_rca = await self.llm_service.generate_text(
                prompt,
                system_prompt,
                max_tokens=500
            )
            
            group.rca_content = updated_rca.strip()
            group.updated_at = datetime.utcnow()
            
            logger.info(f"Updated RCA for group {group.id} with resolution information")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update RCA with resolution: {e}")
            return False

# Global RCA generator instance
rca_generator = RCAGenerator()

async def get_rca_generator() -> RCAGenerator:
    """Get RCA generator instance"""
    if rca_generator.llm_service is None:
        await rca_generator.initialize()
    return rca_generator
