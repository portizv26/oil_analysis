"""
Analytics Page - Evaluation analytics and insights

This page provides analytics and insights about the AI comment evaluations:
1. Grade distribution by CommentType (boxplots)
2. Notes analysis table
3. Summary statistics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add utils to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.db import (
    ensure_database, get_all_evaluations_with_comment_types,
    get_database_stats
)
from utils.io import load_ai_comments


def main():
    """Main analytics page function"""
    
    st.set_page_config(
        page_title="Analytics - AI Comments Evaluator",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize database
    ensure_database()
    
    st.title("📊 Evaluation Analytics")
    st.markdown("*Insights and analytics from AI comment evaluations*")
    
    # Get evaluation data
    evaluations_data = get_all_evaluations_with_comment_types()
    
    if not evaluations_data:
        st.warning("No evaluation data available yet. Complete some evaluations in the Review page first.")
        
        # Show database stats even if no evaluations
        display_database_summary()
        return
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(evaluations_data)
    
    # Display summary metrics
    display_summary_metrics(df)
    
    # Create two-column layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Grade distribution by CommentType (boxplot)
        display_grade_boxplot(df)
        
    with col2:
        # Grade statistics table
        display_grade_statistics(df)
    
    # Notes analysis (full width)
    st.header("📝 Notes Analysis")
    display_notes_analysis(df)
    
    # Detailed evaluations table (full width)
    st.header("📋 Detailed Evaluations")
    display_detailed_evaluations(df)


def display_summary_metrics(df: pd.DataFrame):
    """Display summary metrics at the top of the page"""
    
    st.header("📈 Summary Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Evaluations", len(df))
    
    with col2:
        unique_comments = df['AICommentId'].nunique()
        st.metric("Unique Comments", unique_comments)
    
    with col3:
        unique_alerts = df['AlertId'].nunique()
        st.metric("Unique Alerts", unique_alerts)
    
    with col4:
        avg_grade = df['Grade'].mean()
        st.metric("Average Grade", f"{avg_grade:.2f}")


def display_grade_boxplot(df: pd.DataFrame):
    """Display boxplot of grades by CommentType"""
    
    st.subheader("🎯 Grade Distribution by Comment Type")
    
    # Check if we have enough data for meaningful analysis
    if len(df) < 3:
        st.info("Need at least 3 evaluations for meaningful boxplot visualization.")
        return
    
    # Create boxplot using Plotly
    fig = px.box(
        df, 
        x='CommentType', 
        y='Grade',
        title="Grade Distribution by Comment Type",
        labels={'CommentType': 'Comment Type', 'Grade': 'Grade (1-7)'},
        color='CommentType'
    )
    
    # Customize the plot
    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_tickangle=-45
    )
    
    # Set y-axis range to show full grade scale
    fig.update_layout(yaxis=dict(range=[0.5, 7.5]))
    
    st.plotly_chart(fig)
    
    # Show count per comment type
    comment_counts = df['CommentType'].value_counts()
    st.markdown("**Evaluation counts by Comment Type:**")
    for comment_type, count in comment_counts.items():
        st.markdown(f"- **{comment_type}**: {count} evaluations")


def display_grade_statistics(df: pd.DataFrame):
    """Display detailed statistics table by CommentType"""
    
    st.subheader("📊 Grade Statistics by Comment Type")
    
    # Calculate statistics by CommentType
    stats = df.groupby('CommentType')['Grade'].agg([
        'count',
        'mean', 
        'median',
        'std',
        'min',
        'max'
    ]).round(2)
    
    # Rename columns for clarity
    stats.columns = ['Count', 'Mean', 'Median', 'Std Dev', 'Min', 'Max']
    
    # Reset index to make CommentType a column
    stats = stats.reset_index()
    
    # Display as a styled table
    st.dataframe(
        stats,
        hide_index=True
    )


def display_notes_analysis(df: pd.DataFrame):
    """Display analysis of notes by CommentType"""
    
    # Filter to only evaluations with notes
    notes_df = df[df['Notes'].notna() & (df['Notes'] != '')]
    
    if notes_df.empty:
        st.info("No evaluations with notes available yet.")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Notes Summary")
        
        # Notes statistics
        total_notes = len(notes_df)
        notes_by_type = notes_df.groupby('CommentType')['Notes'].count()
        
        st.metric("Total Evaluations with Notes", total_notes)
        
        st.markdown("**Notes by Comment Type:**")
        for comment_type, count in notes_by_type.items():
            percentage = (count / total_notes) * 100
            st.markdown(f"- **{comment_type}**: {count} ({percentage:.1f}%)")
    
    with col2:
        st.subheader("📈 Notes vs Grades")
        
        # Average grade for evaluations with vs without notes
        avg_grade_with_notes = notes_df['Grade'].mean()
        avg_grade_without_notes = df[df['Notes'].isna() | (df['Notes'] == '')]['Grade'].mean()
        
        st.metric("Avg Grade (with notes)", f"{avg_grade_with_notes:.2f}")
        st.metric("Avg Grade (without notes)", f"{avg_grade_without_notes:.2f}")
    
    # Detailed notes table
    st.subheader("📋 Notes by Comment Type")
    
    # Create a table with CommentType, Grade, and Notes
    notes_table = notes_df[['CommentType', 'Grade', 'Notes', 'CreatedAt']].copy()
    notes_table['CreatedAt'] = pd.to_datetime(notes_table['CreatedAt']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Sort by CommentType then by Grade
    notes_table = notes_table.sort_values(['CommentType', 'Grade'])
    
    st.dataframe(
        notes_table,
        hide_index=True,
        column_config={
            'CommentType': 'Comment Type',
            'Grade': st.column_config.NumberColumn('Grade', min_value=1, max_value=7),
            'Notes': st.column_config.TextColumn('Notes', width='large'),
            'CreatedAt': 'Created'
        }
    )


def display_detailed_evaluations(df: pd.DataFrame):
    """Display detailed evaluations table with filters"""
    
    # Filters
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # CommentType filter
        comment_types = ['All'] + sorted(df['CommentType'].unique().tolist())
        selected_type = st.selectbox("Filter by Comment Type:", comment_types)
    
    with col2:
        # Grade filter
        grades = ['All'] + sorted(df['Grade'].unique().tolist())
        selected_grade = st.selectbox("Filter by Grade:", grades)
    
    with col3:
        # Notes filter
        notes_filter = st.selectbox("Filter by Notes:", ['All', 'With Notes', 'Without Notes'])
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['CommentType'] == selected_type]
    
    if selected_grade != 'All':
        filtered_df = filtered_df[filtered_df['Grade'] == selected_grade]
    
    if notes_filter == 'With Notes':
        filtered_df = filtered_df[filtered_df['Notes'].notna() & (filtered_df['Notes'] != '')]
    elif notes_filter == 'Without Notes':
        filtered_df = filtered_df[filtered_df['Notes'].isna() | (filtered_df['Notes'] == '')]
    
    # Display filtered results
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} evaluations**")
    
    if not filtered_df.empty:
        # Prepare display dataframe
        display_df = filtered_df[['CommentType', 'Grade', 'Notes', 'AICommentId', 'AlertId', 'CreatedAt']].copy()
        display_df['CreatedAt'] = pd.to_datetime(display_df['CreatedAt']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            display_df,
            hide_index=True,
            column_config={
                'CommentType': 'Comment Type',
                'Grade': st.column_config.NumberColumn('Grade', min_value=1, max_value=7),
                'Notes': st.column_config.TextColumn('Notes', width='medium'),
                'AICommentId': 'Comment ID',
                'AlertId': 'Alert ID', 
                'CreatedAt': 'Created'
            }
        )
    else:
        st.info("No evaluations match the selected filters.")


def display_database_summary():
    """Display database summary stats"""
    
    st.header("🗃️ Database Summary")
    
    stats = get_database_stats()
    
    if 'error' in stats:
        st.error(f"Database error: {stats['error']}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Evaluations", stats.get('total_evaluations', 0))
        st.metric("Unique Alerts Evaluated", stats.get('unique_alerts_evaluated', 0))
    
    with col2:
        st.metric("Unique Comments Evaluated", stats.get('unique_comments_evaluated', 0))
        st.metric("Unique Evaluators", stats.get('unique_evaluators', 0))
    
    # Database info
    with st.expander("Database Information"):
        st.code(f"Database Path: {stats.get('database_path', 'Unknown')}")
        st.code(f"Database Exists: {stats.get('database_exists', False)}")


if __name__ == "__main__":
    main()