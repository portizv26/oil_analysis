"""
Chart generation utilities using Plotly for oil analysis evaluator.
Creates telemetry trend charts and other visualizations.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Optional


def create_telemetry_trend_chart(
    telemetry_df: pd.DataFrame,
    variable_name: str,
    title: Optional[str] = None
) -> go.Figure:
    """
    Create a telemetry trend chart for a specific variable with limit bands.
    
    Args:
        telemetry_df: DataFrame with telemetry data
        variable_name: The variable to plot
        title: Optional chart title
        
    Returns:
        Plotly figure object
    """
    if telemetry_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No telemetry data available", 
                          x=0.5, y=0.5, xref="paper", yref="paper",
                          showarrow=False, font_size=16)
        return fig
    
    # Filter data for specific variable
    var_data = telemetry_df[telemetry_df['VariableName'] == variable_name].copy()
    
    if var_data.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"No data for variable: {variable_name}", 
                          x=0.5, y=0.5, xref="paper", yref="paper",
                          showarrow=False, font_size=16)
        return fig
    
    # Sort by timestamp
    var_data = var_data.sort_values('Timestamp')
    
    fig = go.Figure()
    
    # Add upper limit band if available
    if 'UpperLimitValue' in var_data.columns and var_data['UpperLimitValue'].notna().any():
        upper_limit = var_data['UpperLimitValue'].iloc[0]  # Assuming constant limit
        fig.add_hline(y=upper_limit, line_dash="dash", line_color="red", 
                     annotation_text="Upper Limit", annotation_position="top right")
    
    # Add lower limit band if available
    if 'LowerLimitValue' in var_data.columns and var_data['LowerLimitValue'].notna().any():
        lower_limit = var_data['LowerLimitValue'].iloc[0]  # Assuming constant limit
        fig.add_hline(y=lower_limit, line_dash="dash", line_color="red",
                     annotation_text="Lower Limit", annotation_position="bottom right")
    
    # Add main trend line
    fig.add_trace(go.Scatter(
        x=var_data['Timestamp'],
        y=var_data['Value'],
        mode='lines+markers',
        name=variable_name,
        line=dict(color='blue', width=2),
        marker=dict(size=4)
    ))
    
    # Color points that breach limits
    if 'IsLimitReached' in var_data.columns:
        breach_data = var_data[var_data['IsLimitReached'] == True]
        if not breach_data.empty:
            fig.add_trace(go.Scatter(
                x=breach_data['Timestamp'],
                y=breach_data['Value'],
                mode='markers',
                name='Limit Breaches',
                marker=dict(color='red', size=8, symbol='x')
            ))
    
    # Add rolling mean if enough data points
    if len(var_data) > 10:
        var_data['RollingMean'] = var_data['Value'].rolling(window=min(10, len(var_data)//3), center=True).mean()
        fig.add_trace(go.Scatter(
            x=var_data['Timestamp'],
            y=var_data['RollingMean'],
            mode='lines',
            name='Rolling Mean',
            line=dict(color='orange', width=1, dash='dot'),
            opacity=0.7
        ))
    
    # Update layout
    chart_title = title or f"Telemetry Trend: {variable_name}"
    fig.update_layout(
        title=chart_title,
        xaxis_title="Timestamp",
        yaxis_title="Value",
        hovermode='x unified',
        showlegend=True,
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_oil_breach_chart(oil_df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing oil elements by breach level.
    
    Args:
        oil_df: DataFrame with oil measurement data
        
    Returns:
        Plotly figure object
    """
    if oil_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No oil data available", 
                          x=0.5, y=0.5, xref="paper", yref="paper",
                          showarrow=False, font_size=16)
        return fig
    
    # Get latest measurement per element
    latest_oil = oil_df.sort_values('SampleDate').groupby('ElementName').last().reset_index()
    
    # Filter only breached elements
    if 'IsLimitReached' in latest_oil.columns:
        breached = latest_oil[latest_oil['IsLimitReached'] == True]
    else:
        breached = latest_oil
    
    if breached.empty:
        fig = go.Figure()
        fig.add_annotation(text="No breached elements found", 
                          x=0.5, y=0.5, xref="paper", yref="paper",
                          showarrow=False, font_size=16)
        return fig
    
    # Create color mapping for breach levels
    color_map = {
        'urgent': 'red',
        'critical': 'orange', 
        'alert': 'yellow',
        'none': 'green'
    }
    
    # Default color if BreachLevel not available
    if 'BreachLevel' not in breached.columns:
        breached['BreachLevel'] = 'alert'
    
    colors = [color_map.get(level, 'gray') for level in breached['BreachLevel']]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=breached['ElementName'],
        y=breached['Value'],
        marker=dict(color=colors),
        text=breached['BreachLevel'],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Oil Elements - Breach Status",
        xaxis_title="Element Name",
        yaxis_title="Value",
        showlegend=False,
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_evaluation_distribution_chart(evaluations_df: pd.DataFrame) -> go.Figure:
    """
    Create a distribution chart of evaluation grades.
    
    Args:
        evaluations_df: DataFrame with evaluation data
        
    Returns:
        Plotly figure object
    """
    if evaluations_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No evaluations data available", 
                          x=0.5, y=0.5, xref="paper", yref="paper",
                          showarrow=False, font_size=16)
        return fig
    
    # Count grades
    grade_counts = evaluations_df['Grade'].value_counts().sort_index()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=grade_counts.index,
        y=grade_counts.values,
        marker=dict(color='lightblue'),
        text=grade_counts.values,
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Distribution of Evaluation Grades",
        xaxis_title="Grade (1-7)",
        yaxis_title="Count",
        xaxis=dict(tickmode='linear', tick0=1, dtick=1),
        showlegend=False,
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig
