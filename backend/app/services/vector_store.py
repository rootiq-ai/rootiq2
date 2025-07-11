"""
Vector Store Service for alert embeddings and similarity search
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime

from core.database import db_manager
from services.llm_service import get_llm_service
from models.alert import Alert
from core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store service for alert embeddings"""
    
    def __init__(self):
        self.llm_service = None
        self.db_manager = db_manager
        
    async def initialize(self):
        """Initialize the vector store"""
        try:
            self.llm_service = await get_llm_service()
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def add_alert(self, alert: Alert) -> bool:
        """Add alert to vector store"""
        try:
            # Generate alert text for embedding
            alert_text = self._create_alert_text(alert)
            
            # Generate embedding
            embedding = await self.llm_service.generate_embedding(alert_text)
            
            # Prepare metadata
            metadata = {
                "alert_id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "severity": alert.severity,
                "source_system": alert.source_system,
                "service_name": alert.service_name or "",
                "host_name": alert.host_name or "",
                "environment": alert.environment or "",
                "status": alert.status,
                "timestamp": alert.timestamp.isoformat(),
                "tags": alert.tags,
                "summary": alert_text[:500]  # First 500 chars as summary
            }
            
            # Add to database
            await self.db_manager.add_alert_embedding(alert.id, embedding, metadata)
            
            logger.info(f"Added alert {alert.id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add alert {alert.id} to vector store: {e}")
            return False
    
    async def find_similar_alerts(self, alert: Alert, threshold: float = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar alerts for the given alert"""
        try:
            if threshold is None:
                threshold = settings.SIMILARITY_THRESHOLD
            
            # Generate alert text for embedding
            alert_text = self._create_alert_text(alert)
            
            # Generate embedding
            query_embedding = await self.llm_service.generate_embedding(alert_text)
            
            # Search for similar alerts
            similar_alerts = await self.db_manager.search_similar_alerts(query_embedding, limit + 1)  # +1 to account for self
            
            # Filter out the alert itself and apply threshold
            filtered_alerts = []
            for similar_alert in similar_alerts:
                if (similar_alert["alert_id"] != alert.id and 
                    similar_alert["similarity"] >= threshold):
                    filtered_alerts.append(similar_alert)
            
            return filtered_alerts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar alerts for {alert.id}: {e}")
            return []
    
    async def find_similar_by_id(self, alert_id: str, threshold: float = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar alerts by alert ID"""
        try:
            if threshold is None:
                threshold = settings.SIMILARITY_THRESHOLD
            
            # Get alert from database
            alert_data = await self.db_manager.get_alert_by_id(alert_id)
            if not alert_data:
                logger.warning(f"Alert {alert_id} not found in vector store")
                return []
            
            # Get the alert's embedding by searching for it
            alert_metadata = alert_data["metadata"]
            alert_text = alert_metadata.get("summary", "")
            
            if not alert_text:
                logger.warning(f"No summary found for alert {alert_id}")
                return []
            
            # Generate embedding for search
            query_embedding = await self.llm_service.generate_embedding(alert_text)
            
            # Search for similar alerts
            similar_alerts = await self.db_manager.search_similar_alerts(query_embedding, limit + 1)
            
            # Filter out the alert itself and apply threshold
            filtered_alerts = []
            for similar_alert in similar_alerts:
                if (similar_alert["alert_id"] != alert_id and 
                    similar_alert["similarity"] >= threshold):
                    filtered_alerts.append(similar_alert)
            
            return filtered_alerts[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar alerts by ID {alert_id}: {e}")
            return []
    
    async def find_candidates_for_grouping(self, threshold: float = None, batch_size: int = 100) -> List[Tuple[str, List[str]]]:
        """Find candidates for alert grouping based on similarity"""
        try:
            if threshold is None:
                threshold = settings.SIMILARITY_THRESHOLD
            
            # This is a simplified approach - in production, you might want more sophisticated clustering
            # Get collection stats to determine processing approach
            stats = await self.db_manager.get_collection_stats()
            total_alerts = stats.get("total_alerts", 0)
            
            if total_alerts == 0:
                return []
            
            logger.info(f"Finding grouping candidates from {total_alerts} alerts")
            
            # For now, return empty list - actual implementation would involve:
            # 1. Clustering algorithms (K-means, DBSCAN, etc.)
            # 2. Similarity matrix calculation
            # 3. Community detection algorithms
            
            # This is a placeholder that should be implemented based on specific requirements
            candidates = []
            
            return candidates
            
        except Exception as e:
            logger.error(f"Failed to find grouping candidates: {e}")
            return []
    
    async def update_alert(self, alert: Alert) -> bool:
        """Update alert in vector store"""
        try:
            # Remove existing alert
            await self.remove_alert(alert.id)
            
            # Add updated alert
            return await self.add_alert(alert)
            
        except Exception as e:
            logger.error(f"Failed to update alert {alert.id} in vector store: {e}")
            return False
    
    async def remove_alert(self, alert_id: str) -> bool:
        """Remove alert from vector store"""
        try:
            await self.db_manager.delete_alert(alert_id)
            logger.info(f"Removed alert {alert_id} from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove alert {alert_id} from vector store: {e}")
            return False
    
    async def get_alert_embedding(self, alert_id: str) -> Optional[List[float]]:
        """Get embedding for a specific alert"""
        try:
            # This would require modifications to the database layer to return embeddings
            # For now, we'll regenerate the embedding
            alert_data = await self.db_manager.get_alert_by_id(alert_id)
            if not alert_data:
                return None
            
            alert_metadata = alert_data["metadata"]
            alert_text = alert_metadata.get("summary", "")
            
            if alert_text:
                return await self.llm_service.generate_embedding(alert_text)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get embedding for alert {alert_id}: {e}")
            return None
    
    async def calculate_similarity_matrix(self, alert_ids: List[str]) -> Dict[str, Dict[str, float]]:
        """Calculate similarity matrix for given alert IDs"""
        try:
            similarity_matrix = {}
            
            # Get embeddings for all alerts
            embeddings = {}
            for alert_id in alert_ids:
                embedding = await self.get_alert_embedding(alert_id)
                if embedding:
                    embeddings[alert_id] = embedding
            
            # Calculate pairwise similarities
            for i, alert_id1 in enumerate(alert_ids):
                if alert_id1 not in embeddings:
                    continue
                    
                similarity_matrix[alert_id1] = {}
                
                for j, alert_id2 in enumerate(alert_ids):
                    if alert_id2 not in embeddings:
                        continue
                    
                    if i == j:
                        similarity_matrix[alert_id1][alert_id2] = 1.0
                    elif alert_id2 in similarity_matrix and alert_id1 in similarity_matrix[alert_id2]:
                        # Use already calculated similarity (symmetric)
                        similarity_matrix[alert_id1][alert_id2] = similarity_matrix[alert_id2][alert_id1]
                    else:
                        # Calculate similarity
                        similarity = self.llm_service._cosine_similarity(
                            embeddings[alert_id1], 
                            embeddings[alert_id2]
                        )
                        similarity_matrix[alert_id1][alert_id2] = similarity
            
            return similarity_matrix
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity matrix: {e}")
            return {}
    
    async def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            stats = await self.db_manager.get_collection_stats()
            
            # Add additional vector store specific stats
            stats.update({
                "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
                "max_group_size": settings.MAX_GROUP_SIZE
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get vector store stats: {e}")
            return {}
    
    def _create_alert_text(self, alert: Alert) -> str:
        """Create comprehensive text representation of alert for embedding"""
        text_parts = [
            f"Title: {alert.title}",
            f"Description: {alert.description}",
            f"Severity: {alert.severity}",
            f"Source: {alert.source_system}"
        ]
        
        if alert.service_name:
            text_parts.append(f"Service: {alert.service_name}")
        
        if alert.host_name:
            text_parts.append(f"Host: {alert.host_name}")
        
        if alert.environment:
            text_parts.append(f"Environment: {alert.environment}")
        
        if alert.tags:
            text_parts.append(f"Tags: {', '.join(alert.tags)}")
        
        if alert.metrics:
            metrics_text = ', '.join([f"{k}: {v}" for k, v in alert.metrics.items()])
            text_parts.append(f"Metrics: {metrics_text}")
        
        return " | ".join(text_parts)

# Global vector store instance
vector_store = VectorStore()

async def get_vector_store() -> VectorStore:
    """Get vector store instance"""
    if vector_store.llm_service is None:
        await vector_store.initialize()
    return vector_store
