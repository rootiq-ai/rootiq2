"""
LLM Service for Ollama integration
"""
import asyncio
import httpx
import json
import logging
from typing import Optional, List, Dict, Any
import numpy as np
from datetime import datetime

from core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with Ollama LLM"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.client = None
        
    async def initialize(self):
        """Initialize the LLM service"""
        try:
            self.client = httpx.AsyncClient(timeout=self.timeout)
            
            # Check if Ollama is running
            await self._check_ollama_health()
            
            # Ensure required models are available
            await self._ensure_models_available()
            
            logger.info("LLM service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def _check_ollama_health(self):
        """Check if Ollama is healthy and responding"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise Exception(f"Ollama health check failed: {response.status_code}")
                
            logger.info("Ollama is healthy and responding")
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            raise
    
    async def _ensure_models_available(self):
        """Ensure required models are available"""
        try:
            # Get list of available models
            response = await self.client.get(f"{self.base_url}/api/tags")
            models_data = response.json()
            
            available_models = [model["name"] for model in models_data.get("models", [])]
            
            # Check if main model is available
            if self.model not in available_models:
                logger.warning(f"Model {self.model} not found. Attempting to pull...")
                await self._pull_model(self.model)
            
            # Check if embedding model is available
            if self.embedding_model not in available_models:
                logger.warning(f"Embedding model {self.embedding_model} not found. Attempting to pull...")
                await self._pull_model(self.embedding_model)
                
            logger.info("Required models are available")
            
        except Exception as e:
            logger.error(f"Failed to ensure models are available: {e}")
            raise
    
    async def _pull_model(self, model_name: str):
        """Pull a model from Ollama"""
        try:
            logger.info(f"Pulling model: {model_name}")
            
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=600  # Extended timeout for model pulling
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully pulled model: {model_name}")
            else:
                raise Exception(f"Failed to pull model {model_name}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Ollama"""
        try:
            if not self.client:
                await self.initialize()
            
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                
                if not embedding:
                    raise Exception("Empty embedding returned")
                
                return embedding
            else:
                raise Exception(f"Embedding generation failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1000) -> str:
        """Generate text using Ollama"""
        try:
            if not self.client:
                await self.initialize()
            
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "")
            else:
                raise Exception(f"Text generation failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            raise
    
    async def analyze_alert_similarity(self, alert1_text: str, alert2_text: str) -> float:
        """Analyze similarity between two alerts using embeddings"""
        try:
            # Generate embeddings for both alerts
            embedding1 = await self.generate_embedding(alert1_text)
            embedding2 = await self.generate_embedding(alert2_text)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(embedding1, embedding2)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Failed to analyze alert similarity: {e}")
            return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            
            # Ensure similarity is between 0 and 1
            return max(0.0, min(1.0, float(similarity)))
            
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {e}")
            return 0.0
    
    async def generate_alert_summary(self, alert_text: str) -> str:
        """Generate a summary for an alert"""
        try:
            system_prompt = """
            You are an expert system administrator. Create a concise summary of the following alert.
            Focus on the key issue, affected system/service, and severity.
            Keep the summary under 100 words.
            """
            
            prompt = f"Alert details:\n{alert_text}\n\nSummary:"
            
            summary = await self.generate_text(prompt, system_prompt, max_tokens=150)
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate alert summary: {e}")
            return alert_text[:200] + "..." if len(alert_text) > 200 else alert_text
    
    async def classify_alert_category(self, alert_text: str) -> str:
        """Classify alert into a category"""
        try:
            system_prompt = """
            You are an expert system administrator. Classify the following alert into one of these categories:
            - Infrastructure
            - Application
            - Database
            - Network
            - Security
            - Performance
            - Storage
            - Other
            
            Return only the category name.
            """
            
            prompt = f"Alert details:\n{alert_text}\n\nCategory:"
            
            category = await self.generate_text(prompt, system_prompt, max_tokens=10)
            
            return category.strip()
            
        except Exception as e:
            logger.error(f"Failed to classify alert: {e}")
            return "Other"
    
    async def extract_alert_keywords(self, alert_text: str) -> List[str]:
        """Extract keywords from alert text"""
        try:
            system_prompt = """
            You are an expert system administrator. Extract the most important keywords 
            from the following alert that would be useful for grouping similar alerts.
            Return 5-10 keywords separated by commas.
            Focus on technical terms, service names, error types, and affected components.
            """
            
            prompt = f"Alert details:\n{alert_text}\n\nKeywords:"
            
            keywords_text = await self.generate_text(prompt, system_prompt, max_tokens=100)
            
            # Parse keywords
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            
            return keywords[:10]  # Limit to 10 keywords
            
        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return []
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        try:
            if not self.client:
                await self.initialize()
            
            response = await self.client.get(f"{self.base_url}/api/tags")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get model info: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}

# Global LLM service instance
llm_service = LLMService()

async def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    if llm_service.client is None:
        await llm_service.initialize()
    return llm_service
