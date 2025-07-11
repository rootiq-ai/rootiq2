"""
Alert Dashboard Component for Streamlit frontend
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class AlertDashboard:
    """Alert Dashboard component"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def render(self):
        """Render the alert dashboard"""
        try:
            # Get statistics
            stats = self.api_client.get_cached_stats()
            alert_stats = stats.get("alerts", {})
            group_stats = stats.get("groups", {})
            
            # Render metrics row
            self.render_metrics(alert_stats, group_stats)
            
            # Create tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Recent Alerts", "🔍 Search", "➕ Create Alert"])
            
            with tab1:
                self.render_overview(alert_stats, group_stats)
            
            with tab2:
                self.render_recent_alerts()
            
            with tab3:
                self.render_search_interface()
            
            with tab4:
                self.render_create_alert_form()
                
        except Exception as e:
            st.error(f"Failed to load dashboard: {e}")
            logger.error(f"Dashboard render error: {e}", exc_info=True)
    
    def render_metrics(self, alert_stats: Dict[str, Any], group_stats: Dict[str, Any]):
        """Render key metrics at the top"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_alerts = alert_stats.get("total_alerts", 0)
            recent_alerts = alert_stats.get("recent_alerts_24h", 0)
            delta = f"+{recent_alerts}" if recent_alerts > 0 else None
            
            st.metric(
                label="Total Alerts",
                value=total_alerts,
                delta=delta,
                help="Total number of alerts in the system"
            )
        
        with col2:
            total_groups = group_stats.get("total_groups", 0)
            active_groups = group_stats.get("active_groups", 0)
            
            st.metric(
                label="Alert Groups",
                value=total_groups,
                delta=f"{active_groups} active",
                help="Total alert groups (active groups shown as delta)"
            )
        
        with col3:
            groups_with_rca = group_stats.get("groups_with_rca", 0)
            rca_completion_rate = 0
            if total_groups > 0:
                rca_completion_rate = round((groups_with_rca / total_groups) * 100, 1)
            
            st.metric(
                label="RCA Completion",
                value=f"{rca_completion_rate}%",
                delta=f"{groups_with_rca} completed",
                help="Percentage of groups with completed RCA"
            )
        
        with col4:
            avg_resolution_time = group_stats.get("average_resolution_time")
            if avg_resolution_time:
                avg_time_str = f"{avg_resolution_time:.1f}h"
                delta_color = "inverse" if avg_resolution_time > 24 else "normal"
            else:
                avg_time_str = "N/A"
                delta_color = "off"
            
            st.metric(
                label="Avg Resolution",
                value=avg_time_str,
                help="Average time to resolve incidents"
            )
        
        with col5:
            # Calculate critical/high severity percentage
            severity_dist = alert_stats.get("severity_distribution", {})
            critical_count = severity_dist.get("Critical", 0)
            high_count = severity_dist.get("High", 0)
            total_severity = sum(severity_dist.values()) if severity_dist else 1
            
            critical_pct = round(((critical_count + high_count) / total_severity) * 100, 1)
            color = "inverse" if critical_pct > 20 else "normal"
            
            st.metric(
                label="High Severity",
                value=f"{critical_pct}%",
                delta=f"{critical_count + high_count} alerts",
                help="Percentage of critical and high severity alerts"
            )
    
    def render_overview(self, alert_stats: Dict[str, Any], group_stats: Dict[str, Any]):
        """Render overview charts and statistics"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Alert Distribution by Severity")
            
            # Severity distribution pie chart
            severity_dist = alert_stats.get("severity_distribution", {})
            if severity_dist:
                df_severity = pd.DataFrame(
                    list(severity_dist.items()),
                    columns=["Severity", "Count"]
                )
                
                # Define colors for severity levels
                color_map = {
                    "Critical": "#ff4757",
                    "High": "#ff6348", 
                    "Medium": "#ffa502",
                    "Low": "#2ed573",
                    "Info": "#54a0ff"
                }
                
                fig_severity = px.pie(
                    df_severity,
                    values="Count",
                    names="Severity",
                    color="Severity",
                    color_discrete_map=color_map,
                    hole=0.4
                )
                
                fig_severity.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                )
                
                fig_severity.update_layout(
                    showlegend=True,
                    height=400,
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                
                st.plotly_chart(fig_severity, use_container_width=True)
            else:
                st.info("No alert data available")
        
        with col2:
            st.subheader("Alert Sources")
            
            # Source distribution bar chart
            source_dist = alert_stats.get("source_distribution", {})
            if source_dist:
                df_sources = pd.DataFrame(
                    list(source_dist.items()),
                    columns=["Source", "Count"]
                ).sort_values("Count", ascending=True)
                
                fig_sources = px.bar(
                    df_sources,
                    x="Count",
                    y="Source",
                    orientation="h",
                    color="Count",
                    color_continuous_scale="viridis"
                )
                
                fig_sources.update_layout(
                    height=400,
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=False
                )
                
                fig_sources.update_traces(
                    hovertemplate='<b>%{y}</b><br>Alerts: %{x}<extra></extra>'
                )
                
                st.plotly_chart(fig_sources, use_container_width=True)
            else:
                st.info("No source data available")
        
        # Group status overview
        st.subheader("Group Status Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Group status distribution
            status_dist = group_stats.get("status_distribution", {})
            if status_dist:
                df_status = pd.DataFrame(
                    list(status_dist.items()),
                    columns=["Status", "Count"]
                )
                
                status_colors = {
                    "Active": "#ff4757",
                    "Investigating": "#ffa502",
                    "Resolved": "#2ed573",
                    "Closed": "#747d8c"
                }
                
                fig_status = px.bar(
                    df_status,
                    x="Status",
                    y="Count",
                    color="Status",
                    color_discrete_map=status_colors
                )
                
                fig_status.update_layout(
                    height=300,
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=False
                )
                
                st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Priority distribution
            priority_dist = group_stats.get("priority_distribution", {})
            if priority_dist:
                df_priority = pd.DataFrame(
                    list(priority_dist.items()),
                    columns=["Priority", "Count"]
                )
                
                priority_colors = {
                    "Critical": "#ff4757",
                    "High": "#ff6348",
                    "Medium": "#ffa502", 
                    "Low": "#2ed573"
                }
                
                fig_priority = px.bar(
                    df_priority,
                    x="Priority",
                    y="Count",
                    color="Priority",
                    color_discrete_map=priority_colors
                )
                
                fig_priority.update_layout(
                    height=300,
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=False
                )
                
                st.plotly_chart(fig_priority, use_container_width=True)
        
        with col3:
            # Recent activity gauge
            recent_alerts = alert_stats.get("recent_alerts_24h", 0)
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=recent_alerts,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Alerts (24h)"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 25], 'color': "lightgray"},
                        {'range': [25, 50], 'color': "yellow"},
                        {'range': [50, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 75
                    }
                }
            ))
            
            fig_gauge.update_layout(
                height=300,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    def render_recent_alerts(self):
        """Render recent alerts table"""
        try:
            # Get recent alerts
            alerts_response = self.api_client.get_cached_alerts(limit=100)
            
            if not alerts_response.get("success"):
                st.error("Failed to load alerts")
                return
            
            alerts = alerts_response.get("data", [])
            
            if not alerts:
                st.info("No alerts found")
                return
            
            # Create DataFrame
            df_alerts = pd.DataFrame(alerts)
            
            # Convert timestamp to datetime
            df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'])
            df_alerts['created_at'] = pd.to_datetime(df_alerts['created_at'])
            
            # Sort by timestamp (most recent first)
            df_alerts = df_alerts.sort_values('timestamp', ascending=False)
            
            # Filter options
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                severity_filter = st.multiselect(
                    "Filter by Severity",
                    options=df_alerts['severity'].unique(),
                    default=[]
                )
            
            with col2:
                status_filter = st.multiselect(
                    "Filter by Status", 
                    options=df_alerts['status'].unique(),
                    default=[]
                )
            
            with col3:
                source_filter = st.multiselect(
                    "Filter by Source",
                    options=df_alerts['source_system'].unique(),
                    default=[]
                )
            
            with col4:
                limit = st.selectbox(
                    "Show",
                    options=[25, 50, 100, 200],
                    index=1
                )
            
            # Apply filters
            filtered_df = df_alerts.copy()
            
            if severity_filter:
                filtered_df = filtered_df[filtered_df['severity'].isin(severity_filter)]
            
            if status_filter:
                filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
            
            if source_filter:
                filtered_df = filtered_df[filtered_df['source_system'].isin(source_filter)]
            
            # Limit results
            filtered_df = filtered_df.head(limit)
            
            # Display table
            st.dataframe(
                filtered_df[[
                    'id', 'title', 'severity', 'status', 'source_system',
                    'service_name', 'host_name', 'environment', 'timestamp'
                ]],
                use_container_width=True,
                height=400,
                column_config={
                    "id": st.column_config.TextColumn("ID", width="small"),
                    "title": st.column_config.TextColumn("Title", width="large"),
                    "severity": st.column_config.TextColumn("Severity", width="small"),
                    "status": st.column_config.TextColumn("Status", width="small"),
                    "source_system": st.column_config.TextColumn("Source", width="medium"),
                    "service_name": st.column_config.TextColumn("Service", width="medium"),
                    "host_name": st.column_config.TextColumn("Host", width="medium"),
                    "environment": st.column_config.TextColumn("Environment", width="small"),
                    "timestamp": st.column_config.DatetimeColumn("Time", width="medium")
                }
            )
            
            # Alert details on selection
            if not filtered_df.empty:
                selected_indices = st.multiselect(
                    "Select alerts for details:",
                    options=range(len(filtered_df)),
                    format_func=lambda x: f"{filtered_df.iloc[x]['title'][:50]}..."
                )
                
                if selected_indices:
                    for idx in selected_indices:
                        alert = filtered_df.iloc[idx]
                        
                        with st.expander(f"📋 {alert['title']}", expanded=False):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**ID:** {alert['id']}")
                                st.write(f"**Severity:** {alert['severity']}")
                                st.write(f"**Status:** {alert['status']}")
                                st.write(f"**Source:** {alert['source_system']}")
                                st.write(f"**Environment:** {alert['environment']}")
                            
                            with col2:
                                st.write(f"**Service:** {alert['service_name']}")
                                st.write(f"**Host:** {alert['host_name']}")
                                st.write(f"**Created:** {alert['created_at']}")
                                st.write(f"**Group ID:** {alert.get('group_id', 'Not assigned')}")
                            
                            st.write(f"**Description:** {alert['description']}")
                            
                            if alert.get('tags'):
                                st.write(f"**Tags:** {', '.join(alert['tags'])}")
                            
                            if alert.get('metrics'):
                                st.write("**Metrics:**")
                                st.json(alert['metrics'])
                            
                            # Action buttons
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if st.button(f"Find Similar", key=f"similar_{alert['id']}"):
                                    self.show_similar_alerts(alert['id'])
                            
                            with col2:
                                if st.button(f"Classify", key=f"classify_{alert['id']}"):
                                    self.classify_alert(alert['id'])
                            
                            with col3:
                                if st.button(f"View Group", key=f"group_{alert['id']}"):
                                    if alert.get('group_id'):
                                        st.session_state.selected_group_id = alert['group_id']
                                        st.session_state.current_page = 'Alert Groups'
                                        st.experimental_rerun()
                                    else:
                                        st.warning("Alert not assigned to any group")
        
        except Exception as e:
            st.error(f"Failed to load recent alerts: {e}")
            logger.error(f"Recent alerts error: {e}", exc_info=True)
    
    def render_search_interface(self):
        """Render alert search interface"""
        st.subheader("Advanced Alert Search")
        
        # Search form
        with st.form("alert_search"):
            col1, col2 = st.columns(2)
            
            with col1:
                query = st.text_input("Search Query", help="Search in title, description, and tags")
                
                severity = st.multiselect(
                    "Severity",
                    options=["Critical", "High", "Medium", "Low", "Info"]
                )
                
                status = st.multiselect(
                    "Status",
                    options=["Open", "Acknowledged", "Resolved", "Closed"]
                )
            
            with col2:
                service_name = st.text_input("Service Name")
                environment = st.text_input("Environment")
                tags = st.text_input("Tags (comma-separated)")
            
            # Date range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
            
            submitted = st.form_submit_button("Search Alerts")
        
        if submitted:
            # Build search request
            search_data = {
                "limit": 100,
                "offset": 0
            }
            
            if query:
                search_data["query"] = query
            if severity:
                search_data["severity"] = severity
            if status:
                search_data["status"] = status
            if service_name:
                search_data["service_name"] = service_name
            if environment:
                search_data["environment"] = environment
            if tags:
                search_data["tags"] = [tag.strip() for tag in tags.split(",")]
            if start_date:
                search_data["start_date"] = start_date.isoformat()
            if end_date:
                search_data["end_date"] = end_date.isoformat()
            
            try:
                # Perform search
                search_response = self.api_client.search_alerts(search_data)
                
                if search_response.get("success"):
                    results = search_response.get("data", [])
                    total = search_response.get("total", 0)
                    
                    st.success(f"Found {total} alerts matching your criteria")
                    
                    if results:
                        # Display results
                        df_results = pd.DataFrame(results)
                        df_results['timestamp'] = pd.to_datetime(df_results['timestamp'])
                        
                        st.dataframe(
                            df_results[[
                                'id', 'title', 'severity', 'status', 'source_system',
                                'service_name', 'timestamp'
                            ]],
                            use_container_width=True
                        )
                else:
                    st.error("Search failed")
                    
            except Exception as e:
                st.error(f"Search error: {e}")
    
    def render_create_alert_form(self):
        """Render form to create new alerts"""
        st.subheader("Create New Alert")
        
        with st.form("create_alert"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Alert Title*", help="Brief description of the alert")
                
                severity = st.selectbox(
                    "Severity*",
                    options=["Critical", "High", "Medium", "Low", "Info"],
                    index=2
                )
                
                source_system = st.selectbox(
                    "Source System*",
                    options=["Prometheus", "Grafana", "Nagios", "Zabbix", "DataDog", "New Relic", "Manual"],
                    index=6
                )
                
                service_name = st.text_input("Service Name")
            
            with col2:
                environment = st.selectbox(
                    "Environment",
                    options=["production", "staging", "development", "testing"],
                    index=0
                )
                
                host_name = st.text_input("Host Name")
                
                tags = st.text_input("Tags (comma-separated)", value="manual")
                
                external_id = st.text_input("External ID", help="ID from source monitoring system")
            
            description = st.text_area(
                "Description*",
                help="Detailed description of the alert",
                height=100
            )
            
            # Metrics section
            st.subheader("Metrics (Optional)")
            metric_name = st.text_input("Metric Name")
            metric_value = st.number_input("Metric Value", value=0.0)
            
            submitted = st.form_submit_button("Create Alert", type="primary")
        
        if submitted:
            # Validate required fields
            if not title or not description:
                st.error("Title and Description are required fields")
                return
            
            # Build alert data
            alert_data = {
                "title": title,
                "description": description,
                "severity": severity,
                "source_system": source_system
            }
            
            if service_name:
                alert_data["service_name"] = service_name
            if host_name:
                alert_data["host_name"] = host_name
            if environment:
                alert_data["environment"] = environment
            if external_id:
                alert_data["external_id"] = external_id
            
            # Process tags
            if tags:
                alert_data["tags"] = [tag.strip() for tag in tags.split(",")]
            
            # Process metrics
            if metric_name and metric_value:
                alert_data["metrics"] = {metric_name: metric_value}
            
            try:
                # Create alert
                response = self.api_client.create_alert(alert_data)
                
                if response.get("success"):
                    alert = response.get("data")
                    st.success(f"✅ Alert created successfully!")
                    st.info(f"Alert ID: {alert['id']}")
                    
                    # Clear cache to refresh data
                    st.cache_data.clear()
                    
                    # Show option to create sample alerts
                    if st.button("Create Sample Alerts for Demo"):
                        with st.spinner("Creating sample alerts..."):
                            results = self.api_client.bulk_create_sample_alerts(5)
                            st.success(f"Created {len(results)} sample alerts")
                            st.cache_data.clear()
                            st.experimental_rerun()
                else:
                    st.error("Failed to create alert")
                    
            except Exception as e:
                st.error(f"Failed to create alert: {e}")
    
    def show_similar_alerts(self, alert_id: str):
        """Show similar alerts for given alert ID"""
        try:
            response = self.api_client.find_similar_alerts(alert_id)
            
            if response.get("success"):
                similar_alerts = response.get("data", [])
                
                if similar_alerts:
                    st.subheader(f"Similar Alerts to {alert_id}")
                    
                    for similar in similar_alerts:
                        alert = similar["alert"]
                        similarity_score = similar["similarity_score"]
                        
                        with st.expander(f"🔗 {alert['title']} (Similarity: {similarity_score:.2f})"):
                            st.write(f"**Description:** {alert['description']}")
                            st.write(f"**Severity:** {alert['severity']}")
                            st.write(f"**Service:** {alert.get('service_name', 'N/A')}")
                            st.write(f"**Host:** {alert.get('host_name', 'N/A')}")
                else:
                    st.info("No similar alerts found")
            else:
                st.error("Failed to find similar alerts")
                
        except Exception as e:
            st.error(f"Error finding similar alerts: {e}")
    
    def classify_alert(self, alert_id: str):
        """Classify alert using AI"""
        try:
            with st.spinner("Classifying alert..."):
                response = self.api_client.classify_alert(alert_id)
                
                if response.get("success"):
                    data = response.get("data", {})
                    
                    st.success("Alert classified successfully!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Category:** {data.get('category', 'Unknown')}")
                        st.write(f"**Keywords:** {', '.join(data.get('keywords', []))}")
                    
                    with col2:
                        st.write("**AI Summary:**")
                        st.write(data.get('summary', 'No summary available'))
                else:
                    st.error("Failed to classify alert")
                    
        except Exception as e:
            st.error(f"Error classifying alert: {e}")
