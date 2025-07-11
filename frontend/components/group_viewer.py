"""
Alert Group Viewer Component for Streamlit frontend
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class GroupViewer:
    """Alert Group Viewer component"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def render(self):
        """Render the group viewer"""
        try:
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 Group Overview", "👥 Group List", "🔍 Search Groups"])
            
            with tab1:
                self.render_group_overview()
            
            with tab2:
                self.render_group_list()
            
            with tab3:
                self.render_group_search()
                
        except Exception as e:
            st.error(f"Failed to load group viewer: {e}")
            logger.error(f"Group viewer render error: {e}", exc_info=True)
    
    def render_group_overview(self):
        """Render group overview with statistics"""
        try:
            # Get group statistics
            stats_response = self.api_client.get_group_stats()
            
            if not stats_response.get("success"):
                st.error("Failed to load group statistics")
                return
            
            stats = stats_response.get("data", {})
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_groups = stats.get("total_groups", 0)
                st.metric("Total Groups", total_groups)
            
            with col2:
                active_groups = stats.get("active_groups", 0)
                st.metric("Active Groups", active_groups)
            
            with col3:
                resolved_groups = stats.get("resolved_groups", 0)
                st.metric("Resolved Groups", resolved_groups)
            
            with col4:
                groups_with_rca = stats.get("groups_with_rca", 0)
                st.metric("Groups with RCA", groups_with_rca)
            
            # Charts row
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Group Status Distribution")
                
                status_dist = stats.get("status_distribution", {})
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
                    
                    fig_status = px.pie(
                        df_status,
                        values="Count",
                        names="Status",
                        color="Status",
                        color_discrete_map=status_colors
                    )
                    
                    fig_status.update_traces(
                        textposition='inside',
                        textinfo='percent+label'
                    )
                    
                    fig_status.update_layout(
                        height=400,
                        margin=dict(t=20, b=20, l=20, r=20)
                    )
                    
                    st.plotly_chart(fig_status, use_container_width=True)
                else:
                    st.info("No group status data available")
            
            with col2:
                st.subheader("Group Priority Distribution")
                
                priority_dist = stats.get("priority_distribution", {})
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
                        height=400,
                        margin=dict(t=20, b=20, l=20, r=20),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_priority, use_container_width=True)
                else:
                    st.info("No group priority data available")
            
            # Average resolution time
            avg_resolution = stats.get("average_resolution_time")
            if avg_resolution:
                st.subheader("Average Resolution Time")
                
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=avg_resolution,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Hours"},
                    delta={'reference': 24},
                    gauge={
                        'axis': {'range': [None, 48]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 12], 'color': "lightgreen"},
                            {'range': [12, 24], 'color': "yellow"},
                            {'range': [24, 48], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 24
                        }
                    }
                ))
                
                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)
            
        except Exception as e:
            st.error(f"Failed to render group overview: {e}")
            logger.error(f"Group overview error: {e}", exc_info=True)
    
    def render_group_list(self):
        """Render list of alert groups"""
        try:
            # Filter controls
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=["Active", "Investigating", "Resolved", "Closed"],
                    default=[]
                )
            
            with col2:
                priority_filter = st.multiselect(
                    "Filter by Priority",
                    options=["Critical", "High", "Medium", "Low"],
                    default=[]
                )
            
            with col3:
                rca_filter = st.multiselect(
                    "Filter by RCA Status",
                    options=["Pending", "In Progress", "Completed", "Failed"],
                    default=[]
                )
            
            with col4:
                limit = st.selectbox(
                    "Show",
                    options=[10, 20, 50, 100],
                    index=1
                )
            
            # Get groups
            groups_response = self.api_client.list_groups(
                limit=limit,
                status=status_filter if status_filter else None,
                priority=priority_filter if priority_filter else None,
                rca_status=rca_filter if rca_filter else None
            )
            
            if not groups_response.get("success"):
                st.error("Failed to load groups")
                return
            
            groups = groups_response.get("data", [])
            total_groups = groups_response.get("total", 0)
            
            if not groups:
                st.info("No groups found matching the criteria")
                return
            
            st.write(f"Showing {len(groups)} of {total_groups} groups")
            
            # Display groups
            for group in groups:
                self.render_group_card(group)
                
        except Exception as e:
            st.error(f"Failed to render group list: {e}")
            logger.error(f"Group list error: {e}", exc_info=True)
    
    def render_group_card(self, group: Dict[str, Any]):
        """Render an individual group card"""
        # Determine status color
        status_colors = {
            "Active": "🔴",
            "Investigating": "🟡", 
            "Resolved": "🟢",
            "Closed": "⚫"
        }
        
        priority_colors = {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢"
        }
        
        status_icon = status_colors.get(group.get("status", ""), "⚪")
        priority_icon = priority_colors.get(group.get("priority", ""), "⚪")
        
        # Calculate duration
        created_at = pd.to_datetime(group.get("created_at"))
        duration_str = self.format_duration(group.get("duration_minutes", 0))
        
        with st.expander(
            f"{status_icon} {priority_icon} {group.get('title', 'Untitled Group')} "
            f"({group.get('alert_count', 0)} alerts)",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Group ID:** {group.get('id', 'Unknown')}")
                st.write(f"**Status:** {group.get('status', 'Unknown')}")
                st.write(f"**Priority:** {group.get('priority', 'Unknown')}")
                st.write(f"**Category:** {group.get('category', 'Unknown')}")
            
            with col2:
                st.write(f"**Alert Count:** {group.get('alert_count', 0)}")
                st.write(f"**Duration:** {duration_str}")
                st.write(f"**RCA Status:** {group.get('rca_status', 'Unknown')}")
                st.write(f"**Created:** {created_at.strftime('%Y-%m-%d %H:%M')}")
            
            with col3:
                affected_services = group.get("affected_services", [])
                affected_hosts = group.get("affected_hosts", [])
                
                st.write(f"**Services:** {', '.join(affected_services[:3])}")
                if len(affected_services) > 3:
                    st.write(f"... and {len(affected_services) - 3} more")
                
                st.write(f"**Hosts:** {', '.join(affected_hosts[:3])}")
                if len(affected_hosts) > 3:
                    st.write(f"... and {len(affected_hosts) - 3} more")
            
            st.write(f"**Description:** {group.get('description', 'No description')}")
            
            # Tags
            tags = group.get("tags", [])
            if tags:
                tag_str = " ".join([f"`{tag}`" for tag in tags])
                st.write(f"**Tags:** {tag_str}")
            
            # Severity distribution
            severity_dist = group.get("severity_distribution", {})
            if severity_dist:
                st.write("**Severity Distribution:**")
                severity_str = ", ".join([f"{k}: {v}" for k, v in severity_dist.items()])
                st.write(severity_str)
            
            # Action buttons
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                if st.button("View Details", key=f"details_{group['id']}"):
                    self.show_group_details(group["id"])
            
            with col2:
                if st.button("View RCA", key=f"rca_{group['id']}"):
                    self.show_group_rca(group["id"])
            
            with col3:
                if group.get("status") == "Active":
                    if st.button("Mark Investigating", key=f"investigating_{group['id']}"):
                        self.update_group_status(group["id"], "Investigating")
            
            with col4:
                if group.get("status") in ["Active", "Investigating"]:
                    if st.button("Resolve", key=f"resolve_{group['id']}"):
                        self.resolve_group(group["id"])
            
            with col5:
                if group.get("rca_status") in ["Pending", "Failed"]:
                    if st.button("Generate RCA", key=f"gen_rca_{group['id']}"):
                        self.generate_rca(group["id"])
    
    def render_group_search(self):
        """Render group search interface"""
        st.subheader("Advanced Group Search")
        
        with st.form("group_search"):
            col1, col2 = st.columns(2)
            
            with col1:
                query = st.text_input("Search Query", help="Search in title, description, and tags")
                
                status = st.multiselect(
                    "Status",
                    options=["Active", "Investigating", "Resolved", "Closed"]
                )
                
                priority = st.multiselect(
                    "Priority", 
                    options=["Critical", "High", "Medium", "Low"]
                )
            
            with col2:
                rca_status = st.multiselect(
                    "RCA Status",
                    options=["Pending", "In Progress", "Completed", "Failed"]
                )
                
                category = st.text_input("Category")
                assigned_to = st.text_input("Assigned To")
            
            # Date range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date")
            with col2:
                end_date = st.date_input("End Date")
            
            submitted = st.form_submit_button("Search Groups")
        
        if submitted:
            # Build search request
            search_data = {
                "limit": 50,
                "offset": 0
            }
            
            if query:
                search_data["query"] = query
            if status:
                search_data["status"] = status
            if priority:
                search_data["priority"] = priority
            if rca_status:
                search_data["rca_status"] = rca_status
            if category:
                search_data["category"] = category
            if assigned_to:
                search_data["assigned_to"] = assigned_to
            if start_date:
                search_data["start_date"] = start_date.isoformat()
            if end_date:
                search_data["end_date"] = end_date.isoformat()
            
            try:
                # Perform search
                search_response = self.api_client.search_groups(search_data)
                
                if search_response.get("success"):
                    results = search_response.get("data", [])
                    total = search_response.get("total", 0)
                    
                    st.success(f"Found {total} groups matching your criteria")
                    
                    if results:
                        for group in results:
                            self.render_group_card(group)
                    else:
                        st.info("No groups found matching the criteria")
                else:
                    st.error("Search failed")
                    
            except Exception as e:
                st.error(f"Search error: {e}")
    
    def show_group_details(self, group_id: str):
        """Show detailed group information"""
        try:
            response = self.api_client.get_group_with_alerts(group_id)
            
            if not response.get("success"):
                st.error("Failed to load group details")
                return
            
            group_data = response.get("data", {})
            alerts = group_data.get("alerts", [])
            
            st.subheader(f"Group Details: {group_data.get('title', 'Unknown')}")
            
            # Group information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**ID:** {group_data.get('id')}")
                st.write(f"**Status:** {group_data.get('status')}")
                st.write(f"**Priority:** {group_data.get('priority')}")
                st.write(f"**Category:** {group_data.get('category')}")
                st.write(f"**Alert Count:** {group_data.get('alert_count')}")
            
            with col2:
                st.write(f"**RCA Status:** {group_data.get('rca_status')}")
                st.write(f"**Created:** {group_data.get('created_at')}")
                st.write(f"**Updated:** {group_data.get('updated_at')}")
                st.write(f"**Duration:** {self.format_duration(group_data.get('duration_minutes', 0))}")
                
                if group_data.get('assigned_to'):
                    st.write(f"**Assigned To:** {group_data.get('assigned_to')}")
            
            st.write(f"**Description:** {group_data.get('description')}")
            
            # Affected resources
            if group_data.get('affected_services'):
                st.write(f"**Affected Services:** {', '.join(group_data.get('affected_services'))}")
            
            if group_data.get('affected_hosts'):
                st.write(f"**Affected Hosts:** {', '.join(group_data.get('affected_hosts'))}")
            
            if group_data.get('affected_environments'):
                st.write(f"**Affected Environments:** {', '.join(group_data.get('affected_environments'))}")
            
            # Alerts in group
            if alerts:
                st.subheader("Alerts in Group")
                
                df_alerts = pd.DataFrame(alerts)
                df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'])
                
                st.dataframe(
                    df_alerts[[
                        'id', 'title', 'severity', 'status', 'source_system',
                        'service_name', 'host_name', 'timestamp'
                    ]],
                    use_container_width=True
                )
            else:
                st.info("No alerts found in this group")
                
        except Exception as e:
            st.error(f"Failed to show group details: {e}")
    
    def show_group_rca(self, group_id: str):
        """Show RCA for group"""
        try:
            response = self.api_client.get_rca(group_id)
            
            if not response.get("success"):
                st.error("Failed to load RCA")
                return
            
            rca_data = response.get("data", {})
            rca_content = rca_data.get("rca_content")
            
            if rca_content:
                st.subheader(f"Root Cause Analysis - Group {group_id}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Status:** {rca_data.get('rca_status')}")
                
                with col2:
                    confidence = rca_data.get("confidence")
                    if confidence:
                        st.write(f"**Confidence:** {confidence:.2%}")
                
                with col3:
                    generated_at = rca_data.get("generated_at")
                    if generated_at:
                        st.write(f"**Generated:** {pd.to_datetime(generated_at).strftime('%Y-%m-%d %H:%M')}")
                
                st.markdown("---")
                st.markdown(rca_content)
            else:
                st.info("No RCA available for this group")
                
                if st.button("Generate RCA", key=f"generate_rca_{group_id}"):
                    self.generate_rca(group_id)
                    
        except Exception as e:
            st.error(f"Failed to show RCA: {e}")
    
    def update_group_status(self, group_id: str, status: str):
        """Update group status"""
        try:
            update_data = {"status": status}
            response = self.api_client.update_group(group_id, update_data)
            
            if response.get("success"):
                st.success(f"Group status updated to {status}")
                st.experimental_rerun()
            else:
                st.error("Failed to update group status")
                
        except Exception as e:
            st.error(f"Failed to update status: {e}")
    
    def resolve_group(self, group_id: str):
        """Resolve a group"""
        resolution_notes = st.text_area(
            "Resolution Notes (optional)",
            key=f"resolution_{group_id}",
            help="Add notes about how the issue was resolved"
        )
        
        if st.button("Confirm Resolution", key=f"confirm_resolve_{group_id}"):
            try:
                response = self.api_client.resolve_group(group_id, resolution_notes)
                
                if response.get("success"):
                    st.success("Group marked as resolved")
                    st.experimental_rerun()
                else:
                    st.error("Failed to resolve group")
                    
            except Exception as e:
                st.error(f"Failed to resolve group: {e}")
    
    def generate_rca(self, group_id: str):
        """Generate RCA for a group"""
        try:
            with st.spinner("Generating RCA... This may take a few moments."):
                response = self.api_client.generate_rca(group_id)
                
                if response.get("success"):
                    if response.get("rca_content"):
                        st.success("RCA generated successfully!")
                        st.experimental_rerun()
                    else:
                        st.info("RCA generation started in background. Please check back shortly.")
                else:
                    st.error("Failed to generate RCA")
                    
        except Exception as e:
            st.error(f"Failed to generate RCA: {e}")
    
    def format_duration(self, duration_minutes: float) -> str:
        """Format duration in a human-readable way"""
        if duration_minutes < 60:
            return f"{duration_minutes:.0f} minutes"
        elif duration_minutes < 1440:  # 24 hours
            hours = duration_minutes / 60
            return f"{hours:.1f} hours"
        else:
            days = duration_minutes / 1440
            return f"{days:.1f} days"
