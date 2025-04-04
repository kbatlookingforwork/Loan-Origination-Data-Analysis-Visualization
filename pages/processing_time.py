import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px

# Import custom modules
from visualization import plot_processing_time_boxplot, plot_processing_time_trend
from utils import create_date_filters, filter_dataframe, display_metric_card, format_time
from statistics import detect_trends

# Set page configuration
st.set_page_config(
    page_title="Processing Time Analysis",
    page_icon="⏱️",
    layout="wide"
)

# Check if data is available in session state
if 'data' not in st.session_state or st.session_state.data is None or 'processor' not in st.session_state:
    st.error("No data available for analysis. Please upload data on the main page.")
    st.stop()

# Initialize
processor = st.session_state.processor
data = processor.data

# Page title
st.title("Loan Processing Time Analysis")
st.markdown("Analyze processing times to identify bottlenecks and optimize workflow.")

# Sidebar for filters
st.sidebar.header("Filters")

# Date range filter
start_date, end_date = create_date_filters(data, 'application_date', st.sidebar)

# Status filter
if 'status_standardized' in data.columns:
    status_options = data['status_standardized'].unique().tolist()
    selected_status = st.sidebar.multiselect("Status", status_options, default=status_options)
else:
    selected_status = None

# Apply filters
filters = {}
if start_date and end_date:
    filters['application_date'] = (pd.Timestamp(start_date), pd.Timestamp(end_date) + timedelta(days=1) - timedelta(microseconds=1))
if selected_status:
    filters['status_standardized'] = selected_status

filtered_data = filter_dataframe(data, filters)

# Display warning if filtered data is empty or has no processing time data
if filtered_data.empty:
    st.warning("No data available with the selected filters. Please adjust your filters.")
    st.stop()

if 'processing_time_days' not in filtered_data.columns:
    st.error("Processing time data is not available. Make sure to map application and decision dates correctly.")
    st.stop()

# Filter out rows with missing processing time
processing_time_data = filtered_data.dropna(subset=['processing_time_days'])

if processing_time_data.empty:
    st.warning("No processing time data available. Make sure application and decision dates are valid.")
    st.stop()

# Calculate key metrics
total_applications = len(processing_time_data)
mean_days = processing_time_data['processing_time_days'].mean()
median_days = processing_time_data['processing_time_days'].median()
min_days = processing_time_data['processing_time_days'].min()
max_days = processing_time_data['processing_time_days'].max()

# Create metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    display_metric_card("Total Applications", total_applications)

with col2:
    display_metric_card("Mean Processing Time", f"{mean_days:.1f} days")

with col3:
    display_metric_card("Median Processing Time", f"{median_days:.1f} days")

with col4:
    display_metric_card("Range", f"{min_days:.1f} - {max_days:.1f} days")

# Distribution of processing times
st.subheader("Processing Time Distribution")

# Option to group by status
group_by_status = st.checkbox("Group by application status", value=True)

if group_by_status and 'status_standardized' in processing_time_data.columns:
    group_col = 'status_standardized'
else:
    group_col = None

# Plot processing time distribution
st.markdown("""
### Processing Time Distribution
This boxplot shows the distribution of processing times for loan applications. The box represents the middle 50% of processing times,
with the line inside the box showing the median. The whiskers extend to show the range of processing times, excluding outliers.
This visualization helps identify typical processing durations and any concerning delays.
""")

fig = plot_processing_time_boxplot(processing_time_data, group_col=group_col)
st.plotly_chart(fig, use_container_width=True, key="processing_time_distribution")

# Processing time trend analysis
st.subheader("Processing Time Trend")

# Time period selection
time_period = st.radio(
    "Select time period for trend",
    ("Monthly", "Quarterly", "Yearly"),
    horizontal=True
)

# Prepare data for trend analysis based on selected time period
if time_period == "Monthly" and 'application_yearmonth' in processing_time_data.columns:
    grouped = processing_time_data.groupby('application_yearmonth')
    time_col = 'application_yearmonth'
elif time_period == "Quarterly":
    processing_time_data['quarter'] = processing_time_data['application_date'].dt.to_period('Q').astype(str)
    grouped = processing_time_data.groupby('quarter')
    time_col = 'quarter'
elif time_period == "Yearly" and 'application_year' in processing_time_data.columns:
    grouped = processing_time_data.groupby('application_year')
    time_col = 'application_year'
else:
    st.warning(f"Cannot group by {time_period}. Using monthly grouping instead.")
    if 'application_yearmonth' in processing_time_data.columns:
        grouped = processing_time_data.groupby('application_yearmonth')
        time_col = 'application_yearmonth'
    else:
        st.error("Cannot create time trend analysis. Check date columns mapping.")
        st.stop()

# Calculate processing time statistics per time period
processing_time_trend = pd.DataFrame({
    'count': grouped['processing_time_days'].count(),
    'mean_days': grouped['processing_time_days'].mean(),
    'median_days': grouped['processing_time_days'].median(),
    'min_days': grouped['processing_time_days'].min(),
    'max_days': grouped['processing_time_days'].max()
}).reset_index()

# Plot processing time trend
if not processing_time_trend.empty:
    st.markdown("""
    ### Processing Time Trend
    This chart shows how loan processing times have changed over time. The lines show both mean (average) and median 
    processing times. The median is less affected by outliers, so comparing these metrics helps identify if a few extreme 
    cases are skewing the average. Monitoring this trend helps detect efficiency improvements or emerging bottlenecks.
    """)
    
    fig = plot_processing_time_trend(processing_time_trend, time_col=time_col)
    st.plotly_chart(fig, use_container_width=True, key="processing_time_trend")
    
    # Detect trend
    trend_info = detect_trends(processing_time_trend, 'mean_days')
    
    # Display trend information
    st.info(f"Trend Analysis: Processing time is {trend_info['trend']} with {trend_info['confidence']} confidence")
    
    if trend_info['recent_change'] is not None:
        recent_change = trend_info['recent_change'] * 100
        if abs(recent_change) > 5:
            direction = "increased" if recent_change > 0 else "decreased"
            st.info(f"Recent change: Processing time has {direction} by {abs(recent_change):.1f}% in the most recent periods")
else:
    st.warning("Insufficient data to generate processing time trend.")

# Outlier analysis
st.subheader("Processing Time Outlier Analysis")

# Calculate IQR for outlier detection
q1 = processing_time_data['processing_time_days'].quantile(0.25)
q3 = processing_time_data['processing_time_days'].quantile(0.75)
iqr = q3 - q1
upper_bound = q3 + (1.5 * iqr)

# Identify outliers
outliers = processing_time_data[processing_time_data['processing_time_days'] > upper_bound]
outlier_percentage = len(outliers) / len(processing_time_data) * 100

# Display outlier information
col1, col2 = st.columns(2)

with col1:
    display_metric_card("Outlier Threshold", f"{upper_bound:.1f} days", 
                       delta_description="Applications taking longer than this are considered outliers")

with col2:
    display_metric_card("Outlier Percentage", f"{outlier_percentage:.1f}%", 
                       delta_description=f"{len(outliers)} out of {len(processing_time_data)} applications")

# Display outliers if any exist
if not outliers.empty:
    st.subheader("Outlier Applications")
    with st.expander("View outlier details"):
        # Sort outliers by processing time (descending)
        outliers_sorted = outliers.sort_values('processing_time_days', ascending=False)
        
        # Select relevant columns to display
        display_columns = ['application_id', 'application_date', 'decision_date', 
                          'processing_time_days', 'status_standardized']
        
        # Add additional relevant columns if available
        potential_columns = ['loan_amount', 'income', 'credit_score', 'rejection_reason']
        display_columns.extend([col for col in potential_columns if col in outliers_sorted.columns])
        
        # Filter columns to only those that exist
        display_columns = [col for col in display_columns if col in outliers_sorted.columns]
        
        # Display the dataframe
        st.dataframe(outliers_sorted[display_columns])

# Processing time by factors
st.subheader("Processing Time by Factors")

# Select factor for analysis
factor_options = []

# Add status as a factor if available
if 'status_standardized' in data.columns:
    factor_options.append('status_standardized')

# Add loan amount as factor if available
if 'loan_amount' in data.columns:
    factor_options.append('loan_amount')

# Add other potential factors
potential_factors = ['income', 'credit_score']
factor_options.extend([col for col in potential_factors if col in data.columns])

# Add any categorical columns that might be meaningful
categorical_cols = data.select_dtypes(include=['object', 'category']).columns
for col in categorical_cols:
    if col not in ['application_id', 'status', 'status_standardized', 'rejection_reason']:
        unique_values = data[col].nunique()
        if 2 <= unique_values <= 20:  # Only include factors with reasonable number of categories
            factor_options.append(col)

if factor_options:
    selected_factor = st.selectbox("Select factor for analysis", factor_options)
    
    if selected_factor in data.columns:
        # For numeric factors, create bins
        if pd.api.types.is_numeric_dtype(data[selected_factor]):
            num_bins = st.slider("Number of bins", min_value=3, max_value=10, value=5)
            
            # Create bins
            factor_data = processing_time_data.copy()
            factor_min = factor_data[selected_factor].min()
            factor_max = factor_data[selected_factor].max()
            bin_edges = np.linspace(factor_min, factor_max, num_bins + 1)
            bin_labels = [f"{bin_edges[i]:.0f}-{bin_edges[i+1]:.0f}" for i in range(num_bins)]
            
            factor_data['factor_bin'] = pd.cut(factor_data[selected_factor], bins=bin_edges, labels=bin_labels)
            
            st.markdown("""
            ### Processing Time by Numeric Factor
            This chart shows how processing times vary across different ranges of the selected numeric factor.
            Each box represents the distribution of processing times within that range. This visualization helps
            identify whether certain value ranges (like loan amounts or credit scores) are associated with 
            faster or slower processing times.
            """)
            
            # Plot boxplot by bin
            fig = plot_processing_time_boxplot(factor_data, group_col='factor_bin')
            st.plotly_chart(fig, use_container_width=True, key="processing_time_by_numeric_factor")
            
            # Calculate correlation
            correlation = factor_data[selected_factor].corr(factor_data['processing_time_days'])
            
            if not pd.isna(correlation):
                direction = "positive" if correlation > 0 else "negative"
                strength = "strong" if abs(correlation) > 0.5 else "moderate" if abs(correlation) > 0.3 else "weak"
                
                st.info(f"Correlation Analysis: {selected_factor.replace('_', ' ').title()} has a {strength} {direction} correlation ({correlation:.2f}) with processing time")
        
        # For categorical factors
        else:
            st.markdown("""
            ### Processing Time by Categorical Factor
            This chart shows how processing times vary across different categories of the selected factor.
            Each box represents the distribution of processing times within that category. This helps identify
            whether certain categories (like loan types or departments) consistently experience faster or slower
            processing times, which can inform resource allocation decisions.
            """)
            
            # Plot boxplot by category
            fig = plot_processing_time_boxplot(processing_time_data, group_col=selected_factor)
            st.plotly_chart(fig, use_container_width=True, key="processing_time_by_categorical_factor")
else:
    st.warning("No suitable factors found for processing time analysis.")

# Raw data view
st.subheader("Raw Data")
with st.expander("View filtered data"):
    st.dataframe(processing_time_data)
