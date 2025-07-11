"""
API Client for communicating with the Alert Monitoring System backend
"""
import requests
import logging
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import streamlit as st

logger = logging.getLogger(__name__)

class APIClient:
    """Client for interacting with the backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            else:
                return {"success": True}
                
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to {url}")
            raise Exception("Unable to connect to the backend API. Please check if the server is running.")
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout error for {url}")
            raise Exception("Request timed out. The server might be overloaded.")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            try:
                error_data = e.response.json()
                raise Exception(f"API Error: {error_data.get('detail', str(e))}")
            except json.JSONDecodeError:
                raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
        
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise Exception(f"Unexpected error: {str(e)}")
    
    # Health and System endpoints
    def get_health(self) -> Dict[str, Any]:
        """Get API health status"""
        return self._make_request("GET", "/health")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return self._make_request("GET", "/info")
    
    # Alert endpoints
    def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert"""
        return self._make_request("POST", "/api/v1/alerts/", json=alert_data)
    
    def get_alert(self, alert_id: str) -> Dict[str, Any]:
        """Get alert by ID"""
        return self._make_request("GET", f"/api/v1/alerts/{alert_id}")
    
    def update_alert(self, alert_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an alert"""
        return self._make_request("PUT", f"/api/v1/alerts/{alert_id}", json=update_data)
    
    def delete_alert(self, alert_id: str) -> Dict[str, Any]:
        """Delete an alert"""
        return self._make_request("DELETE", f"/api/v1/alerts/{alert_id}")
    
    def list_alerts(self, 
                   limit: int = 50, 
                   offset: int = 0, 
                   severity: Optional[List[str]] = None,
                   status: Optional[List[str]] = None,
                   service_name: Optional[str] = None,
                   environment: Optional[str] = None) -> Dict[str, Any]:
        """List alerts with optional filtering"""
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status
        if service_name:
            params["service_name"] = service_name
        if environment:
            params["environment"] = environment
        
        return self._make_request("GET", "/api/v1/alerts/", params=params)
    
    def search_alerts(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search alerts with advanced filtering"""
        return self._make_request("POST", "/api/v1/alerts/search", json=search_data)
    
    def find_similar_alerts(self, alert_id: str, threshold: float = 0.8, limit: int = 10) -> Dict[str, Any]:
        """Find similar alerts"""
        similarity_data = {
            "alert_id": alert_id,
            "threshold": threshold,
            "limit": limit
        }
        return self._make_request("POST", f"/api/v1/alerts/{alert_id}/similar", json=similarity_data)
    
    def get_alert_group(self, alert_id: str) -> Dict[str, Any]:
        """Get the group that an alert belongs to"""
        return self._make_request("GET", f"/api/v1/alerts/{alert_id}/group")
    
    def classify_alert(self, alert_id: str) -> Dict[str, Any]:
        """Classify an alert using AI"""
        return self._make_request("POST", f"/api/v1/alerts/{alert_id}/classify")
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        return self._make_request("GET", "/api/v1/alerts/stats/summary")
    
    # Group endpoints
    def list_groups(self,
                   limit: int = 20,
                   offset: int = 0,
                   status: Optional[List[str]] = None,
                   priority: Optional[List[str]] = None,
                   rca_status: Optional[List[str]] = None) -> Dict[str, Any]:
        """List alert groups with optional filtering"""
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        if rca_status:
            params["rca_status"] = rca_status
        
        return self._make_request("GET", "/api/v1/groups/", params=params)
    
    def get_group(self, group_id: str) -> Dict[str, Any]:
        """Get group by ID"""
        return self._make_request("GET", f"/api/v1/groups/{group_id}")
    
    def get_group_with_alerts(self, group_id: str) -> Dict[str, Any]:
        """Get group with full alert details"""
        return self._make_request("GET", f"/api/v1/groups/{group_id}/with-alerts")
    
    def update_group(self, group_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a group"""
        return self._make_request("PUT", f"/api/v1/groups/{group_id}", json=update_data)
    
    def search_groups(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search groups with advanced filtering"""
        return self._make_request("POST", "/api/v1/groups/search", json=search_data)
    
    def generate_rca(self, group_id: str, force_regenerate: bool = False, include_context: bool = True) -> Dict[str, Any]:
        """Generate RCA for a group"""
        rca_data = {
            "group_id": group_id,
            "force_regenerate": force_regenerate,
            "include_context": include_context
        }
        return self._make_request("POST", f"/api/v1/groups/{group_id}/rca", json=rca_data)
    
    def get_rca(self, group_id: str) -> Dict[str, Any]:
        """Get RCA for a group"""
        return self._make_request("GET", f"/api/v1/groups/{group_id}/rca")
    
    def resolve_group(self, group_id: str, resolution_notes: Optional[str] = None) -> Dict[str, Any]:
        """Mark a group as resolved"""
        data = {}
        if resolution_notes:
            data["resolution_notes"] = resolution_notes
        
        return self._make_request("POST", f"/api/v1/groups/{group_id}/resolve", json=data)
    
    def get_group_stats(self) -> Dict[str, Any]:
        """Get group statistics"""
        return self._make_request("GET", "/api/v1/groups/stats/summary")
    
    def merge_groups(self, source_group_ids: List[str], target_group_id: str, merge_reason: Optional[str] = None) -> Dict[str, Any]:
        """Merge multiple groups into one"""
        merge_data = {
            "source_group_ids": source_group_ids,
            "target_group_id": target_group_id
        }
        if merge_reason:
            merge_data["merge_reason"] = merge_reason
        
        return self._make_request("POST", "/api/v1/groups/merge", json=merge_data)
    
    # Utility methods for Streamlit integration
    @st.cache_data(ttl=30)
    def get_cached_alerts(_self, limit: int = 50) -> Dict[str, Any]:
        """Get cached alerts for better performance"""
        return _self.list_alerts(limit=limit)
    
    @st.cache_data(ttl=30)
    def get_cached_groups(_self, limit: int = 20) -> Dict[str, Any]:
        """Get cached groups for better performance"""
        return _self.list_groups(limit=limit)
    
    @st.cache_data(ttl=60)
    def get_cached_stats(_self) -> Dict[str, Any]:
        """Get cached statistics for better performance"""
        try:
            alert_stats = _self.get_alert_stats()
            group_stats = _self.get_group_stats()
            
            return {
                "alerts": alert_stats.get("data", {}),
                "groups": group_stats.get("data", {})
            }
        except Exception as e:
            logger.error(f"Failed to get cached stats: {e}")
            return {"alerts": {}, "groups": {}}
    
    def create_sample_alert(self, title: str, description: str, severity: str = "Medium") -> Dict[str, Any]:
        """Create a sample alert for testing"""
        alert_data = {
            "title": title,
            "description": description,
            "severity": severity,
            "source_system": "Manual",
            "service_name": "test-service",
            "host_name": "test-host",
            "environment": "development",
            "tags": ["test", "manual"],
            "metrics": {
                "test_metric": 1.0
            }
        }
        
        return self.create_alert(alert_data)
    
    def bulk_create_sample_alerts(self, count: int = 5) -> List[Dict[str, Any]]:
        """Create multiple sample alerts for testing"""
        sample_alerts = [
            {
                "title": "High CPU Usage",
                "description": "CPU usage exceeded 90% on web server",
                "severity": "High",
                "service_name": "web-api",
                "host_name": "web-01"
            },
            {
                "title": "Database Connection Timeout",
                "description": "Database connections timing out after 30 seconds",
                "severity": "Critical",
                "service_name": "database",
                "host_name": "db-01"
            },
            {
                "title": "Memory Usage Warning",
                "description": "Memory usage approaching 85% threshold",
                "severity": "Medium",
                "service_name": "web-api",
                "host_name": "web-02"
            },
            {
                "title": "Disk Space Low",
                "description": "Disk space below 10% on log partition",
                "severity": "High",
                "service_name": "logging",
                "host_name": "log-01"
            },
            {
                "title": "Network Latency Spike",
                "description": "Network latency increased to 500ms",
                "severity": "Medium",
                "service_name": "network",
                "host_name": "router-01"
            }
        ]
        
        results = []
        for i, alert_template in enumerate(sample_alerts[:count]):
            alert_data = {
                **alert_template,
                "source_system": "Demo",
                "environment": "production",
                "tags": ["demo", "sample"],
                "metrics": {"value": i * 10 + 50}
            }
            
            try:
                result = self.create_alert(alert_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to create sample alert {i}: {e}")
        
        return results
