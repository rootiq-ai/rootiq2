#!/usr/bin/env python3
"""
Demo script for Alert Monitoring System
Creates sample alerts and demonstrates system capabilities
"""
import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class AlertMonitoringDemo:
    """Demo class for Alert Monitoring System"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
        self.session = requests.Session()
        self.created_alerts = []
        
    def check_system_health(self) -> bool:
        """Check if the system is running"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ System health check failed: {e}")
            return False
    
    def create_sample_alerts(self) -> List[str]:
        """Create a comprehensive set of sample alerts"""
        print("🚨 Creating sample alerts...")
        
        # Define sample alert templates
        alert_templates = [
            {
                "title": "High CPU Usage on Web Server",
                "description": "CPU usage has exceeded 90% on web-server-01 for the past 5 minutes. This may impact application performance.",
                "severity": "High",
                "source_system": "Prometheus",
                "service_name": "web-api",
                "host_name": "web-server-01",
                "environment": "production",
                "tags": ["cpu", "performance", "infrastructure"],
                "metrics": {"cpu_usage": 95.2, "duration_minutes": 5}
            },
            {
                "title": "Database Connection Pool Exhausted",
                "description": "All database connections are in use. New connection requests are being queued.",
                "severity": "Critical",
                "source_system": "DataDog",
                "service_name": "user-database",
                "host_name": "db-primary-01",
                "environment": "production",
                "tags": ["database", "connections", "performance"],
                "metrics": {"active_connections": 100, "max_connections": 100}
            },
            {
                "title": "API Response Time Degradation",
                "description": "Average API response time has increased to 2.5 seconds, exceeding the 1-second SLA.",
                "severity": "High",
                "source_system": "New Relic",
                "service_name": "user-api",
                "host_name": "api-server-02",
                "environment": "production",
                "tags": ["api", "latency", "sla"],
                "metrics": {"avg_response_time_ms": 2500, "sla_threshold_ms": 1000}
            },
            {
                "title": "Memory Usage Warning",
                "description": "Memory usage on application server has reached 85%, approaching critical threshold.",
                "severity": "Medium",
                "source_system": "Nagios",
                "service_name": "web-api",
                "host_name": "app-server-03",
                "environment": "production",
                "tags": ["memory", "infrastructure", "warning"],
                "metrics": {"memory_usage_percent": 85, "threshold_percent": 90}
            },
            {
                "title": "Disk Space Running Low",
                "description": "Available disk space on /var/log partition is below 10% on log aggregator.",
                "severity": "Medium",
                "source_system": "Zabbix",
                "service_name": "log-aggregator",
                "host_name": "log-server-01",
                "environment": "production",
                "tags": ["disk", "storage", "logs"],
                "metrics": {"free_space_percent": 8, "total_space_gb": 500}
            },
            {
                "title": "SSL Certificate Expiring Soon",
                "description": "SSL certificate for api.example.com will expire in 7 days.",
                "severity": "Medium",
                "source_system": "Custom",
                "service_name": "api-gateway",
                "host_name": "gateway-01",
                "environment": "production",
                "tags": ["ssl", "certificate", "security"],
                "metrics": {"days_until_expiry": 7}
            },
            {
                "title": "Failed Login Attempts Spike",
                "description": "Detected 500+ failed login attempts from multiple IP addresses in the last 10 minutes.",
                "severity": "High",
                "source_system": "Custom",
                "service_name": "auth-service",
                "host_name": "auth-server-01",
                "environment": "production",
                "tags": ["security", "authentication", "attack"],
                "metrics": {"failed_attempts": 547, "time_window_minutes": 10}
            },
            {
                "title": "Application Memory Leak Detected",
                "description": "Java heap usage continuously increasing on payment service, indicating potential memory leak.",
                "severity": "High",
                "source_system": "Grafana",
                "service_name": "payment-service",
                "host_name": "payment-server-02",
                "environment": "production",
                "tags": ["memory", "java", "memory-leak"],
                "metrics": {"heap_usage_mb": 3800, "max_heap_mb": 4096}
            },
            {
                "title": "Network Latency Increase",
                "description": "Network latency between data centers has increased to 150ms, affecting replication.",
                "severity": "Medium",
                "source_system": "Prometheus",
                "service_name": "database-replica",
                "host_name": "db-replica-west",
                "environment": "production",
                "tags": ["network", "latency", "replication"],
                "metrics": {"latency_ms": 150, "normal_latency_ms": 50}
            },
            {
                "title": "Load Balancer Health Check Failures",
                "description": "3 out of 6 backend servers are failing health checks on the main load balancer.",
                "severity": "Critical",
                "source_system": "HAProxy",
                "service_name": "load-balancer",
                "host_name": "lb-primary",
                "environment": "production",
                "tags": ["load-balancer", "health-check", "availability"],
                "metrics": {"failing_servers": 3, "total_servers": 6}
            },
            # Similar alerts for grouping demonstration
            {
                "title": "High CPU Usage on Web Server 02",
                "description": "CPU usage has exceeded 92% on web-server-02 for the past 6 minutes. Load balancer should redirect traffic.",
                "severity": "High",
                "source_system": "Prometheus",
                "service_name": "web-api",
                "host_name": "web-server-02",
                "environment": "production",
                "tags": ["cpu", "performance", "infrastructure"],
                "metrics": {"cpu_usage": 92.1, "duration_minutes": 6}
            },
            {
                "title": "Excessive CPU Load on Application Server",
                "description": "Application server experiencing high CPU load of 88% due to increased traffic volume.",
                "severity": "High",
                "source_system": "DataDog",
                "service_name": "web-api",
                "host_name": "web-server-03",
                "environment": "production",
                "tags": ["cpu", "performance", "traffic"],
                "metrics": {"cpu_usage": 88.5, "requests_per_second": 450}
            },
            {
                "title": "Database Slow Query Detected",
                "description": "Query execution time for user lookup has increased to 15 seconds, causing connection timeouts.",
                "severity": "High",
                "source_system": "MySQL",
                "service_name": "user-database",
                "host_name": "db-primary-01",
                "environment": "production",
                "tags": ["database", "query", "performance"],
                "metrics": {"query_time_seconds": 15, "normal_time_seconds": 0.5}
            },
            {
                "title": "Database Connection Timeout",
                "description": "Multiple applications reporting database connection timeouts. Database server may be overloaded.",
                "severity": "Critical",
                "source_system": "Application Logs",
                "service_name": "user-database",
                "host_name": "db-primary-01",
                "environment": "production",
                "tags": ["database", "timeout", "connections"],
                "metrics": {"timeout_count": 25, "connection_attempts": 100}
            }
        ]
        
        created_alert_ids = []
        
        for i, template in enumerate(alert_templates):
            try:
                # Add some randomness to timestamps
                base_time = datetime.utcnow() - timedelta(minutes=random.randint(5, 120))
                
                # Create the alert
                response = self.session.post(
                    f"{self.api_url}/alerts/",
                    json=template,
                    timeout=10
                )
                
                if response.status_code == 200:
                    alert_data = response.json()
                    if alert_data.get("success"):
                        alert_id = alert_data["data"]["id"]
                        created_alert_ids.append(alert_id)
                        print(f"  ✅ Created alert {i+1}/{len(alert_templates)}: {template['title']}")
                    else:
                        print(f"  ❌ Failed to create alert {i+1}: {alert_data.get('message', 'Unknown error')}")
                else:
                    print(f"  ❌ HTTP {response.status_code} for alert {i+1}")
                
                # Small delay to avoid overwhelming the system
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error creating alert {i+1}: {e}")
        
        self.created_alerts = created_alert_ids
        print(f"✅ Created {len(created_alert_ids)} sample alerts")
        return created_alert_ids
    
    def wait_for_processing(self, max_wait_seconds: int = 60):
        """Wait for alerts to be processed and grouped"""
        print("⏳ Waiting for alert processing and grouping...")
        
        start_time = time.time()
        processed_count = 0
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # Check how many alerts have been processed
                response = self.session.get(f"{self.api_url}/alerts/stats/summary")
                if response.status_code == 200:
                    stats = response.json()
                    if stats.get("success"):
                        total = stats["data"].get("total_alerts", 0)
                        print(f"  📊 Total alerts in system: {total}")
                
                # Check groups
                response = self.session.get(f"{self.api_url}/groups/")
                if response.status_code == 200:
                    groups_data = response.json()
                    if groups_data.get("success"):
                        groups = groups_data.get("data", [])
                        print(f"  👥 Alert groups created: {len(groups)}")
                        
                        if groups:
                            print("  📋 Group summary:")
                            for group in groups[:5]:  # Show first 5 groups
                                print(f"    - {group.get('title', 'Unknown')}: {group.get('alert_count', 0)} alerts")
                            return True
                
                time.sleep(5)
                
            except Exception as e:
                print(f"  ⚠️ Error checking processing status: {e}")
                time.sleep(2)
        
        print(f"⏰ Timeout after {max_wait_seconds} seconds")
        return False
    
    def demonstrate_rca_generation(self):
        """Demonstrate RCA generation for created groups"""
        print("🔍 Demonstrating RCA generation...")
        
        try:
            # Get available groups
            response = self.session.get(f"{self.api_url}/groups/")
            if response.status_code != 200:
                print("❌ Failed to fetch groups")
                return
            
            groups_data = response.json()
            if not groups_data.get("success"):
                print("❌ Failed to get groups data")
                return
            
            groups = groups_data.get("data", [])
            if not groups:
                print("ℹ️ No groups available for RCA generation")
                return
            
            # Generate RCA for the first few groups
            for i, group in enumerate(groups[:3]):
                group_id = group["id"]
                group_title = group.get("title", "Unknown")
                
                print(f"  🔬 Generating RCA for group: {group_title}")
                
                # Trigger RCA generation
                rca_request = {
                    "group_id": group_id,
                    "force_regenerate": True,
                    "include_context": True
                }
                
                response = self.session.post(
                    f"{self.api_url}/groups/{group_id}/rca",
                    json=rca_request,
                    timeout=30
                )
                
                if response.status_code == 200:
                    rca_result = response.json()
                    if rca_result.get("success"):
                        print(f"    ✅ RCA generation started for group {i+1}")
                        
                        # Wait a bit and check if RCA is completed
                        time.sleep(10)
                        
                        rca_response = self.session.get(f"{self.api_url}/groups/{group_id}/rca")
                        if rca_response.status_code == 200:
                            rca_data = rca_response.json()
                            if rca_data.get("success"):
                                data = rca_data.get("data", {})
                                if data.get("rca_content"):
                                    print(f"    📝 RCA completed with {len(data['rca_content'])} characters")
                                    confidence = data.get("confidence")
                                    if confidence:
                                        print(f"    📊 Confidence score: {confidence:.1%}")
                                else:
                                    print(f"    ⏳ RCA still processing...")
                    else:
                        print(f"    ❌ RCA generation failed: {rca_result.get('message')}")
                else:
                    print(f"    ❌ HTTP {response.status_code} for RCA generation")
                
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Error in RCA demonstration: {e}")
    
    def show_system_summary(self):
        """Show a summary of the current system state"""
        print("📊 System Summary:")
        print("=" * 50)
        
        try:
            # Alert statistics
            response = self.session.get(f"{self.api_url}/alerts/stats/summary")
            if response.status_code == 200:
                stats = response.json()
                if stats.get("success"):
                    data = stats["data"]
                    print(f"📋 Total Alerts: {data.get('total_alerts', 0)}")
                    print(f"🕐 Recent Alerts (24h): {data.get('recent_alerts_24h', 0)}")
                    
                    severity_dist = data.get("severity_distribution", {})
                    if severity_dist:
                        print("📊 Severity Distribution:")
                        for severity, count in severity_dist.items():
                            print(f"   {severity}: {count}")
            
            # Group statistics  
            response = self.session.get(f"{self.api_url}/groups/stats/summary")
            if response.status_code == 200:
                stats = response.json()
                if stats.get("success"):
                    data = stats["data"]
                    print(f"👥 Total Groups: {data.get('total_groups', 0)}")
                    print(f"🔴 Active Groups: {data.get('active_groups', 0)}")
                    print(f"✅ Resolved Groups: {data.get('resolved_groups', 0)}")
                    print(f"🔍 Groups with RCA: {data.get('groups_with_rca', 0)}")
                    
                    avg_resolution = data.get("average_resolution_time")
                    if avg_resolution:
                        print(f"⏱️ Avg Resolution Time: {avg_resolution:.1f} hours")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error getting system summary: {e}")
    
    def cleanup_demo_data(self):
        """Clean up demo data (optional)"""
        print("🧹 Cleaning up demo data...")
        
        deleted_count = 0
        for alert_id in self.created_alerts:
            try:
                response = self.session.delete(f"{self.api_url}/alerts/{alert_id}")
                if response.status_code == 200:
                    deleted_count += 1
                time.sleep(0.1)
            except Exception as e:
                print(f"  ⚠️ Error deleting alert {alert_id}: {e}")
        
        print(f"🗑️ Deleted {deleted_count} demo alerts")
    
    def run_full_demo(self):
        """Run the complete demonstration"""
        print("🚀 Starting Alert Monitoring System Demo")
        print("=" * 60)
        
        # Check system health
        if not self.check_system_health():
            print("❌ System is not healthy. Please start the backend service.")
            return False
        
        print("✅ System is healthy and ready")
        
        # Create sample alerts
        alert_ids = self.create_sample_alerts()
        if not alert_ids:
            print("❌ Failed to create sample alerts")
            return False
        
        # Wait for processing
        if self.wait_for_processing():
            print("✅ Alert processing completed")
        else:
            print("⚠️ Alert processing may still be in progress")
        
        # Demonstrate RCA generation
        self.demonstrate_rca_generation()
        
        # Show system summary
        self.show_system_summary()
        
        print("=" * 60)
        print("🎉 Demo completed successfully!")
        print("🌐 Visit http://localhost:8501 to explore the web interface")
        print("📚 API documentation: http://localhost:8000/docs")
        
        # Ask if user wants to clean up
        try:
            cleanup = input("\n🧹 Would you like to clean up demo data? (y/N): ")
            if cleanup.lower().startswith('y'):
                self.cleanup_demo_data()
        except KeyboardInterrupt:
            print("\n👋 Demo finished")
        
        return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Alert Monitoring System Demo")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the Alert Monitoring System API"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup prompt"
    )
    
    args = parser.parse_args()
    
    demo = AlertMonitoringDemo(args.url)
    
    try:
        success = demo.run_full_demo()
        if not success:
            exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
        exit(0)
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
