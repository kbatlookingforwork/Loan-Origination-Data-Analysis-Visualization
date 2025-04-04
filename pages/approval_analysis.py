import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Import custom modules
from visualization import plot_approval_rate_trend, plot_approval_rate_by_factor
from utils import create_date_filters, filter_dataframe, display_metric_card
from statistics import detect_trends

# Set page configuration
st.set_page_config(
    page_title="Approval Rate Analysis",
    page_icon="📈",
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
st.title("Loan Approval Rate Analysis")
st.markdown("Analyze approval trends and identify factors influencing approval rates.")

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

# Display warning if filtered data is empty
if filtered_data.empty:
    st.warning("No data available with the selected filters. Please adjust your filters.")
    st.stop()

# Calculate key metrics
total_applications = len(filtered_data)
approved = filtered_data['status_standardized'].eq('approved').sum()
rejected = filtered_data['status_standardized'].eq('rejected').sum()
approval_rate = approved / total_applications if total_applications > 0 else 0

# Create metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    display_metric_card("Total Applications", total_applications)

with col2:
    display_metric_card("Approved", approved)

with col3:
    display_metric_card("Rejected", rejected)

with col4:
    display_metric_card("Approval Rate", approval_rate)

# Time period selection for trend analysis
st.subheader("Approval Rate Trend")
time_period = st.radio(
    "Select time period for trend",
    ("Monthly", "Quarterly", "Yearly"),
    horizontal=True
)

# Generate approval rate trend data
period_mapping = {"Monthly": "monthly", "Quarterly": "quarterly", "Yearly": "yearly"}
approval_trend_data = processor.get_approval_rate(time_period=period_mapping[time_period])

# Filter trend data by date if needed
if start_date and end_date:
    if 'application_yearmonth' in approval_trend_data.columns:
        # For monthly data
        approval_trend_data = approval_trend_data[
            (approval_trend_data['application_yearmonth'] >= start_date.strftime('%Y-%m')) &
            (approval_trend_data['application_yearmonth'] <= end_date.strftime('%Y-%m'))
        ]
    elif 'quarter' in approval_trend_data.columns:
        # For quarterly data, this is more complex and would need proper filtering
        pass
    elif 'application_year' in approval_trend_data.columns:
        # For yearly data
        approval_trend_data = approval_trend_data[
            (approval_trend_data['application_year'] >= start_date.year) &
            (approval_trend_data['application_year'] <= end_date.year)
        ]

# Plot approval rate trend
if not approval_trend_data.empty:
    time_col = 'application_yearmonth' if 'application_yearmonth' in approval_trend_data.columns else \
              'quarter' if 'quarter' in approval_trend_data.columns else 'application_year'
    
    st.markdown("""
    ### Approval Rate Over Time
    This chart shows the approval rate trend and application volume over time. The line represents the percentage of 
    applications approved, while the bars show the total number of applications received in each period. This helps identify
    seasonal patterns and long-term trends in approval rates.
    """)
              
    fig = plot_approval_rate_trend(approval_trend_data, time_col=time_col)
    st.plotly_chart(fig, use_container_width=True, key="approval_rate_trend")
    
    # Detect trend
    trend_info = detect_trends(approval_trend_data, 'approval_rate')
    
    # Display trend information
    st.info(f"Trend Analysis: Approval rate is {trend_info['trend']} with {trend_info['confidence']} confidence")
    
    if trend_info['recent_change'] is not None:
        recent_change_pct = trend_info['recent_change'] * 100
        if abs(recent_change_pct) > 1:
            direction = "increased" if recent_change_pct > 0 else "decreased"
            st.info(f"Recent change: Approval rate has {direction} by {abs(recent_change_pct):.1f}% in the most recent periods")
else:
    st.warning("Insufficient data to generate approval rate trend.")

# Approval rate by other factors
st.subheader("Approval Rate by Factors")

# Select factor for analysis
factor_options = []

# Numeric factors
numeric_cols = data.select_dtypes(include=['number']).columns
potential_numeric_factors = ['loan_amount', 'income', 'credit_score']
available_numeric_factors = [col for col in potential_numeric_factors if col in numeric_cols]

# Categorical factors - add any categorical columns that might be meaningful
categorical_cols = data.select_dtypes(include=['object', 'category']).columns
potential_categorical_factors = []
for col in categorical_cols:
    if col not in ['application_id', 'status', 'status_standardized', 'rejection_reason']:
        unique_values = data[col].nunique()
        if 2 <= unique_values <= 20:  # Only include factors with reasonable number of categories
            potential_categorical_factors.append(col)

factor_options = available_numeric_factors + potential_categorical_factors

if factor_options:
    selected_factor = st.selectbox("Select factor for analysis", factor_options)
    
    if selected_factor in data.columns:
        # For numeric factors, create bins
        if selected_factor in numeric_cols:
            num_bins = st.slider("Number of bins", min_value=3, max_value=10, value=5)
            
            # Create bins
            factor_data = filtered_data.copy()
            factor_min = factor_data[selected_factor].min()
            factor_max = factor_data[selected_factor].max()
            bin_edges = np.linspace(factor_min, factor_max, num_bins + 1)
            bin_labels = [f"{bin_edges[i]:.0f}-{bin_edges[i+1]:.0f}" for i in range(num_bins)]
            
            factor_data['factor_bin'] = pd.cut(factor_data[selected_factor], bins=bin_edges, labels=bin_labels)
            
            # Calculate approval rate by bin
            grouped = factor_data.groupby('factor_bin')
            approval_by_factor = pd.DataFrame({
                'total_applications': grouped.size(),
                'approved': grouped['status_standardized'].apply(lambda x: (x == 'approved').sum()),
            })
            
            approval_by_factor['approval_rate'] = approval_by_factor['approved'] / approval_by_factor['total_applications']
            approval_by_factor = approval_by_factor.reset_index()
            
            st.markdown("""
            ### Approval Rate by Numeric Factor
            This chart shows how approval rates vary across different ranges of the selected numeric factor. 
            The line shows the approval rate for each range, while the bars display the number of applications.
            This visualization helps identify optimal ranges and potential thresholds affecting approval decisions.
            """)
            
            # Plot
            fig = plot_approval_rate_by_factor(approval_by_factor, factor_col='factor_bin')
            st.plotly_chart(fig, use_container_width=True, key="approval_rate_by_numeric_factor")
            
            # Calculate correlation if data allows
            if len(factor_data) > 10:
                factor_data['is_approved'] = (factor_data['status_standardized'] == 'approved').astype(int)
                correlation = factor_data[selected_factor].corr(factor_data['is_approved'])
                
                if not pd.isna(correlation):
                    direction = "positive" if correlation > 0 else "negative"
                    strength = "strong" if abs(correlation) > 0.5 else "moderate" if abs(correlation) > 0.3 else "weak"
                    
                    st.info(f"Correlation Analysis: {selected_factor.replace('_', ' ').title()} has a {strength} {direction} correlation ({correlation:.2f}) with approval rate")
        
        # For categorical factors
        else:
            # Calculate approval rate by category
            grouped = filtered_data.groupby(selected_factor)
            approval_by_factor = pd.DataFrame({
                'total_applications': grouped.size(),
                'approved': grouped['status_standardized'].apply(lambda x: (x == 'approved').sum()),
            })
            
            approval_by_factor['approval_rate'] = approval_by_factor['approved'] / approval_by_factor['total_applications']
            approval_by_factor = approval_by_factor.reset_index()
            
            # Sort by total applications
            approval_by_factor = approval_by_factor.sort_values('total_applications', ascending=False)
            
            st.markdown("""
            ### Approval Rate by Categorical Factor
            This chart shows how approval rates vary across different categories of the selected factor.
            The line shows the approval rate for each category, while the bars display the number of applications.
            This helps identify which categories have higher approval rates and whether volume correlates with approvals.
            """)
            
            # Plot
            fig = plot_approval_rate_by_factor(approval_by_factor, factor_col=selected_factor)
            st.plotly_chart(fig, use_container_width=True, key="approval_rate_by_categorical_factor")
else:
    st.warning("No suitable factors found for approval rate analysis.")

# Raw data view
st.subheader("Raw Data")
with st.expander("View filtered data"):
    st.dataframe(filtered_data)
