import pandas as pd
import streamlit as st
import base64
import io
from datetime import datetime

def format_time(seconds):
    """
    Format time in seconds to a human-readable string
    
    Parameters:
    seconds (float): Time in seconds
    
    Returns:
    str: Formatted time string
    """
    if seconds is None or pd.isna(seconds):
        return "N/A"
        
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"

def get_unique_values(df, column, max_display=10):
    """
    Get unique values from a dataframe column
    
    Parameters:
    df (pd.DataFrame): Dataframe
    column (str): Column name
    max_display (int): Maximum number of unique values to return
    
    Returns:
    list: List of unique values
    """
    if df is None or column not in df.columns:
        return []
        
    values = df[column].dropna().unique()
    
    if len(values) > max_display:
        # Return most frequent values if there are too many
        value_counts = df[column].value_counts().head(max_display)
        return value_counts.index.tolist()
    
    return values.tolist()

def download_dataframe(df, filename=None):
    """
    Generate a download link for a dataframe
    
    Parameters:
    df (pd.DataFrame): Dataframe to download
    filename (str): Filename without extension
    
    Returns:
    str: HTML link for downloading the file
    """
    if filename is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"loan_data_{now}"
    
    # Convert dataframe to CSV
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download CSV</a>'
    return href

def download_excel(df, filename=None):
    """
    Generate a download link for a dataframe as Excel
    
    Parameters:
    df (pd.DataFrame): Dataframe to download
    filename (str): Filename without extension
    
    Returns:
    bytes: Excel file as bytes
    """
    if filename is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"loan_data_{now}"
    
    # Convert dataframe to Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
    
    return output.getvalue()

def create_date_filters(df, date_col, container):
    """
    Create date range filters
    
    Parameters:
    df (pd.DataFrame): Dataframe
    date_col (str): Date column name
    container: Streamlit container to place the filters
    
    Returns:
    tuple: (start_date, end_date)
    """
    if df is None or date_col not in df.columns:
        return None, None
    
    # Get min and max dates
    date_series = pd.to_datetime(df[date_col])
    min_date = date_series.min().date()
    max_date = date_series.max().date()
    
    # Create two columns for the filters
    col1, col2 = container.columns(2)
    
    # Create the date inputs
    start_date = col1.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
    end_date = col2.date_input("End Date", max_date, min_value=min_date, max_value=max_date)
    
    return start_date, end_date

def filter_dataframe(df, filters):
    """
    Apply filters to a dataframe
    
    Parameters:
    df (pd.DataFrame): Dataframe to filter
    filters (dict): Dictionary of filters {column: value}
    
    Returns:
    pd.DataFrame: Filtered dataframe
    """
    if df is None or not filters:
        return df
    
    filtered_df = df.copy()
    
    for column, value in filters.items():
        if column in filtered_df.columns:
            if isinstance(value, (list, tuple)) and len(value) == 2:
                # Range filter (typically for dates)
                start, end = value
                
                if pd.api.types.is_datetime64_any_dtype(filtered_df[column]):
                    filtered_df = filtered_df[(filtered_df[column] >= start) & (filtered_df[column] <= end)]
                else:
                    try:
                        filtered_df = filtered_df[(filtered_df[column] >= start) & (filtered_df[column] <= end)]
                    except:
                        # Skip if filter can't be applied
                        pass
            else:
                # Single value filter
                if value is not None:
                    if isinstance(value, (list, tuple)):
                        filtered_df = filtered_df[filtered_df[column].isin(value)]
                    else:
                        filtered_df = filtered_df[filtered_df[column] == value]
    
    return filtered_df

def display_metric_card(title, value, delta=None, delta_description=None):
    """
    Display a metric in a card format
    
    Parameters:
    title (str): Metric title
    value: Metric value
    delta: Delta value for the metric
    delta_description (str): Description of what the delta means
    """
    # Format values based on type
    if isinstance(value, float):
        if value < 1:
            # Percentage
            formatted_value = f"{value:.1%}"
        else:
            formatted_value = f"{value:,.1f}"
    elif isinstance(value, int):
        formatted_value = f"{value:,}"
    else:
        formatted_value = str(value)
    
    # Display the metric
    if delta is not None:
        st.metric(
            label=title,
            value=formatted_value,
            delta=delta,
            help=delta_description
        )
    else:
        st.metric(
            label=title,
            value=formatted_value,
            help=delta_description
        )
