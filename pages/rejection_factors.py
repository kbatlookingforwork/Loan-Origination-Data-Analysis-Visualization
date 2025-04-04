import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Import custom modules
from visualization import plot_rejection_reasons, plot_correlation_heatmap, plot_loan_amount_comparison
from utils import create_date_filters, filter_dataframe, display_metric_card
from statistics import calculate_summary_metrics

# Set page configuration
st.set_page_config(
    page_title="Rejection Factors Analysis",
    page_icon="❌",
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
st.title("Loan Rejection Factors Analysis")
st.markdown("Analyze factors that influence loan rejection and identify opportunities for improvement.")

# Sidebar for filters
st.sidebar.header("Filters")

# Date range filter
start_date, end_date = create_date_filters(data, 'application_date', st.sidebar)

# Additional filters
loan_amount_filter = st.sidebar.checkbox("Filter by loan amount")
if loan_amount_filter and 'loan_amount' in data.columns:
    min_amount = float(data['loan_amount'].min())
    max_amount = float(data['loan_amount'].max())
    loan_amount_range = st.sidebar.slider(
        "Loan Amount Range",
        min_value=min_amount,
        max_value=max_amount,
        value=(min_amount, max_amount)
    )
else:
    loan_amount_range = None

# Apply filters
filters = {}
if start_date and end_date:
    filters['application_date'] = (pd.Timestamp(start_date), pd.Timestamp(end_date) + timedelta(days=1) - timedelta(microseconds=1))
if loan_amount_range:
    filters['loan_amount'] = loan_amount_range

filtered_data = filter_dataframe(data, filters)

# Display warning if filtered data is empty
if filtered_data.empty:
    st.warning("No data available with the selected filters. Please adjust your filters.")
    st.stop()

# Filter to only rejected applications for rejection-specific analysis
rejected_data = filtered_data[filtered_data['status_standardized'] == 'rejected']

if rejected_data.empty:
    st.warning("No rejected applications found with the current filters.")
    
    # Still show general metrics and correlations
    total_applications = len(filtered_data)
    approved = filtered_data['status_standardized'].eq('approved').sum()
    approval_rate = approved / total_applications if total_applications > 0 else 0
    
    st.subheader("General Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        display_metric_card("Total Applications", total_applications)
    
    with col2:
        display_metric_card("Approved Applications", approved)
    
    with col3:
        display_metric_card("Approval Rate", approval_rate)
        
    # Skip the rest of the rejection-specific analysis
    st.subheader("Factor Correlation Analysis")
    
    # Get correlation factors
    correlation_data = processor.get_correlation_factors()
    
    if not correlation_data.empty:
        fig = plot_correlation_heatmap(correlation_data)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No correlation data available. Make sure numeric factors are correctly mapped.")
    
    st.stop()

# Calculate key metrics
total_applications = len(filtered_data)
rejected_count = len(rejected_data)
rejection_rate = rejected_count / total_applications if total_applications > 0 else 0

# Create metrics row
col1, col2, col3 = st.columns(3)

with col1:
    display_metric_card("Total Applications", total_applications)

with col2:
    display_metric_card("Rejected Applications", rejected_count)

with col3:
    display_metric_card("Rejection Rate", rejection_rate)

# Rejection reasons analysis
st.subheader("Rejection Reasons")

if 'rejection_reason' in rejected_data.columns:
    # Get top rejection reasons
    rejection_factors = processor.get_rejection_factors(n_top=10)
    
    if not rejection_factors.empty:
        st.markdown("""
        ### Top Rejection Reasons
        This chart displays the most common reasons for loan application rejections. The bars show both the 
        count and percentage of each reason. Understanding these patterns helps identify the most significant 
        barriers to approval that applicants face and areas where process improvements might be needed.
        """)
        
        fig = plot_rejection_reasons(rejection_factors)
        st.plotly_chart(fig, use_container_width=True, key="rejection_reasons_chart")
    else:
        st.warning("No rejection reason data available or all values are missing.")
else:
    st.warning("Rejection reason data is not available. Please map the rejection reason column in the data processor.")

# Factor correlation analysis
st.subheader("Factor Correlation Analysis")

# Get correlation factors
correlation_data = processor.get_correlation_factors()

if not correlation_data.empty:
    st.markdown("""
    ### Factor Correlation Analysis
    This heatmap displays how strongly different factors correlate with application approval. 
    Deeper colors indicate stronger correlations, with blue showing positive correlation (factor increases approval likelihood) 
    and red showing negative correlation (factor decreases approval likelihood). This visualization helps 
    identify which factors have the strongest influence on the loan decision process.
    """)
    
    fig = plot_correlation_heatmap(correlation_data)
    st.plotly_chart(fig, use_container_width=True, key="correlation_heatmap_chart")
    
    # Display most significant correlations with descriptions
    st.subheader("Key Correlations Explained")
    
    sorted_correlations = correlation_data.sort_values(by='correlation_with_approval', key=abs, ascending=False)
    
    for _, row in sorted_correlations.iterrows():
        factor = row['factor']
        corr = row['correlation_with_approval']
        
        if abs(corr) > 0.1:  # Only show significant correlations
            direction = "positive" if corr > 0 else "negative"
            factor_name = factor.replace('_', ' ').title()
            
            if direction == "positive":
                explanation = f"Higher {factor_name.lower()} is associated with higher approval rates."
            else:
                explanation = f"Higher {factor_name.lower()} is associated with lower approval rates."
            
            st.markdown(f"**{factor_name}** (correlation: {corr:.2f}): {explanation}")
else:
    st.warning("No correlation data available. Make sure numeric factors are correctly mapped.")

# Loan amount analysis by status
st.subheader("Loan Amount Analysis by Status")

if 'loan_amount' in filtered_data.columns:
    loan_amount_data = processor.get_loan_amount_analysis()
    
    if not loan_amount_data.empty:
        st.markdown("""
        ### Loan Amount Analysis by Status
        This chart compares the average and median loan amounts for approved versus rejected applications.
        The comparison helps identify if loan size is a significant factor in the decision process and whether
        there's a pattern of approving or rejecting certain loan amounts. Large differences may suggest 
        undisclosed loan amount thresholds in the approval process.
        """)
        
        fig = plot_loan_amount_comparison(loan_amount_data)
        st.plotly_chart(fig, use_container_width=True, key="loan_amount_comparison_chart")
    else:
        st.warning("No loan amount data available for analysis.")
else:
    st.warning("Loan amount data is not available. Please map the loan amount column in the data processor.")

# Detailed rejection analysis by specific factors
st.subheader("Detailed Rejection Analysis")

# Select numerical factors for additional analysis
numerical_factors = []
if 'loan_amount' in filtered_data.columns:
    numerical_factors.append('loan_amount')
if 'income' in filtered_data.columns:
    numerical_factors.append('income')
if 'credit_score' in filtered_data.columns:
    numerical_factors.append('credit_score')

if numerical_factors:
    selected_factor = st.selectbox("Select factor for detailed analysis", numerical_factors)
    
    # Create binned analysis
    if selected_factor in filtered_data.columns:
        # Create bins
        num_bins = st.slider("Number of bins", min_value=3, max_value=10, value=5)
        
        factor_data = filtered_data.copy()
        factor_min = factor_data[selected_factor].min()
        factor_max = factor_data[selected_factor].max()
        bin_edges = np.linspace(factor_min, factor_max, num_bins + 1)
        bin_labels = [f"{bin_edges[i]:.0f}-{bin_edges[i+1]:.0f}" for i in range(num_bins)]
        
        factor_data['factor_bin'] = pd.cut(factor_data[selected_factor], bins=bin_edges, labels=bin_labels)
        
        # Calculate rejection rate by bin
        grouped = factor_data.groupby('factor_bin')
        rejection_by_bin = pd.DataFrame({
            'total': grouped.size(),
            'rejected': grouped['status_standardized'].apply(lambda x: (x == 'rejected').sum()),
        })
        
        rejection_by_bin['rejection_rate'] = rejection_by_bin['rejected'] / rejection_by_bin['total']
        rejection_by_bin = rejection_by_bin.reset_index()
        
        # Create the figure
        fig = go.Figure()
        
        # Add rejection rate line
        fig.add_trace(
            go.Scatter(
                x=rejection_by_bin['factor_bin'],
                y=rejection_by_bin['rejection_rate'].round(3),
                name="Rejection Rate",
                line=dict(color="#C0392B", width=3),
                mode="lines+markers",
                yaxis="y"
            )
        )
        
        # Add application count bars
        fig.add_trace(
            go.Bar(
                x=rejection_by_bin['factor_bin'],
                y=rejection_by_bin['total'],
                name="Application Count",
                marker_color="#F5B7B1",
                opacity=0.7,
                yaxis="y2"
            )
        )
        
        # Set x-axis title
        fig.update_xaxes(title_text=selected_factor.replace('_', ' ').title() + " Range")
        
        # Update layout for dual y-axes
        fig.update_layout(
            yaxis=dict(
                title="Rejection Rate",
                range=[0, max(1.0, rejection_by_bin['rejection_rate'].max() * 1.1)],
                tickformat=".0%"
            ),
            yaxis2=dict(
                title="Number of Applications",
                overlaying="y",
                side="right"
            )
        )
        
        fig.update_layout(
            title_text=f"Rejection Rate by {selected_factor.replace('_', ' ').title()}",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.markdown("""
        ### Rejection Rate by Factor Range
        This chart shows how rejection rates vary across different ranges of the selected numeric factor.
        The line represents the rejection rate for each range, while the bars show the number of applications.
        This visualization helps identify threshold values where rejection rates significantly change and
        helps target specific value ranges for deeper investigation.
        """)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add some analysis text
        highest_rejection = rejection_by_bin.loc[rejection_by_bin['rejection_rate'].idxmax()]
        lowest_rejection = rejection_by_bin.loc[rejection_by_bin['rejection_rate'].idxmin()]
        
        st.markdown(f"""
        ### Key Observations:
        
        - **Highest Rejection Rate**: {highest_rejection['factor_bin']} range with {highest_rejection['rejection_rate']*100:.1f}% rejection rate
        - **Lowest Rejection Rate**: {lowest_rejection['factor_bin']} range with {lowest_rejection['rejection_rate']*100:.1f}% rejection rate
        """)
        
        if 'rejection_reason' in rejected_data.columns:
            st.subheader(f"Top Rejection Reasons by {selected_factor.replace('_', ' ').title()} Range")
            
            # Create tabs for each bin
            tabs = st.tabs([str(bin_label) for bin_label in rejection_by_bin['factor_bin']])
            
            for i, tab in enumerate(tabs):
                bin_label = rejection_by_bin['factor_bin'].iloc[i]
                
                with tab:
                    # Filter to rejections in this bin
                    bin_rejections = rejected_data.copy()
                    if 'factor_bin' not in bin_rejections.columns:
                        bin_rejections['factor_bin'] = pd.cut(bin_rejections[selected_factor], bins=bin_edges, labels=bin_labels)
                    bin_rejections = bin_rejections[bin_rejections['factor_bin'] == bin_label]
                    
                    if not bin_rejections.empty and 'rejection_reason' in bin_rejections.columns:
                        # Get rejection reasons for this bin
                        reason_counts = bin_rejections['rejection_reason'].value_counts().reset_index()
                        reason_counts.columns = ['reason', 'count']
                        
                        # Calculate percentage
                        total_bin_rejections = reason_counts['count'].sum()
                        reason_counts['percentage'] = (reason_counts['count'] / total_bin_rejections * 100).round(1)
                        
                        # Show top 5 reasons
                        st.table(reason_counts.head(5))
                    else:
                        st.write("No rejection data available for this range.")
else:
    st.warning("No numerical factors available for detailed rejection analysis.")

# Raw rejection data
st.subheader("Rejected Applications Data")
with st.expander("View rejected applications data"):
    st.dataframe(rejected_data)
