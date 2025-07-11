"""
RCA Display Component for Streamlit frontend
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)

class RCADisplay:
    """RCA Display and Analysis component"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def render(self):
        """Render the RCA analysis interface"""
        try:
            # Create tabs for different RCA views
            tab1, tab2, tab3 = st.tabs(["📊 RCA Overview", "📋 RCA Reports", "🔍 RCA Search"])
            
            with tab1:
                self.render_rca_overview()
            
            with tab2:
                self.render_rca_reports()
            
            with tab3:
                self.render_rca_search()
                
        except Exception as e:
            st.error(f"Failed to load RCA display: {e}")
            logger.error(f"RCA display render error: {e}", exc_info=True)
    
    def render_rca_overview(self):
        """Render RCA overview dashboard"""
        try:
            # Get group statistics to understand RCA completion
            stats_response = self.api_client.get_group_stats()
            
            if not stats_response.get("success"):
                st.error("Failed to load RCA statistics")
                return
            
            stats = stats_response.get("data", {})
            
            # RCA Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_groups = stats.get("total_groups", 0)
                st.metric("Total Groups", total_groups)
            
            with col2:
                groups_with_rca = stats.get("groups_with_rca", 0)
                st.metric("RCAs Completed", groups_with_rca)
            
            with col3:
                if total_groups > 0:
                    completion_rate = (groups_with_rca / total_groups) * 100
                else:
                    completion_rate = 0
                st.metric("Completion Rate", f"{completion_rate:.1f}%")
            
            with col4:
                pending_rca = total_groups - groups_with_rca
                st.metric("Pending RCAs", pending_rca)
            
            # Get groups with RCA status breakdown
            groups_response = self.api_client.list_groups(limit=100)
            
            if groups_response.get("success"):
                groups = groups_response.get("data", [])
                
                # RCA Status Distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("RCA Status Distribution")
                    
                    rca_status_counts = {}
                    for group in groups:
                        rca_status = group.get("rca_status", "Unknown")
                        rca_status_counts[rca_status] = rca_status_counts.get(rca_status, 0) + 1
                    
                    if rca_status_counts:
                        df_rca_status = pd.DataFrame(
                            list(rca_status_counts.items()),
                            columns=["RCA Status", "Count"]
                        )
                        
                        rca_colors = {
                            "Completed": "#2ed573",
                            "In Progress": "#ffa502",
                            "Pending": "#ff6348",
                            "Failed": "#ff4757"
                        }
                        
                        fig_rca = px.pie(
                            df_rca_status,
                            values="Count",
                            names="RCA Status",
                            color="RCA Status",
                            color_discrete_map=rca_colors
                        )
                        
                        fig_rca.update_traces(
                            textposition='inside',
                            textinfo='percent+label'
                        )
                        
                        fig_rca.update_layout(
                            height=400,
                            margin=dict(t=20, b=20, l=20, r=20)
                        )
                        
                        st.plotly_chart(fig_rca, use_container_width=True)
                
                with col2:
                    st.subheader("RCA Quality Metrics")
                    
                    # Calculate confidence scores for completed RCAs
                    completed_groups = [g for g in groups if g.get("rca_status") == "Completed"]
                    
                    if completed_groups:
                        confidence_scores = []
                        for group in completed_groups:
                            if group.get("rca_confidence"):
                                confidence_scores.append(group["rca_confidence"])
                        
                        if confidence_scores:
                            avg_confidence = sum(confidence_scores) / len(confidence_scores)
                            
                            # Create confidence histogram
                            fig_conf = px.histogram(
                                x=confidence_scores,
                                nbins=10,
                                title="RCA Confidence Score Distribution",
                                labels={"x": "Confidence Score", "y": "Count"}
                            )
                            
                            fig_conf.add_vline(
                                x=avg_confidence,
                                line_dash="dash",
                                line_color="red",
                                annotation_text=f"Avg: {avg_confidence:.2f}"
                            )
                            
                            fig_conf.update_layout(
                                height=400,
                                margin=dict(t=20, b=20, l=20, r=20)
                            )
                            
                            st.plotly_chart(fig_conf, use_container_width=True)
                        else:
                            st.info("No confidence scores available")
                    else:
                        st.info("No completed RCAs available")
                
                # RCA Generation Timeline
                st.subheader("RCA Generation Timeline")
                
                # Filter groups with RCA generation dates
                rca_timeline_data = []
                for group in groups:
                    if group.get("rca_generated_at"):
                        rca_timeline_data.append({
                            "date": pd.to_datetime(group["rca_generated_at"]).date(),
                            "group_id": group["id"],
                            "title": group.get("title", "Unknown"),
                            "confidence": group.get("rca_confidence", 0)
                        })
                
                if rca_timeline_data:
                    df_timeline = pd.DataFrame(rca_timeline_data)
                    
                    # Group by date and count RCAs
                    daily_counts = df_timeline.groupby("date").size().reset_index(name="RCAs_Generated")
                    
                    fig_timeline = px.line(
                        daily_counts,
                        x="date",
                        y="RCAs_Generated",
                        title="RCAs Generated Over Time",
                        markers=True
                    )
                    
                    fig_timeline.update_layout(
                        height=300,
                        margin=dict(t=20, b=20, l=20, r=20)
                    )
                    
                    st.plotly_chart(fig_timeline, use_container_width=True)
                else:
                    st.info("No RCA generation timeline data available")
            
            else:
                st.error("Failed to load group data for RCA analysis")
                
        except Exception as e:
            st.error(f"Failed to render RCA overview: {e}")
            logger.error(f"RCA overview error: {e}", exc_info=True)
    
    def render_rca_reports(self):
        """Render list of RCA reports"""
        try:
            # Filter controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                rca_status_filter = st.multiselect(
                    "RCA Status",
                    options=["Completed", "In Progress", "Pending", "Failed"],
                    default=["Completed"]
                )
            
            with col2:
                priority_filter = st.multiselect(
                    "Group Priority",
                    options=["Critical", "High", "Medium", "Low"],
                    default=[]
                )
            
            with col3:
                confidence_threshold = st.slider(
                    "Min Confidence Score",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1
                )
            
            # Get groups
            groups_response = self.api_client.list_groups(
                limit=100,
                rca_status=rca_status_filter if rca_status_filter else None,
                priority=priority_filter if priority_filter else None
            )
            
            if not groups_response.get("success"):
                st.error("Failed to load groups")
                return
            
            groups = groups_response.get("data", [])
            
            # Filter by confidence if needed
            if confidence_threshold > 0:
                groups = [
                    g for g in groups 
                    if g.get("rca_confidence", 0) >= confidence_threshold
                ]
            
            if not groups:
                st.info("No RCA reports found matching the criteria")
                return
            
            st.write(f"Found {len(groups)} RCA reports")
            
            # Display RCA reports
            for group in groups:
                self.render_rca_report_card(group)
                
        except Exception as e:
            st.error(f"Failed to render RCA reports: {e}")
            logger.error(f"RCA reports error: {e}", exc_info=True)
    
    def render_rca_report_card(self, group: Dict[str, Any]):
        """Render an individual RCA report card"""
        rca_status = group.get("rca_status", "Unknown")
        confidence = group.get("rca_confidence")
        
        # Status icons
        status_icons = {
            "Completed": "✅",
            "In Progress": "🔄",
            "Pending": "⏳",
            "Failed": "❌"
        }
        
        status_icon = status_icons.get(rca_status, "❓")
        
        # Confidence indicator
        confidence_str = ""
        if confidence is not None:
            confidence_str = f" (Confidence: {confidence:.1%})"
        
        with st.expander(
            f"{status_icon} {group.get('title', 'Unknown Group')}{confidence_str}",
            expanded=False
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Group ID:** {group.get('id')}")
                st.write(f"**Priority:** {group.get('priority')}")
                st.write(f"**Status:** {group.get('status')}")
                st.write(f"**RCA Status:** {rca_status}")
            
            with col2:
                st.write(f"**Alert Count:** {group.get('alert_count', 0)}")
                st.write(f"**Category:** {group.get('category', 'Unknown')}")
                
                if group.get('rca_generated_at'):
                    generated_at = pd.to_datetime(group['rca_generated_at'])
                    st.write(f"**RCA Generated:** {generated_at.strftime('%Y-%m-%d %H:%M')}")
                
                if confidence is not None:
                    st.write(f"**Confidence:** {confidence:.1%}")
            
            st.write(f"**Description:** {group.get('description', 'No description')}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("View Full RCA", key=f"view_rca_{group['id']}"):
                    self.show_full_rca(group["id"])
            
            with col2:
                if rca_status == "Completed":
                    if st.button("Export RCA", key=f"export_rca_{group['id']}"):
                        self.export_rca(group["id"])
            
            with col3:
                if rca_status in ["Failed", "Pending"]:
                    if st.button("Regenerate RCA", key=f"regen_rca_{group['id']}"):
                        self.regenerate_rca(group["id"])
    
    def render_rca_search(self):
        """Render RCA search interface"""
        st.subheader("Search RCA Reports")
        
        with st.form("rca_search"):
            col1, col2 = st.columns(2)
            
            with col1:
                query = st.text_input(
                    "Search in RCA Content",
                    help="Search for keywords in RCA reports"
                )
                
                group_priority = st.multiselect(
                    "Group Priority",
                    options=["Critical", "High", "Medium", "Low"]
                )
            
            with col2:
                category = st.text_input("Category")
                
                min_confidence = st.slider(
                    "Minimum Confidence",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.1
                )
            
            # Date range
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("RCA Generated After")
            with col2:
                end_date = st.date_input("RCA Generated Before")
            
            submitted = st.form_submit_button("Search RCAs")
        
        if submitted:
            try:
                # Get all groups first (since we need to search RCA content)
                groups_response = self.api_client.list_groups(limit=200)
                
                if not groups_response.get("success"):
                    st.error("Failed to search RCAs")
                    return
                
                groups = groups_response.get("data", [])
                
                # Filter groups based on criteria
                filtered_groups = []
                
                for group in groups:
                    # Skip if no RCA
                    if group.get("rca_status") != "Completed":
                        continue
                    
                    # Filter by priority
                    if group_priority and group.get("priority") not in group_priority:
                        continue
                    
                    # Filter by category
                    if category and category.lower() not in group.get("category", "").lower():
                        continue
                    
                    # Filter by confidence
                    if group.get("rca_confidence", 0) < min_confidence:
                        continue
                    
                    # Filter by date
                    if group.get("rca_generated_at"):
                        rca_date = pd.to_datetime(group["rca_generated_at"]).date()
                        if start_date and rca_date < start_date:
                            continue
                        if end_date and rca_date > end_date:
                            continue
                    
                    # Search in RCA content if query provided
                    if query:
                        # Get full RCA content
                        try:
                            rca_response = self.api_client.get_rca(group["id"])
                            if rca_response.get("success"):
                                rca_data = rca_response.get("data", {})
                                rca_content = rca_data.get("rca_content", "")
                                
                                if query.lower() not in rca_content.lower():
                                    continue
                        except:
                            continue
                    
                    filtered_groups.append(group)
                
                st.success(f"Found {len(filtered_groups)} RCA reports matching your criteria")
                
                if filtered_groups:
                    for group in filtered_groups:
                        self.render_rca_report_card(group)
                else:
                    st.info("No RCA reports found matching the search criteria")
                    
            except Exception as e:
                st.error(f"Search error: {e}")
    
    def show_full_rca(self, group_id: str):
        """Show full RCA content"""
        try:
            response = self.api_client.get_rca(group_id)
            
            if not response.get("success"):
                st.error("Failed to load RCA")
                return
            
            rca_data = response.get("data", {})
            rca_content = rca_data.get("rca_content")
            
            if not rca_content:
                st.warning("No RCA content available")
                return
            
            st.subheader(f"Full RCA Report - Group {group_id}")
            
            # RCA metadata
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Status:** {rca_data.get('rca_status', 'Unknown')}")
            
            with col2:
                confidence = rca_data.get("confidence")
                if confidence is not None:
                    st.write(f"**Confidence:** {confidence:.1%}")
            
            with col3:
                generated_at = rca_data.get("generated_at")
                if generated_at:
                    st.write(f"**Generated:** {pd.to_datetime(generated_at).strftime('%Y-%m-%d %H:%M')}")
            
            st.markdown("---")
            
            # Display RCA content with formatting
            self.format_and_display_rca(rca_content)
            
            # Analysis tools
            st.markdown("---")
            st.subheader("RCA Analysis Tools")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Extract Key Points", key=f"extract_{group_id}"):
                    self.extract_key_points(rca_content)
            
            with col2:
                if st.button("Word Cloud", key=f"wordcloud_{group_id}"):
                    self.generate_word_frequency(rca_content)
            
            with col3:
                if st.button("Export as PDF", key=f"pdf_{group_id}"):
                    st.info("PDF export feature would be implemented here")
            
        except Exception as e:
            st.error(f"Failed to show full RCA: {e}")
    
    def format_and_display_rca(self, rca_content: str):
        """Format and display RCA content with better formatting"""
        # Split content into sections
        sections = re.split(r'\n(?=\d+\.|\*\*)', rca_content)
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if it's a numbered section
            if re.match(r'^\d+\.', section):
                lines = section.split('\n')
                header = lines[0]
                content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                
                st.subheader(header)
                if content:
                    st.write(content)
            
            # Check if it's a markdown header
            elif section.startswith('**') and section.endswith('**'):
                st.subheader(section.strip('*'))
            
            else:
                st.write(section)
    
    def extract_key_points(self, rca_content: str):
        """Extract key points from RCA content"""
        # Simple key point extraction (in production, could use NLP)
        lines = rca_content.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            # Look for lines that might be key points
            if (line.startswith('-') or 
                line.startswith('*') or 
                'root cause' in line.lower() or
                'recommendation' in line.lower() or
                'action' in line.lower()):
                key_points.append(line)
        
        if key_points:
            st.subheader("Extracted Key Points")
            for point in key_points[:10]:  # Limit to 10 points
                st.write(f"• {point.lstrip('- *')}")
        else:
            st.info("No clear key points found")
    
    def generate_word_frequency(self, rca_content: str):
        """Generate word frequency analysis"""
        # Simple word frequency (in production, could use proper NLP)
        import re
        from collections import Counter
        
        # Clean and split text
        words = re.findall(r'\b[a-zA-Z]{3,}\b', rca_content.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 
            'did', 'she', 'use', 'her', 'way', 'many', 'with', 'that', 'this', 
            'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 
            'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 
            'over', 'such', 'take', 'than', 'them', 'well', 'were', 'will', 'what',
            'system', 'alert', 'group'
        }
        
        filtered_words = [word for word in words if word not in stop_words]
        word_freq = Counter(filtered_words)
        
        # Get top 20 words
        top_words = word_freq.most_common(20)
        
        if top_words:
            st.subheader("Most Frequent Words")
            
            # Create bar chart
            df_words = pd.DataFrame(top_words, columns=["Word", "Frequency"])
            
            fig_words = px.bar(
                df_words,
                x="Frequency",
                y="Word",
                orientation="h",
                title="Word Frequency in RCA"
            )
            
            fig_words.update_layout(
                height=500,
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig_words, use_container_width=True)
        else:
            st.info("No significant word patterns found")
    
    def export_rca(self, group_id: str):
        """Export RCA report"""
        try:
            response = self.api_client.get_rca(group_id)
            
            if response.get("success"):
                rca_data = response.get("data", {})
                rca_content = rca_data.get("rca_content", "")
                
                if rca_content:
                    # Create downloadable text file
                    st.download_button(
                        label="Download RCA as Text",
                        data=rca_content,
                        file_name=f"rca_group_{group_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        key=f"download_rca_{group_id}"
                    )
                else:
                    st.warning("No RCA content to export")
            else:
                st.error("Failed to load RCA for export")
                
        except Exception as e:
            st.error(f"Failed to export RCA: {e}")
    
    def regenerate_rca(self, group_id: str):
        """Regenerate RCA for a group"""
        try:
            with st.spinner("Regenerating RCA... This may take a few moments."):
                response = self.api_client.generate_rca(group_id, force_regenerate=True)
                
                if response.get("success"):
                    st.success("RCA regeneration started. Please check back shortly.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to regenerate RCA")
                    
        except Exception as e:
            st.error(f"Failed to regenerate RCA: {e}")
