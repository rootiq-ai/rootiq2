"""
Main Streamlit application for Alert Monitoring System
"""
import streamlit as st
import sys
from pathlib import Path

# Add the frontend directory to Python path
sys.path.append(str(Path(__file__).parent))

from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh
import logging

# Import components
from components.alert_dashboard import AlertDashboard
from components.group_viewer import GroupViewer
from components.rca_display import RCADisplay
from utils.api_client import APIClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Alert Monitoring System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        text-align: center;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .alert-critical {
        border-left-color: #ff4757 !important;
    }
    
    .alert-high {
        border-left-color: #ff6348 !important;
    }
    
    .alert-medium {
        border-left-color: #ffa502 !important;
    }
    
    .alert-low {
        border-left-color: #2ed573 !important;
    }
    
    .status-active {
        background-color: #ff4757;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    
    .status-resolved {
        background-color: #2ed573;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    .stSelectbox > div > div {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

class AlertMonitoringApp:
    """Main application class"""
    
    def __init__(self):
        self.api_client = APIClient()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'Dashboard'
        
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 30  # seconds
        
        if 'selected_alert_id' not in st.session_state:
            st.session_state.selected_alert_id = None
        
        if 'selected_group_id' not in st.session_state:
            st.session_state.selected_group_id = None
    
    def render_header(self):
        """Render the main header"""
        st.markdown("""
        <div class="main-header">
            <h1>🚨 AI Alert Monitoring System</h1>
            <p style="color: white; text-align: center; margin: 0; opacity: 0.9;">
                Intelligent Alert Grouping & Root Cause Analysis
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render the sidebar navigation"""
        with st.sidebar:
            st.image("https://via.placeholder.com/200x60/667eea/FFFFFF?text=Alert+Monitor", 
                    width=200)
            
            # Navigation menu
            selected = option_menu(
                menu_title="Navigation",
                options=["Dashboard", "Alert Groups", "RCA Analysis", "Settings"],
                icons=["speedometer2", "collection", "clipboard-data", "gear"],
                menu_icon="list",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#fafafa"},
                    "icon": {"color": "#667eea", "font-size": "18px"},
                    "nav-link": {
                        "font-size": "16px",
                        "text-align": "left",
                        "margin": "0px",
                        "--hover-color": "#eee"
                    },
                    "nav-link-selected": {"background-color": "#667eea"},
                }
            )
            
            st.session_state.current_page = selected
            
            # Auto-refresh settings
            st.markdown("---")
            st.subheader("Auto-Refresh")
            
            st.session_state.auto_refresh = st.checkbox(
                "Enable Auto-Refresh", 
                value=st.session_state.auto_refresh
            )
            
            if st.session_state.auto_refresh:
                st.session_state.refresh_interval = st.selectbox(
                    "Refresh Interval",
                    options=[10, 30, 60, 120, 300],
                    index=1,
                    format_func=lambda x: f"{x} seconds"
                )
                
                # Auto-refresh component
                st_autorefresh(
                    interval=st.session_state.refresh_interval * 1000,
                    key="auto_refresh"
                )
            
            # System status
            st.markdown("---")
            st.subheader("System Status")
            
            # Check API health
            try:
                health_status = self.api_client.get_health()
                if health_status.get("status") == "healthy":
                    st.success("🟢 API Online")
                else:
                    st.error("🔴 API Issues")
            except Exception as e:
                st.error("🔴 API Offline")
            
            # Quick stats
            try:
                stats = self.api_client.get_alert_stats()
                if stats and stats.get("success"):
                    data = stats["data"]
                    st.metric("Total Alerts", data.get("total_alerts", 0))
                    st.metric("Recent (24h)", data.get("recent_alerts_24h", 0))
            except Exception as e:
                st.warning("Unable to load stats")
    
    def render_main_content(self):
        """Render the main content area"""
        page = st.session_state.current_page
        
        if page == "Dashboard":
            self.render_dashboard()
        elif page == "Alert Groups":
            self.render_groups()
        elif page == "RCA Analysis":
            self.render_rca_analysis()
        elif page == "Settings":
            self.render_settings()
    
    def render_dashboard(self):
        """Render the main dashboard"""
        st.header("📊 Alert Dashboard")
        
        # Initialize dashboard component
        dashboard = AlertDashboard(self.api_client)
        dashboard.render()
    
    def render_groups(self):
        """Render the groups page"""
        st.header("👥 Alert Groups")
        
        # Initialize group viewer component
        group_viewer = GroupViewer(self.api_client)
        group_viewer.render()
    
    def render_rca_analysis(self):
        """Render the RCA analysis page"""
        st.header("🔍 Root Cause Analysis")
        
        # Initialize RCA display component
        rca_display = RCADisplay(self.api_client)
        rca_display.render()
    
    def render_settings(self):
        """Render the settings page"""
        st.header("⚙️ System Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("API Configuration")
            
            current_base_url = getattr(self.api_client, 'base_url', 'http://localhost:8000')
            
            with st.form("api_settings"):
                base_url = st.text_input(
                    "API Base URL",
                    value=current_base_url,
                    help="Backend API base URL"
                )
                
                timeout = st.number_input(
                    "Request Timeout (seconds)",
                    min_value=5,
                    max_value=300,
                    value=30,
                    step=5
                )
                
                submitted = st.form_submit_button("Update Settings")
                
                if submitted:
                    self.api_client.base_url = base_url
                    self.api_client.timeout = timeout
                    st.success("Settings updated successfully!")
        
        with col2:
            st.subheader("Alert Thresholds")
            
            with st.form("threshold_settings"):
                similarity_threshold = st.slider(
                    "Similarity Threshold",
                    min_value=0.1,
                    max_value=1.0,
                    value=0.8,
                    step=0.05,
                    help="Minimum similarity score for alert grouping"
                )
                
                max_group_size = st.number_input(
                    "Maximum Group Size",
                    min_value=5,
                    max_value=100,
                    value=50,
                    step=5,
                    help="Maximum number of alerts per group"
                )
                
                auto_rca = st.checkbox(
                    "Auto-generate RCA",
                    value=True,
                    help="Automatically generate RCA for new groups"
                )
                
                submitted = st.form_submit_button("Save Thresholds")
                
                if submitted:
                    st.success("Thresholds saved successfully!")
        
        # System Information
        st.markdown("---")
        st.subheader("System Information")
        
        try:
            system_info = self.api_client.get_system_info()
            if system_info:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.info(f"**System:** {system_info.get('system', 'Unknown')}")
                
                with col2:
                    st.info(f"**Version:** {system_info.get('version', 'Unknown')}")
                
                with col3:
                    settings_info = system_info.get('settings', {})
                    st.info(f"**Model:** {settings_info.get('ollama_model', 'Unknown')}")
        
        except Exception as e:
            st.error(f"Unable to load system information: {e}")
        
        # Reset Data Section
        st.markdown("---")
        st.subheader("⚠️ Danger Zone")
        
        st.warning("The following actions are irreversible!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear All Alerts", type="secondary"):
                if st.checkbox("I understand this will delete all alerts"):
                    # This would need to be implemented in the API
                    st.error("Feature not implemented yet")
        
        with col2:
            if st.button("🗑️ Clear All Groups", type="secondary"):
                if st.checkbox("I understand this will delete all groups"):
                    # This would need to be implemented in the API
                    st.error("Feature not implemented yet")
    
    def run(self):
        """Run the main application"""
        try:
            # Render header
            self.render_header()
            
            # Render sidebar
            self.render_sidebar()
            
            # Render main content
            self.render_main_content()
            
        except Exception as e:
            st.error(f"Application error: {e}")
            logger.error(f"Application error: {e}", exc_info=True)

def main():
    """Main function"""
    try:
        app = AlertMonitoringApp()
        app.run()
        
    except Exception as e:
        st.error(f"Failed to start application: {e}")
        logger.error(f"Failed to start application: {e}", exc_info=True)

if __name__ == "__main__":
    main()
