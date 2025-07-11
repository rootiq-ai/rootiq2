"""
Utility functions and helpers for the Alert Monitoring System
"""
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def generate_alert_hash(alert_data: Dict[str, Any]) -> str:
    """Generate a unique hash for an alert based on its content"""
    # Create a normalized string representation of the alert
    normalized_data = {
        "title": alert_data.get("title", "").lower().strip(),
        "description": alert_data.get("description", "").lower().strip(),
        "service_name": alert_data.get("service_name", "").lower().strip(),
        "host_name": alert_data.get("host_name", "").lower().strip(),
        "source_system": alert_data.get("source_system", "").lower().strip(),
    }
    
    # Create a deterministic string
    content_string = json.dumps(normalized_data, sort_keys=True)
    
    # Generate hash
    return hashlib.md5(content_string.encode()).hexdigest()

def extract_service_from_text(text: str) -> Optional[str]:
    """Extract service name from alert text using common patterns"""
    service_patterns = [
        r'service[:\s]+([a-zA-Z0-9\-_]+)',
        r'application[:\s]+([a-zA-Z0-9\-_]+)',
        r'app[:\s]+([a-zA-Z0-9\-_]+)',
        r'([a-zA-Z0-9\-_]+)\s+service',
        r'([a-zA-Z0-9\-_]+)\s+application',
    ]
    
    text_lower = text.lower()
    
    for pattern in service_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1)
    
    return None

def extract_host_from_text(text: str) -> Optional[str]:
    """Extract hostname from alert text using common patterns"""
    host_patterns = [
        r'host[:\s]+([a-zA-Z0-9\-_.]+)',
        r'hostname[:\s]+([a-zA-Z0-9\-_.]+)',
        r'server[:\s]+([a-zA-Z0-9\-_.]+)',
        r'node[:\s]+([a-zA-Z0-9\-_.]+)',
        r'on\s+([a-zA-Z0-9\-_.]+)',
        r'from\s+([a-zA-Z0-9\-_.]+)',
    ]
    
    for pattern in host_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            hostname = match.group(1)
            # Basic validation - should look like a hostname
            if '.' in hostname or '-' in hostname:
                return hostname
    
    return None

def extract_metrics_from_text(text: str) -> Dict[str, Union[float, int]]:
    """Extract numerical metrics from alert text"""
    metrics = {}
    
    # Common metric patterns
    metric_patterns = [
        (r'cpu\s+usage[:\s]+([0-9.]+)%?', 'cpu_usage_percent'),
        (r'memory\s+usage[:\s]+([0-9.]+)%?', 'memory_usage_percent'),
        (r'disk\s+usage[:\s]+([0-9.]+)%?', 'disk_usage_percent'),
        (r'load\s+average[:\s]+([0-9.]+)', 'load_average'),
        (r'response\s+time[:\s]+([0-9.]+)', 'response_time_ms'),
        (r'latency[:\s]+([0-9.]+)', 'latency_ms'),
        (r'errors[:\s]+([0-9]+)', 'error_count'),
        (r'requests[:\s]+([0-9]+)', 'request_count'),
        (r'connections[:\s]+([0-9]+)', 'connection_count'),
        (r'([0-9.]+)\s*%', 'percentage_value'),
        (r'([0-9.]+)\s*(ms|milliseconds)', 'time_ms'),
        (r'([0-9.]+)\s*(seconds?|secs?)', 'time_seconds'),
    ]
    
    text_lower = text.lower()
    
    for pattern, metric_name in metric_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            try:
                # Take the first match and convert to float
                value = float(matches[0])
                metrics[metric_name] = value
            except (ValueError, IndexError):
                continue
    
    return metrics

def normalize_severity(severity: str) -> str:
    """Normalize severity level to standard values"""
    severity_mapping = {
        'critical': 'Critical',
        'crit': 'Critical',
        'high': 'High',
        'major': 'High',
        'medium': 'Medium',
        'med': 'Medium',
        'moderate': 'Medium',
        'low': 'Low',
        'minor': 'Low',
        'info': 'Info',
        'information': 'Info',
        'informational': 'Info',
        'warning': 'Medium',
        'warn': 'Medium',
        'error': 'High',
        'emergency': 'Critical',
        'alert': 'Critical',
    }
    
    severity_lower = severity.lower().strip()
    return severity_mapping.get(severity_lower, 'Medium')

def parse_alert_tags(tags_input: Union[str, List[str]]) -> List[str]:
    """Parse tags from various input formats"""
    if isinstance(tags_input, list):
        return [tag.strip() for tag in tags_input if tag.strip()]
    
    if isinstance(tags_input, str):
        # Handle comma-separated, space-separated, or semicolon-separated
        separators = [',', ';', '|']
        tags = [tags_input]
        
        for sep in separators:
            if sep in tags_input:
                tags = tags_input.split(sep)
                break
        else:
            # Try space separation if no other separators found
            tags = tags_input.split()
        
        return [tag.strip() for tag in tags if tag.strip()]
    
    return []

def calculate_alert_priority_score(alert_data: Dict[str, Any]) -> float:
    """Calculate a priority score for an alert (0-100)"""
    score = 0.0
    
    # Severity scoring (40% of total)
    severity_scores = {
        'Critical': 40.0,
        'High': 30.0,
        'Medium': 20.0,
        'Low': 10.0,
        'Info': 5.0
    }
    severity = alert_data.get('severity', 'Medium')
    score += severity_scores.get(severity, 20.0)
    
    # Environment scoring (20% of total)
    environment_scores = {
        'production': 20.0,
        'prod': 20.0,
        'staging': 15.0,
        'stage': 15.0,
        'development': 10.0,
        'dev': 10.0,
        'test': 5.0,
        'testing': 5.0
    }
    environment = alert_data.get('environment', '').lower()
    score += environment_scores.get(environment, 10.0)
    
    # Service criticality (20% of total)
    service_name = alert_data.get('service_name', '').lower()
    critical_services = ['database', 'db', 'auth', 'payment', 'api', 'gateway']
    if any(critical in service_name for critical in critical_services):
        score += 20.0
    elif service_name:
        score += 10.0
    
    # Alert age penalty (10% of total)
    timestamp = alert_data.get('timestamp')
    if timestamp:
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        age_hours = (datetime.utcnow() - timestamp.replace(tzinfo=None)).total_seconds() / 3600
        
        if age_hours < 1:
            score += 10.0
        elif age_hours < 6:
            score += 8.0
        elif age_hours < 24:
            score += 5.0
        else:
            score += 2.0
    
    # Metrics impact (10% of total)
    metrics = alert_data.get('metrics', {})
    if metrics:
        # Look for high percentage values
        for key, value in metrics.items():
            if 'percent' in key.lower() or '%' in str(value):
                try:
                    val = float(str(value).replace('%', ''))
                    if val > 90:
                        score += 10.0
                    elif val > 80:
                        score += 8.0
                    elif val > 70:
                        score += 5.0
                    break
                except:
                    continue
        else:
            score += 2.0
    
    return min(100.0, max(0.0, score))

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize text input for safe storage and processing"""
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized

def validate_alert_data(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean alert data"""
    errors = []
    cleaned_data = {}
    
    # Required fields
    required_fields = ['title', 'description', 'severity', 'source_system']
    for field in required_fields:
        value = alert_data.get(field)
        if not value or not str(value).strip():
            errors.append(f"Missing required field: {field}")
        else:
            cleaned_data[field] = sanitize_text(str(value))
    
    # Optional fields with validation
    optional_fields = {
        'service_name': lambda x: sanitize_text(str(x), 100),
        'host_name': lambda x: sanitize_text(str(x), 100),
        'environment': lambda x: sanitize_text(str(x), 50),
        'external_id': lambda x: sanitize_text(str(x), 100),
    }
    
    for field, validator in optional_fields.items():
        value = alert_data.get(field)
        if value:
            try:
                cleaned_data[field] = validator(value)
            except Exception as e:
                errors.append(f"Invalid {field}: {e}")
    
    # Validate severity
    if 'severity' in cleaned_data:
        cleaned_data['severity'] = normalize_severity(cleaned_data['severity'])
    
    # Validate and parse tags
    tags = alert_data.get('tags')
    if tags:
        cleaned_data['tags'] = parse_alert_tags(tags)
    
    # Validate metrics
    metrics = alert_data.get('metrics')
    if metrics and isinstance(metrics, dict):
        cleaned_metrics = {}
        for key, value in metrics.items():
            try:
                # Ensure values are numeric
                if isinstance(value, (int, float)):
                    cleaned_metrics[sanitize_text(str(key), 50)] = value
                elif isinstance(value, str):
                    # Try to parse as number
                    try:
                        cleaned_metrics[sanitize_text(str(key), 50)] = float(value)
                    except ValueError:
                        cleaned_metrics[sanitize_text(str(key), 50)] = sanitize_text(value, 100)
            except Exception:
                continue
        
        if cleaned_metrics:
            cleaned_data['metrics'] = cleaned_metrics
    
    return {
        'data': cleaned_data,
        'errors': errors,
        'is_valid': len(errors) == 0
    }

def generate_similarity_key(alert1: Dict[str, Any], alert2: Dict[str, Any]) -> str:
    """Generate a unique key for alert similarity pairs"""
    id1 = alert1.get('id', '')
    id2 = alert2.get('id', '')
    
    # Ensure consistent ordering
    if id1 < id2:
        return f"{id1}:{id2}"
    else:
        return f"{id2}:{id1}"

def extract_error_patterns(text: str) -> List[str]:
    """Extract common error patterns from alert text"""
    patterns = []
    
    # Common error patterns
    error_patterns = [
        r'(timeout|timed out)',
        r'(connection refused|connection failed)',
        r'(out of memory|oom)',
        r'(disk full|no space left)',
        r'(permission denied|access denied)',
        r'(not found|404)',
        r'(internal server error|500)',
        r'(bad gateway|502)',
        r'(service unavailable|503)',
        r'(gateway timeout|504)',
        r'(authentication failed|auth failed)',
        r'(certificate|ssl|tls).*?(expired?|invalid|error)',
        r'(database|db).*?(connection|error|timeout)',
        r'(high (cpu|memory|disk|load))',
    ]
    
    text_lower = text.lower()
    
    for pattern in error_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        patterns.extend(matches)
    
    return list(set(patterns))  # Remove duplicates

def cluster_alerts_by_time_window(alerts: List[Dict[str, Any]], window_minutes: int = 30) -> List[List[Dict[str, Any]]]:
    """Cluster alerts by time window"""
    if not alerts:
        return []
    
    # Sort alerts by timestamp
    sorted_alerts = sorted(alerts, key=lambda x: x.get('timestamp', datetime.min))
    
    clusters = []
    current_cluster = [sorted_alerts[0]]
    
    for alert in sorted_alerts[1:]:
        current_time = alert.get('timestamp', datetime.min)
        cluster_start = current_cluster[0].get('timestamp', datetime.min)
        
        # Calculate time difference
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
        if isinstance(cluster_start, str):
            cluster_start = datetime.fromisoformat(cluster_start.replace('Z', '+00:00'))
        
        time_diff = (current_time - cluster_start).total_seconds() / 60
        
        if time_diff <= window_minutes:
            current_cluster.append(alert)
        else:
            clusters.append(current_cluster)
            current_cluster = [alert]
    
    # Add the last cluster
    if current_cluster:
        clusters.append(current_cluster)
    
    return clusters

def calculate_system_health_score(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate overall system health score based on alerts"""
    if not alerts:
        return {
            'score': 100.0,
            'status': 'Healthy',
            'critical_issues': 0,
            'total_alerts': 0
        }
    
    total_alerts = len(alerts)
    critical_count = 0
    high_count = 0
    recent_count = 0
    
    now = datetime.utcnow()
    
    for alert in alerts:
        severity = alert.get('severity', 'Medium')
        timestamp = alert.get('timestamp')
        
        if severity == 'Critical':
            critical_count += 1
        elif severity == 'High':
            high_count += 1
        
        # Count recent alerts (last 1 hour)
        if timestamp:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            age_hours = (now - timestamp.replace(tzinfo=None)).total_seconds() / 3600
            if age_hours <= 1:
                recent_count += 1
    
    # Calculate score (0-100)
    score = 100.0
    
    # Penalize for critical alerts
    score -= critical_count * 20
    
    # Penalize for high severity alerts
    score -= high_count * 10
    
    # Penalize for high volume of recent alerts
    if recent_count > 10:
        score -= (recent_count - 10) * 2
    
    # Ensure score is between 0 and 100
    score = max(0.0, min(100.0, score))
    
    # Determine status
    if score >= 90:
        status = 'Healthy'
    elif score >= 75:
        status = 'Warning'
    elif score >= 50:
        status = 'Degraded'
    else:
        status = 'Critical'
    
    return {
        'score': round(score, 1),
        'status': status,
        'critical_issues': critical_count,
        'high_priority_issues': high_count,
        'recent_alerts': recent_count,
        'total_alerts': total_alerts
    }

# Utility class for rate limiting
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).total_seconds() < window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def cleanup_old_entries(self, window_seconds: int = 3600):
        """Clean up old rate limit entries"""
        now = datetime.utcnow()
        
        for key in list(self.requests.keys()):
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if (now - req_time).total_seconds() < window_seconds
            ]
            
            if not self.requests[key]:
                del self.requests[key]

# Global rate limiter instance
rate_limiter = RateLimiter()
