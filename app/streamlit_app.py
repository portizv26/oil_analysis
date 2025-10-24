"""
AI Comments Evaluator - Main Streamlit Application

A lightweight web app to evaluate AI-generated comments about mining equipment conditions.
Reads static oil & telemetry data from Parquet; stores evaluator feedback in SQLite.
"""
import streamlit as st
import pandas as pd
from pathlib import Path

# Add utils to path for imports
import sys
sys.path.append(str(Path(__file__).parent))

from utils.db import ensure_database, get_database_stats
from utils.io import validate_data_files, get_data_stats, get_available_alerts, get_alerts_summary
from utils.schemas import EvaluationCreate
from utils.s3_sync import download_data_files, test_s3_connection, upload_evaluations_parquet


# @st.cache_data(ttl=3600)  # Cache for 1 hour
def download_s3_data():
    """Download data files from S3 if needed (cached for performance)"""
    return download_data_files()


def main():
    """Main application entry point"""
        
    # Page configuration
    st.set_page_config(
        page_title="AI Comments Evaluator",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database
    ensure_database()
    
    # Download data files from S3 on startup
    with st.spinner("📥 Checking for data updates from S3..."):
        try:
            download_success = download_s3_data()
            if download_success:
                st.success("✅ Data files synchronized from S3", icon="📥")
            else:
                # Check if we have local files as fallback
                file_status = validate_data_files()
                if not all(file_status.values()):
                    st.error("❌ Failed to download data from S3 and no local files found")
                    st.info("Please check your S3 configuration or place data files manually in the `data/` folder")
                else:
                    st.warning("⚠️ Using local data files (S3 download failed)")
        except Exception as e:
            st.warning(f"⚠️ S3 download error: {e}. Using local files if available.")
    
    # Main header
    st.title("🔧 AI Comments Evaluator")
    st.markdown("*Evaluate AI-generated comments about mining equipment conditions*")
    
    # Sidebar with navigation and stats
    with st.sidebar:
        st.header("📊 System Status")
        
        # Data validation
        file_status = validate_data_files()
        st.subheader("Data Files")
        
        for filename, exists in file_status.items():
            status_icon = "✅" if exists else "❌"
            st.write(f"{status_icon} {filename}")
        
        # Check if all files exist
        all_files_exist = all(file_status.values())
        
        if not all_files_exist:
            st.error("⚠️ Some data files are missing! Please ensure all Parquet files are in the `data/` folder.")
            st.stop()
        
        # Data statistics
        st.subheader("Data Overview")
        try:
            data_stats = get_data_stats()
            alerts_summary = get_alerts_summary()
            
            if "error" not in data_stats:
                # st.metric("Total Alerts", alerts_summary.get("total_alerts", 0))
                st.metric("Alerts with Comments", alerts_summary.get("alerts_with_comments", 0))
                st.metric("AI Comments", data_stats.get("ai_comments_count", 0))
                # st.metric("Unique Units", data_stats.get("unique_units", 0))
                
                # Show alerts without comments if any
                # alerts_without_comments = alerts_summary.get("alerts_without_comments", 0)
                # if alerts_without_comments > 0:
                #     st.caption(f"📝 {alerts_without_comments} alerts have no comments (filtered from evaluation)")
                
                # Comment types
                # comment_types = data_stats.get("comment_types", [])
                # if comment_types:
                #     st.write("**Comment Types:**")
                #     for ct in comment_types:
                #         st.write(f"• {ct}")
            else:
                st.error(f"Error loading data stats: {data_stats['error']}")
        except Exception as e:
            st.error(f"Error getting data stats: {e}")
        
        # Database statistics
        st.subheader("Evaluation Progress")
        try:
            db_stats = get_database_stats()
            if "error" not in db_stats:
                st.metric("Total Evaluations", db_stats.get("total_evaluations", 0))
                # st.metric("Alerts Evaluated", db_stats.get("unique_alerts_evaluated", 0))
                # st.metric("Comments Evaluated", db_stats.get("unique_comments_evaluated", 0))
                # st.metric("Active Evaluators", db_stats.get("unique_evaluators", 0))
            else:
                st.error(f"Database error: {db_stats['error']}")
        except Exception as e:
            st.error(f"Error getting database stats: {e}")
        
        # S3 Management Section
        st.subheader("☁️ S3 Management")
        
        # Test S3 connection
        # if st.button("🔗 Test S3 Connection"):
        #     with st.spinner("Testing S3 connection..."):
        #         if test_s3_connection():
        #             st.success("✅ S3 connection successful")
        #         else:
        #             st.error("❌ S3 connection failed")
        
        # Manual data refresh
        if st.button("🔄 Refresh Data from S3"):
            with st.spinner("Downloading latest data..."):
                # Clear cache and download fresh data
                # download_s3_data.clear()
                if download_data_files():
                    st.success("✅ Data refreshed successfully")
                    st.rerun()
                else:
                    st.error("❌ Failed to refresh data")
        
        # Upload evaluations as parquet
        if st.button("📤 Export & Upload Evaluations"):
            with st.spinner("Exporting evaluations to parquet..."):
                if upload_evaluations_parquet():
                    st.success("✅ Evaluations exported to S3")
                else:
                    st.error("❌ Failed to export evaluations")
    
    # Main content area
    if all_files_exist:
        st.header("🎯 Quick Start")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("How to Use")
            st.markdown("""
            1. **Navigate to Review Page** - Use the sidebar or click the button below
            2. **Select an Alert** - Choose from available alerts to evaluate
            3. **Review Context** - Examine oil and telemetry data for the alert
            4. **Evaluate Comments** - Grade each AI comment on a scale of 1-7
            5. **Submit Evaluation** - Save your assessment to the database
            6. **Continue** - Move to the next alert for evaluation
            """)
            
            # Quick navigation to review page
            if st.button("🚀 Start Evaluating", type="primary", width='stretch'):
                st.switch_page("pages/1_Review.py")
        
        with col2:
            st.subheader("Grading Scale (1-7)")
            st.markdown("""
            **7 - Excellent:** Concise, accurate, directly actionable; cites evidence
            
            **5-6 - Good/Very Good:** Accurate and actionable recommendations
            
            **3-4 - Partial:** Mixed accuracy, vague actions, partial understanding
            
            **1-2 - Poor:** Very poor, irrelevant, or potentially unsafe advice
            """)
        
        # # Show available alerts for quick reference
        # try:
        #     available_alerts = get_available_alerts()
        #     if available_alerts:
        #         st.header("📋 Available Alerts (with Comments)")
                
        #         # Create a summary table
        #         alerts_summary = []
        #         for alert_id in available_alerts[:10]:  # Show first 10
        #             alerts_summary.append({"AlertId": alert_id})
                
        #         summary_df = pd.DataFrame(alerts_summary)
        #         st.dataframe(summary_df, width='stretch')
                
        #         if len(available_alerts) > 10:
        #             st.info(f"Showing first 10 of {len(available_alerts)} total alerts with comments. Use the Review page to access all alerts.")
        #     else:
        #         st.warning("No alerts with AI comments found in the data.")
                
        # except Exception as e:
        #     st.error(f"Error loading alerts: {e}")
        
        # # Additional information
        # st.header("ℹ️ About This Application")
        
        # with st.expander("System Architecture"):
        #     st.markdown("""
        #     **Data Sources (Read-Only):**
        #     - `alerts.parquet` - Alert information with oil/telemetry links
        #     - `oil_measurements.parquet` - Oil analysis results
        #     - `telemetry_measurements.parquet` - Equipment sensor data  
        #     - `ai_comments.parquet` - AI-generated maintenance comments
            
        #     **Evaluation Storage:**
        #     - `state/eval.db` - SQLite database for evaluator feedback
        #     - Automatic daily sync to S3 (if configured)
            
        #     **Key Features:**
        #     - Cached data loading for fast navigation
        #     - Context-aware evaluation (same data for all comments per alert)
        #     - Grade tracking with optional notes
        #     - Multi-evaluator support
        #     """)
        
        # with st.expander("Performance Tips"):
        #     st.markdown("""
        #     - Data is cached automatically for faster loading
        #     - Use the "Next Alert" button for efficient navigation
        #     - Optional notes help track evaluation reasoning
        #     - Database is optimized with proper indexing
        #     - S3 sync preserves evaluation history
        #     """)


if __name__ == "__main__":
    main()