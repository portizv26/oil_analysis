"""
Data I/O utilities for reading Parquet files in oil analysis evaluator.
Handles loading and caching of oil, telemetry, alerts, and AI comments data.
"""
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# Data file paths
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ALERTS_FILE = DATA_DIR / "alerts.parquet"
OIL_FILE = DATA_DIR / "oil_measurements.parquet"
TELEMETRY_FILE = DATA_DIR / "telemetry_measurements.parquet"
COMMENTS_FILE = DATA_DIR / "ai_comments.parquet"


# @st.cache_data
def load_alerts() -> pd.DataFrame:
    """
    Load alerts data from Parquet file.
    
    Returns:
        DataFrame with columns: AlertId, OilAlertId, TelAlertId, TimeStart, UnitId, Component, Label
    """
    try:
        df = pd.read_parquet(ALERTS_FILE)
    
        oil_df = load_oil_measurements()
        oil_df = oil_df[['OilAlertId', 'OilMeter']].drop_duplicates()
        df = df.merge(oil_df, on='OilAlertId', how='left')
        
        # Ensure TimeStart is datetime
        if 'TimeStart' in df.columns:
            df['TimeStart'] = pd.to_datetime(df['TimeStart'])
            
        return df
    except Exception as e:
        st.error(f"Error loading alerts data: {e}")
        return pd.DataFrame()


# @st.cache_data
def load_oil_measurements() -> pd.DataFrame:
    """
    Load oil measurements data from Parquet file.
    
    Returns:
        DataFrame with oil measurement data
    """
    try:
        df = pd.read_parquet(OIL_FILE)
        
        # Ensure SampleDate is datetime
        if 'SampleDate' in df.columns:
            df['SampleDate'] = pd.to_datetime(df['SampleDate'])
            
        return df
    except Exception as e:
        st.error(f"Error loading oil measurements: {e}")
        return pd.DataFrame()


# @st.cache_data
def load_telemetry_measurements() -> pd.DataFrame:
    """
    Load telemetry measurements data from Parquet file.
    
    Returns:
        DataFrame with telemetry measurement data
    """
    try:
        df = pd.read_parquet(TELEMETRY_FILE)
        
        # Ensure Timestamp is datetime
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            
        return df
    except Exception as e:
        st.error(f"Error loading telemetry measurements: {e}")
        return pd.DataFrame()


# @st.cache_data
def load_ai_comments() -> pd.DataFrame:
    """
    Load AI comments data from Parquet file.
    
    Returns:
        DataFrame with AI comments data
    """
    try:
        df = pd.read_parquet(COMMENTS_FILE)
        return df
    except Exception as e:
        st.error(f"Error loading AI comments: {e}")
        return pd.DataFrame()


# @st.cache_data
def get_alert_details(alert_id: str) -> Optional[Dict]:
    """
    Get detailed information for a specific alert.
    
    Args:
        alert_id: The AlertId to look up
        
    Returns:
        Dictionary with alert details or None if not found
    """
    alerts_df = load_alerts()
    
    if alerts_df.empty:
        return None
        
    alert_row = alerts_df[alerts_df['AlertId'] == alert_id]
    # st.write(alert_row)
    
    if alert_row.empty:
        return None
        
    return alert_row.iloc[0].to_dict()


# @st.cache_data
def get_oil_data_for_alert(alert_id: str) -> pd.DataFrame:
    """
    Get oil measurement data for a specific alert.
    
    Args:
        alert_id: The AlertId to filter by
        
    Returns:
        DataFrame with oil measurements for the alert
    """
    # First get the alert details to find OilAlertId
    alert_details = get_alert_details(alert_id)
    
    if not alert_details or not alert_details.get('OilAlertId'):
        return pd.DataFrame()
    
    oil_alert_id = alert_details['OilAlertId']
    oil_df = load_oil_measurements()
    
    if oil_df.empty:
        return pd.DataFrame()
    
    # Filter by OilAlertId
    return oil_df[oil_df['OilAlertId'] == oil_alert_id].copy()


# @st.cache_data
def get_telemetry_data_for_alert(alert_id: str) -> pd.DataFrame:
    """
    Get telemetry measurement data for a specific alert with time window.
    
    Args:
        alert_id: The AlertId to filter by
        
    Returns:
        DataFrame with telemetry measurements for the alert
    """
    # First get the alert details to find TelAlertId and TimeStart
    alert_details = get_alert_details(alert_id)
    
    if not alert_details or not alert_details.get('TelAlertId'):
        return pd.DataFrame()
    
    tel_alert_id = alert_details['TelAlertId']
    time_start = alert_details.get('TimeStart')
    
    telemetry_df = load_telemetry_measurements()
    
    if telemetry_df.empty:
        return pd.DataFrame()
    
    # Filter by TelAlertId
    filtered_df = telemetry_df[telemetry_df['TelAlertId'] == tel_alert_id].copy()
    
    # Apply time window filter (±48h around TimeStart if available)
    if time_start and not filtered_df.empty:
        time_start = pd.to_datetime(time_start)
        start_window = time_start - timedelta(hours=48)
        end_window = time_start + timedelta(hours=48)
        
        filtered_df = filtered_df[
            (filtered_df['Timestamp'] >= start_window) & 
            (filtered_df['Timestamp'] <= end_window)
        ]
    
    return filtered_df


# @st.cache_data
def get_comments_for_alert(alert_id: str) -> pd.DataFrame:
    """
    Get all AI comments for a specific alert.
    
    Args:
        alert_id: The AlertId to filter by
        
    Returns:
        DataFrame with AI comments for the alert
    """
    comments_df = load_ai_comments()
    
    if comments_df.empty:
        return pd.DataFrame()
    
    return comments_df[comments_df['AlertId'] == alert_id].copy()


# @st.cache_data 
def get_oil_summary_table(alert_id: str) -> pd.DataFrame:
    """
    Create oil snapshot table (latest per element) for display.
    Sorted with breached elements on top.
    
    Args:
        alert_id: The AlertId to create summary for
        
    Returns:
        DataFrame with columns: ElementName, Value, LimitValue, BreachLevel, SampleDate
    """
    oil_df = get_oil_data_for_alert(alert_id)
    # st.write(oil_df)
    
    if oil_df.empty:
        return pd.DataFrame()
    
    # Get latest measurement per element
    latest_df = oil_df.sort_values('SampleDate').groupby('ElementName').last().reset_index()
    
    # Select relevant columns
    summary_columns = ['ElementName', 'Value', 'LimitValue', 'BreachLevel']
    available_columns = [col for col in summary_columns if col in latest_df.columns]
    summary_df = latest_df[available_columns].copy()
    
    # Sort with breached elements on top
    if 'IsLimitReached' in latest_df.columns:
        summary_df['IsLimitReached'] = latest_df['IsLimitReached']
        summary_df = summary_df.sort_values(['IsLimitReached', 'ElementName'], ascending=[False, True])
        summary_df = summary_df.drop('IsLimitReached', axis=1)
    else:
        summary_df = summary_df.sort_values('ElementName')
    
    return summary_df.reset_index(drop=True)


# @st.cache_data
def get_telemetry_breaches_table(alert_id: str) -> pd.DataFrame:
    # THIS UNCTION REQUIRES MAJOR CHANGES TO CAPTURE SIGNIFFICCANT DATA TO THE ANALYSIS
    """
    Create telemetry top breaches table for display.
    
    Args:
        alert_id: The AlertId to create breaches table for
        
    Returns:
        DataFrame with columns: VariableName, MaxExcess, AnyLimitReached, LastTimestamp
    """
    tel_df = get_telemetry_data_for_alert(alert_id)
    
    if tel_df.empty:
        return pd.DataFrame()
    
    # Calculate breaches per variable
    breach_stats = []
    
    for var_name in tel_df['VariableName'].unique():
        var_data = tel_df[tel_df['VariableName'] == var_name].copy()
        
        # Calculate max excess (assuming upper limit breach is primary concern)
        max_excess = 0
        if 'UpperLimitValue' in var_data.columns and var_data['UpperLimitValue'].notna().any():
            upper_breaches = var_data[var_data['UpperLimitValue'].notna()]
            if not upper_breaches.empty:
                excess_values = upper_breaches['Value'] - upper_breaches['UpperLimitValue']
                max_excess = excess_values.max() if excess_values.max() > 0 else 0
        
        any_limit_reached = var_data['IsLimitReached'].any() if 'IsLimitReached' in var_data.columns else False
        last_timestamp = var_data['Timestamp'].max()
        
        breach_stats.append({
            'VariableName': var_name,
            'MaxExcess': max_excess,
            'AnyLimitReached': any_limit_reached,
            # 'LastTimestamp': last_timestamp
        })
    
    breach_df = pd.DataFrame(breach_stats)
    # Sort by breach severity
    if not breach_df.empty:
        breach_df = breach_df.sort_values(['AnyLimitReached', 'MaxExcess'], ascending=[False, False])

    return breach_df[breach_df['AnyLimitReached']]


def get_available_alerts() -> List[str]:
    """
    Get list of all available AlertIds that have AI comments.
    Filters alerts to only include those with associated comments.
    
    Returns:
        List of AlertId strings that have comments
    """
    alerts_df = load_alerts()
    comments_df = load_ai_comments()
    
    if alerts_df.empty or comments_df.empty:
        return []
    
    # Get unique AlertIds that have comments
    alerts_with_comments = comments_df['AlertId'].unique()
    
    # Filter alerts dataframe to only include alerts with comments
    filtered_alerts = alerts_df[alerts_df['AlertId'].isin(alerts_with_comments)]
    
    if filtered_alerts.empty:
        return []
    
    return sorted(filtered_alerts['AlertId'].unique().tolist())


def get_alerts_with_filters(component_filter: Optional[str] = None, 
                           unit_filter: Optional[str] = None, 
                           label_filter: Optional[str] = None) -> List[str]:
    """
    Get list of available AlertIds with optional filters.
    Only returns alerts that have AI comments.
    
    Args:
        component_filter: Filter by Component (None for all)
        unit_filter: Filter by UnitId (None for all)
        label_filter: Filter by Label (None for all)
    
    Returns:
        List of filtered AlertId strings that have comments
    """
    alerts_df = load_alerts()
    comments_df = load_ai_comments()
    
    if alerts_df.empty or comments_df.empty:
        return []
    
    # Get unique AlertIds that have comments
    alerts_with_comments = comments_df['AlertId'].unique()
    
    # Filter alerts dataframe to only include alerts with comments
    filtered_alerts = alerts_df[alerts_df['AlertId'].isin(alerts_with_comments)]
    
    if filtered_alerts.empty:
        return []
    
    # Apply filters
    if component_filter and component_filter != 'All':
        filtered_alerts = filtered_alerts[filtered_alerts['Component'] == component_filter]
    
    if unit_filter and unit_filter != 'All':
        filtered_alerts = filtered_alerts[filtered_alerts['UnitId'] == unit_filter]
    
    if label_filter and label_filter != 'All':
        filtered_alerts = filtered_alerts[filtered_alerts['Label'] == label_filter]
    
    if filtered_alerts.empty:
        return []
    
    return sorted(filtered_alerts['AlertId'].unique().tolist())


def get_alert_filter_options() -> Dict[str, List[str]]:
    """
    Get available filter options for alerts that have AI comments.
    
    Returns:
        Dictionary with lists of unique values for each filter field
    """
    alerts_df = load_alerts()
    comments_df = load_ai_comments()
    
    if alerts_df.empty or comments_df.empty:
        return {'components': [], 'units': [], 'labels': []}
    
    # Get unique AlertIds that have comments
    alerts_with_comments = comments_df['AlertId'].unique()
    
    # Filter alerts dataframe to only include alerts with comments
    filtered_alerts = alerts_df[alerts_df['AlertId'].isin(alerts_with_comments)]
    
    if filtered_alerts.empty:
        return {'components': [], 'units': [], 'labels': []}
    
    # Get unique values for each filter field
    components = ['All'] + sorted([str(x) for x in filtered_alerts['Component'].dropna().unique()])
    units = ['All'] + sorted([str(x) for x in filtered_alerts['UnitId'].dropna().unique()])
    labels = ['All'] + sorted([str(x) for x in filtered_alerts['Label'].dropna().unique()])
    
    return {
        'components': components,
        'units': units, 
        'labels': labels
    }


def get_alerts_summary() -> Dict[str, int]:
    """
    Get summary of alerts with and without comments.
    
    Returns:
        Dictionary with total alerts, alerts with comments, and alerts without comments
    """
    alerts_df = load_alerts()
    comments_df = load_ai_comments()
    
    if alerts_df.empty:
        return {"total_alerts": 0, "alerts_with_comments": 0, "alerts_without_comments": 0}
    
    total_alerts = len(alerts_df['AlertId'].unique())
    
    if comments_df.empty:
        return {"total_alerts": total_alerts, "alerts_with_comments": 0, "alerts_without_comments": total_alerts}
    
    alerts_with_comments = len(comments_df['AlertId'].unique())
    alerts_without_comments = total_alerts - alerts_with_comments
    
    return {
        "total_alerts": total_alerts,
        "alerts_with_comments": alerts_with_comments, 
        "alerts_without_comments": alerts_without_comments
    }


def validate_data_files() -> Dict[str, bool]:
    """
    Validate that all required data files exist.
    
    Returns:
        Dictionary mapping file names to existence status
    """
    files_status = {
        "alerts.parquet": ALERTS_FILE.exists(),
        "oil_measurements.parquet": OIL_FILE.exists(),
        "telemetry_measurements.parquet": TELEMETRY_FILE.exists(),
        "ai_comments.parquet": COMMENTS_FILE.exists()
    }
    
    return files_status


def get_data_stats() -> Dict[str, any]:
    """
    Get basic statistics about the loaded data.
    
    Returns:
        Dictionary with data statistics
    """
    try:
        alerts_df = load_alerts()
        oil_df = load_oil_measurements()
        tel_df = load_telemetry_measurements()
        comments_df = load_ai_comments()
        
        valid_ids = comments_df.AlertId.unique()
        alerts_df = alerts_df[alerts_df.AlertId.isin(valid_ids)]
        
        oil_ids = alerts_df.OilAlertId.unique()
        tel_ids = alerts_df.TelAlertId.unique()
        
        oil_df = oil_df[oil_df.OilAlertId.isin(oil_ids)]
        tel_df = tel_df[tel_df.TelAlertId.isin(tel_ids)]
        
        return {
            "alerts_count": len(alerts_df),
            "oil_measurements_count": len(oil_df),
            "telemetry_measurements_count": len(tel_df),
            "ai_comments_count": len(comments_df),
            "unique_units": len(alerts_df['UnitId'].unique()) if not alerts_df.empty else 0,
            "unique_components": len(alerts_df['Component'].unique()) if not alerts_df.empty else 0,
            "comment_types": comments_df['CommentType'].unique().tolist() if not comments_df.empty else []
        }
    except Exception as e:
        return {"error": str(e)}