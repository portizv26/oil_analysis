"""
Review Page - Main grading flow for AI Comments Evaluator

This page handles the core evaluation workflow:
1. Alert selection
2. Context display (oil and telemetry data)  
3. AI comments evaluation
4. Grade submission
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.db import (
    ensure_database, create_evaluation, check_comment_evaluated,
    get_evaluations_by_alert
)
from utils.io import (
    get_available_alerts, get_alerts_with_filters, get_alert_filter_options,
    get_alert_details, get_oil_data_for_alert,
    get_telemetry_data_for_alert, get_comments_for_alert,
    get_oil_summary_table, get_telemetry_breaches_table
)
from utils.charts import create_telemetry_trend_chart, create_oil_breach_chart
from utils.schemas import EvaluationCreate


def main():
    """Main review page function"""
    
    st.set_page_config(
        page_title="Review - AI Comments Evaluator",
        page_icon="📝",
        layout="wide"
    )
    
    # Initialize database
    ensure_database()
    
    st.title("📝 AI Comments Review")
    st.markdown("*Evaluate AI-generated comments with full context*")
    
    # Get filter options
    filter_options = get_alert_filter_options()
    
    if not filter_options['components']:
        st.error("No alerts available for evaluation. Please check your data files.")
        return
    
    # Alert filters section
    st.subheader("🔍 Alert Filters")
    
    # Create filter columns
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 1])
    
    with filter_col1:
        selected_component = st.selectbox(
            "Component:",
            filter_options['components'],
            help="Filter alerts by component type",
            index=filter_options['components'].index(st.session_state.get('component_filter', 'All')) 
                  if st.session_state.get('component_filter', 'All') in filter_options['components'] else 0
        )
        st.session_state.component_filter = selected_component
    
    with filter_col2:
        selected_unit = st.selectbox(
            "Unit ID:",
            filter_options['units'],
            help="Filter alerts by unit identifier",
            index=filter_options['units'].index(st.session_state.get('unit_filter', 'All'))
                  if st.session_state.get('unit_filter', 'All') in filter_options['units'] else 0
        )
        st.session_state.unit_filter = selected_unit
    
    with filter_col3:
        selected_label = st.selectbox(
            "Data Type:",
            filter_options['labels'],
            help="Filter by data availability (oil, telemetry, both)",
            index=filter_options['labels'].index(st.session_state.get('label_filter', 'All'))
                  if st.session_state.get('label_filter', 'All') in filter_options['labels'] else 0
        )
        st.session_state.label_filter = selected_label
    
    with filter_col4:
        # Reset filters button
        if st.button("🔄 Reset Filters"):
            st.session_state.clear()
            st.rerun()
    
    # Get filtered alerts
    available_alerts = get_alerts_with_filters(
        component_filter=selected_component,
        unit_filter=selected_unit,
        label_filter=selected_label
    )
    
    if not available_alerts:
        st.warning("No alerts match the selected filters. Try adjusting your filter criteria.")
        return
    
    # Display filter results
    st.info(f"Found **{len(available_alerts)}** alerts matching your filters")
    
    # Alert selection
    st.subheader("📋 Alert Selection")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_alert = st.selectbox(
            "Select Alert to Evaluate:",
            available_alerts,
            help="Choose an alert to view its context and evaluate AI comments",
            key="alert_selector"
        )
    
    with col2:
        # Quick navigation buttons
        if st.button("🔄 Next Alert"):
            # Find next alert in filtered list
            try:
                current_idx = available_alerts.index(selected_alert)
                next_idx = (current_idx + 1) % len(available_alerts)
                # Store the next alert and filters in session state
                st.session_state.selected_alert = available_alerts[next_idx]
                st.session_state.component_filter = selected_component
                st.session_state.unit_filter = selected_unit  
                st.session_state.label_filter = selected_label
                st.rerun()
            except ValueError:
                pass
    
    # Use session state for alert selection if available and filters match
    if ('selected_alert' in st.session_state and 
        st.session_state.get('component_filter') == selected_component and
        st.session_state.get('unit_filter') == selected_unit and
        st.session_state.get('label_filter') == selected_label and
        st.session_state.selected_alert in available_alerts):
        selected_alert = st.session_state.selected_alert
    
    if not selected_alert:
        st.info("Please select an alert to begin evaluation.")
        return
    
    # Get alert details
    alert_details = get_alert_details(selected_alert)
    # st.write(alert_details)
    
    if not alert_details:
        st.error(f"Could not load details for alert: {selected_alert}")
        return
    
    # Display alert information
    # st.subheader(f"🚨 Alert: {selected_alert}")
    
    alert_col1, alert_col2, alert_col3 = st.columns(3)
    
    with alert_col1:
        st.metric("Unit ID", alert_details.get('UnitId', 'N/A'))
    
    with alert_col2:
        st.metric("Component", alert_details.get('Component', 'N/A'))
    
    with alert_col3:
        oilMt = alert_details.get('OilMeter', 'N/A')
        st.metric("Oil Meter", oilMt)
    
    # Create two-column layout for main content
    left_col, right_col = st.columns([1, 1])
    
    # Left column: Context data (tables and charts)
    with left_col:
        st.header("📊 Context Data")
        
        # Check what type of data is available
        has_oil = alert_details.get('OilAlertId') is not None
        has_telemetry = alert_details.get('TelAlertId') is not None
        
        if has_oil:
            display_oil_context(selected_alert)
        
        if has_telemetry:
            display_telemetry_context(selected_alert)
        
        if not has_oil and not has_telemetry:
            st.warning("No oil or telemetry data available for this alert.")
    
    # Right column: AI comments and evaluation forms
    with right_col:
        st.header("🤖 AI Comments Evaluation")
        display_comments_evaluation(selected_alert)


def display_oil_context(alert_id: str):
    """Display oil measurement context for an alert"""
    
    st.subheader("🛢️ Oil Analysis")
    
    # Get oil data
    oil_summary = get_oil_summary_table(alert_id)
    
    if oil_summary.empty:
        st.info("No oil data available for this alert.")
        return
    
    # Display oil summary table
    st.markdown("**Latest Oil Measurements (Snapshot per Element)**")
    
    # Create a styled dataframe with breach level indicators
    if 'BreachLevel' in oil_summary.columns:
        def style_breach_level(val):
            color_map = {
                'urgent': 'background-color: #ff4444; color: white;',
                'critical': 'background-color: #ff8800; color: white;',
                'alert': 'background-color: #ffff00; color: black;',
                'none': 'background-color: #44ff44; color: black;'
            }
            return color_map.get(val, '')
        
        styled_df = oil_summary.style.applymap(
            style_breach_level,
            subset=['BreachLevel'] if 'BreachLevel' in oil_summary.columns else []
        )
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.dataframe(oil_summary, use_container_width=True)
    
    # Oil breach chart
    oil_data = get_oil_data_for_alert(alert_id)
    # if not oil_data.empty:
    #     fig = create_oil_breach_chart(oil_data)
    #     st.plotly_chart(fig, use_container_width=True)


def display_telemetry_context(alert_id: str):
    """Display telemetry measurement context for an alert"""
    
    st.subheader("📡 Telemetry Analysis")
    
    # Get telemetry breach summary
    breach_summary = get_telemetry_breaches_table(alert_id)
    
    if breach_summary.empty:
        st.info("No telemetry data available for this alert.")
        return
    
    # Display breach summary table
    st.markdown("**Top Telemetry Breaches**")
    st.dataframe(breach_summary, use_container_width=True)
    
    # Telemetry trend charts
    telemetry_data = get_telemetry_data_for_alert(alert_id)
    
    if not telemetry_data.empty:
        # Get unique variables for trend charts
        variables = telemetry_data['VariableName'].unique()
        
        # Show trends for top breached variables (max 3 charts)
        top_variables = breach_summary.head(3)['VariableName'].tolist()
        
        st.markdown("**Variable Trend Charts (Recent Window ±48h)**")
        
        for var_name in top_variables:
            fig = create_telemetry_trend_chart(telemetry_data, var_name)
            st.plotly_chart(fig, use_container_width=True)


def display_comments_evaluation(alert_id: str):
    """Display AI comments and evaluation forms"""
    
    # Get comments for this alert
    comments_df = get_comments_for_alert(alert_id)
    
    if comments_df.empty:
        st.warning("No AI comments available for this alert.")
        return
    
    # Group comments by type
    comment_types = comments_df['CommentType'].unique()
    
    # Check existing evaluations
    existing_evaluations = get_evaluations_by_alert(alert_id)
    evaluated_comments = {eval.AICommentId for eval in existing_evaluations}
    
    st.markdown(f"**{len(comments_df)} AI Comments found** | **{len(evaluated_comments)} already evaluated**")
    
    # Initialize session state for evaluations if not exists
    if 'pending_evaluations' not in st.session_state:
        st.session_state.pending_evaluations = {}
    
    # Display comments grouped by type
    for comment_type in comment_types:
        type_comments = comments_df[comments_df['CommentType'] == comment_type]
        
        with st.expander(f"📋 {comment_type.title()} Comments ({len(type_comments)})", expanded=True):
            
            for _, comment_row in type_comments.iterrows():
                comment_id = comment_row['AICommentId']
                comment_text = comment_row['CommentText']
                
                # Check if already evaluated
                already_evaluated = comment_id in evaluated_comments
                
                # Display comment
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Comment:**")
                    st.write(comment_text)
                
                with col2:
                    if already_evaluated:
                        st.success("✅ Evaluated")
                        # Show existing evaluation details
                        existing_eval = next((e for e in existing_evaluations if e.AICommentId == comment_id), None)
                        if existing_eval:
                            st.write(f"**Grade:** {existing_eval.Grade}/7")
                            if existing_eval.Notes:
                                st.write(f"**Notes:** {existing_eval.Notes}")
                    else:
                        # Evaluation form
                        with st.form(f"eval_form_{comment_id}"):
                            st.markdown("**Evaluate this comment:**")
                            
                            grade = st.slider(
                                "Grade (1-7)",
                                min_value=1,
                                max_value=7,
                                value=4,
                                key=f"grade_{comment_id}",
                                help="1-2: Poor/Unsafe | 3-4: Partial | 5-6: Good | 7: Excellent"
                            )
                            
                            notes = st.text_area(
                                "Notes (optional)",
                                key=f"notes_{comment_id}",
                                help="Brief rationale or issues spotted",
                                height=80
                            )
                            
                            user_id = st.text_input(
                                "Evaluator ID (optional)",
                                key=f"user_{comment_id}",
                                help="Your identifier for tracking"
                            )
                            
                            submitted = st.form_submit_button("Submit Evaluation", type="primary")
                            
                            if submitted:
                                try:
                                    # Create evaluation
                                    evaluation_data = EvaluationCreate(
                                        AICommentId=comment_id,
                                        AlertId=alert_id,
                                        Grade=grade,
                                        Notes=notes if notes.strip() else None,
                                        UserId=user_id if user_id.strip() else None
                                    )
                                    
                                    created_eval = create_evaluation(evaluation_data)
                                    
                                    st.success(f"✅ Evaluation submitted! ID: {created_eval.EvaluationId}")
                                    
                                    # Refresh the page to update the UI
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Error submitting evaluation: {e}")
                
                st.divider()
    
    # Show evaluation progress
    total_comments = len(comments_df)
    evaluated_count = len(evaluated_comments)
    
    if evaluated_count > 0:
        progress = evaluated_count / total_comments
        st.progress(progress)
        st.caption(f"Progress: {evaluated_count}/{total_comments} comments evaluated ({progress:.1%})")
        
        if evaluated_count == total_comments:
            st.success("🎉 All comments for this alert have been evaluated!")
            
            if st.button("➡️ Next Alert", type="primary"):
                # Move to next alert in filtered list
                # Get current filter values from session state or use defaults
                current_component = st.session_state.get('component_filter', 'All')
                current_unit = st.session_state.get('unit_filter', 'All')
                current_label = st.session_state.get('label_filter', 'All')
                
                current_filtered_alerts = get_alerts_with_filters(
                    component_filter=current_component,
                    unit_filter=current_unit,
                    label_filter=current_label
                )
                try:
                    current_idx = current_filtered_alerts.index(alert_id)
                    next_idx = (current_idx + 1) % len(current_filtered_alerts)
                    st.session_state.selected_alert = current_filtered_alerts[next_idx]
                    st.rerun()
                except (ValueError, IndexError):
                    pass


if __name__ == "__main__":
    main()