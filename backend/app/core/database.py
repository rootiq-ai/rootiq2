"""
Database configuration and initialization for ChromaDB
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
import logging
from typing import Optional
import asyncio
import json
from datetime import datetime

from core.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for ChromaDB operations"""
    
    def __init__(self):
        self.client: Optional[chromadb.Client] = None
        self.collection = None
        
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=settings.CHROMADB_PERSIST_DIRECTORY,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection for alerts
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMADB_COLLECTION,
                metadata={"description": "Alert embeddings for similarity search"}
            )
            
            logger.info(f"ChromaDB initialized with collection: {settings.CHROMADB_COLLECTION}")
            logger.info(f"Collection count: {self.collection.count()}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_alert_embedding(self, alert_id: str, embedding: list, metadata: dict):
        """Add alert embedding to the collection"""
        try:
            # Prepare document with alert information
            document = json.dumps({
                "alert_id": alert_id,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": metadata.get("summary", ""),
                "description": metadata.get("description", ""),
                "severity": metadata.get("severity", ""),
                "source": metadata.get("source", "")
            })
            
            self.collection.add(
                embeddings=[embedding],
                documents=[document],
                metadatas=[metadata],
                ids=[alert_id]
            )
            
            logger.info(f"Added embedding for alert: {alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to add alert embedding: {e}")
            raise
    
    async def search_similar_alerts(self, query_embedding: list, limit: int = 10) -> list:
        """Search for similar alerts using vector similarity"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            similar_alerts = []
            if results and results["ids"]:
                for i, alert_id in enumerate(results["ids"][0]):
                    similar_alerts.append({
                        "alert_id": alert_id,
                        "distance": results["distances"][0][i],
                        "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                        "metadata": results["metadatas"][0][i],
                        "document": results["documents"][0][i]
                    })
            
            return similar_alerts
            
        except Exception as e:
            logger.error(f"Failed to search similar alerts: {e}")
            return []
    
    async def get_alert_by_id(self, alert_id: str) -> Optional[dict]:
        """Get alert by ID"""
        try:
            results = self.collection.get(
                ids=[alert_id],
                include=["documents", "metadatas"]
            )
            
            if results and results["ids"]:
                return {
                    "alert_id": results["ids"][0],
                    "metadata": results["metadatas"][0],
                    "document": results["documents"][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get alert by ID: {e}")
            return None
    
    async def delete_alert(self, alert_id: str):
        """Delete alert from collection"""
        try:
            self.collection.delete(ids=[alert_id])
            logger.info(f"Deleted alert: {alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete alert: {e}")
            raise
    
    async def get_collection_stats(self) -> dict:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            
            return {
                "total_alerts": count,
                "collection_name": settings.CHROMADB_COLLECTION,
                "persist_directory": settings.CHROMADB_PERSIST_DIRECTORY
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def reset_collection(self):
        """Reset the collection (for testing purposes)"""
        try:
            if self.client and self.collection:
                self.client.delete_collection(settings.CHROMADB_COLLECTION)
                self.collection = self.client.get_or_create_collection(
                    name=settings.CHROMADB_COLLECTION,
                    metadata={"description": "Alert embeddings for similarity search"}
                )
                logger.info("Collection reset successfully")
                
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

async def init_database():
    """Initialize the database"""
    await db_manager.initialize()

async def get_database():
    """Get database manager instance"""
    return db_manager

# Helper functions for common database operations
async def add_alert_to_db(alert_id: str, embedding: list, metadata: dict):
    """Helper function to add alert to database"""
    await db_manager.add_alert_embedding(alert_id, embedding, metadata)

async def search_similar_in_db(query_embedding: list, limit: int = 10) -> list:
    """Helper function to search similar alerts"""
    return await db_manager.search_similar_alerts(query_embedding, limit)

async def get_db_stats() -> dict:
    """Helper function to get database statistics"""
    return await db_manager.get_collection_stats()
