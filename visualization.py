import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def plot_approval_rate_trend(data, time_col='application_yearmonth', rate_col='approval_rate', 
                            count_col='total_applications'):
    """
    Create a dual-axis plot of approval rate trend and application volume
    
    Parameters:
    data (pd.DataFrame): Dataframe with time period, approval rate and application count
    time_col (str): Column name for time periods
    rate_col (str): Column name for approval rate
    count_col (str): Column name for application count
    
    Returns:
    fig: Plotly figure object
    """
    if data.empty:
        return go.Figure().update_layout(
            title="No data available for approval rate trend",
            xaxis_title="Time Period",
            yaxis_title="Rate / Count"
        )
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add approval rate line
    fig.add_trace(
        go.Scatter(
            x=data[time_col],
            y=data[rate_col].round(3),
            name="Approval Rate",
            line=dict(color="#2E86C1", width=3),
            mode="lines+markers",
            yaxis="y"
        )
    )
    
    # Add application volume bars
    fig.add_trace(
        go.Bar(
            x=data[time_col],
            y=data[count_col],
            name="Application Volume",
            marker_color="#AED6F1",
            opacity=0.7,
            yaxis="y2"
        )
    )
    
    # Set x-axis title
    fig.update_xaxes(title_text="Time Period")
    
    # Update layout for dual y-axes
    fig.update_layout(
        title_text="Approval Rate Trend and Application Volume",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            title="Approval Rate",
            range=[0, max(1.0, data[rate_col].max() * 1.1)],
            tickformat=".0%"
        ),
        yaxis2=dict(
            title="Number of Applications",
            overlaying="y",
            side="right"
        )
    )
    
    return fig

def plot_processing_time_boxplot(data, group_col=None, time_col='processing_time_days'):
    """
    Create a boxplot of processing times, optionally grouped by a category
    
    Parameters:
    data (pd.DataFrame): Dataframe with processing time data
    group_col (str): Column name for grouping
    time_col (str): Column name for processing time
    
    Returns:
    fig: Plotly figure object
    """
    if group_col and group_col in data.columns:
        fig = px.box(
            data,
            x=group_col,
            y=time_col,
            color=group_col,
            title="Processing Time Distribution by " + group_col,
            labels={time_col: "Processing Time (Days)"},
            points="all"
        )
    else:
        fig = px.box(
            data,
            y=time_col,
            title="Overall Processing Time Distribution",
            labels={time_col: "Processing Time (Days)"},
            points="all"
        )
    
    fig.update_layout(
        showlegend=False,
        hovermode="closest"
    )
    
    return fig

def plot_processing_time_trend(data, time_col='application_yearmonth', mean_col='mean_days', 
                              median_col='median_days'):
    """
    Create a line chart of processing time trend over time
    
    Parameters:
    data (pd.DataFrame): Dataframe with time periods and processing time statistics
    time_col (str): Column name for time periods
    mean_col (str): Column name for mean processing time
    median_col (str): Column name for median processing time
    
    Returns:
    fig: Plotly figure object
    """
    if data.empty:
        return go.Figure().update_layout(
            title="No data available for processing time trend",
            xaxis_title="Time Period",
            yaxis_title="Processing Time (Days)"
        )
    
    fig = go.Figure()
    
    # Add mean processing time line
    fig.add_trace(
        go.Scatter(
            x=data[time_col],
            y=data[mean_col].round(1),
            name="Mean Processing Time",
            line=dict(color="#E67E22", width=3),
            mode="lines+markers"
        )
    )
    
    # Add median processing time line
    fig.add_trace(
        go.Scatter(
            x=data[time_col],
            y=data[median_col].round(1),
            name="Median Processing Time",
            line=dict(color="#F39C12", width=3, dash="dash"),
            mode="lines+markers"
        )
    )
    
    # Set x-axis title
    fig.update_xaxes(title_text="Time Period")
    
    # Set y-axis title
    fig.update_yaxes(title_text="Processing Time (Days)")
    
    fig.update_layout(
        title_text="Processing Time Trend",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_rejection_reasons(data, reason_col='reason', count_col='count', percentage_col='percentage'):
    """
    Create a horizontal bar chart of rejection reasons
    
    Parameters:
    data (pd.DataFrame): Dataframe with rejection reasons and counts
    reason_col (str): Column name for rejection reasons
    count_col (str): Column name for rejection counts
    percentage_col (str): Column name for percentage of total rejections
    
    Returns:
    fig: Plotly figure object
    """
    if data.empty:
        return go.Figure().update_layout(
            title="No rejection reason data available",
            xaxis_title="Count",
            yaxis_title="Rejection Reason"
        )
    
    # Sort data by count in descending order
    sorted_data = data.sort_values(by=count_col, ascending=True)
    
    fig = go.Figure()
    
    # Add horizontal bar chart
    fig.add_trace(
        go.Bar(
            y=sorted_data[reason_col],
            x=sorted_data[count_col],
            orientation='h',
            marker_color="#C0392B",
            text=sorted_data[percentage_col].apply(lambda x: f"{x:.1f}%"),
            textposition="outside",
            name="Count"
        )
    )
    
    # Set x-axis title
    fig.update_xaxes(title_text="Number of Rejections")
    
    # Set y-axis title
    fig.update_yaxes(title_text="Rejection Reason")
    
    fig.update_layout(
        title_text="Top Rejection Reasons",
        hovermode="closest",
        margin=dict(l=200, r=20, t=50, b=50)  # Increase left margin for longer text
    )
    
    return fig

def plot_correlation_heatmap(data, factor_col='factor', correlation_col='correlation_with_approval'):
    """
    Create a heatmap of correlations between factors and approval
    
    Parameters:
    data (pd.DataFrame): Dataframe with factors and their correlation with approval
    factor_col (str): Column name for factors
    correlation_col (str): Column name for correlation values
    
    Returns:
    fig: Plotly figure object
    """
    if data.empty:
        return go.Figure().update_layout(
            title="No correlation data available",
            xaxis_title="Factor",
            yaxis_title="Correlation"
        )
    
    # Sort data by absolute correlation value
    sorted_data = data.sort_values(by=correlation_col, key=abs, ascending=False)
    
    # Create a custom colorscale with negative values as red, positive as green
    colorscale = [
        [0, 'rgb(178, 34, 34)'],   # Strong negative correlation (dark red)
        [0.45, 'rgb(246, 178, 107)'],  # Weak negative correlation (light red)
        [0.5, 'rgb(255, 255, 255)'],  # No correlation (white)
        [0.55, 'rgb(162, 229, 184)'],  # Weak positive correlation (light green)
        [1, 'rgb(35, 139, 69)']    # Strong positive correlation (dark green)
    ]
    
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(
        go.Bar(
            x=sorted_data[factor_col],
            y=sorted_data[correlation_col],
            marker_color=sorted_data[correlation_col],
            marker_colorscale=colorscale,
            marker_colorbar=dict(title="Correlation"),
            text=sorted_data[correlation_col].apply(lambda x: f"{x:.3f}"),
            textposition="outside"
        )
    )
    
    # Add horizontal line at zero
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(sorted_data) - 0.5,
        y0=0,
        y1=0,
        line=dict(color="black", width=1, dash="dash")
    )
    
    # Set axis titles
    fig.update_xaxes(title_text="Factor")
    fig.update_yaxes(
        title_text="Correlation with Approval",
        range=[min(-1, sorted_data[correlation_col].min() * 1.2), 
               max(1, sorted_data[correlation_col].max() * 1.2)]
    )
    
    fig.update_layout(
        title_text="Correlation of Factors with Loan Approval",
        hovermode="closest"
    )
    
    return fig

def plot_loan_amount_comparison(data, status_col='status', 
                               mean_col='mean', median_col='median'):
    """
    Create a bar chart comparing loan amounts by approval status
    
    Parameters:
    data (pd.DataFrame): Dataframe with loan amount statistics by status
    status_col (str): Column name for status
    mean_col (str): Column name for mean loan amount
    median_col (str): Column name for median loan amount
    
    Returns:
    fig: Plotly figure object
    """
    if data.empty:
        return go.Figure().update_layout(
            title="No loan amount data available",
            xaxis_title="Status",
            yaxis_title="Loan Amount"
        )
    
    fig = go.Figure()
    
    # Add mean loan amount bars
    fig.add_trace(
        go.Bar(
            x=data[status_col],
            y=data[mean_col].round(0),
            name="Mean Loan Amount",
            marker_color="#3498DB"
        )
    )
    
    # Add median loan amount bars
    fig.add_trace(
        go.Bar(
            x=data[status_col],
            y=data[median_col].round(0),
            name="Median Loan Amount",
            marker_color="#85C1E9"
        )
    )
    
    # Set axis titles
    fig.update_xaxes(title_text="Application Status")
    fig.update_yaxes(title_text="Loan Amount")
    
    fig.update_layout(
        title_text="Loan Amount Comparison by Status",
        hovermode="closest",
        barmode="group"
    )
    
    return fig

def plot_approval_rate_by_factor(data, factor_col, rate_col='approval_rate', count_col='total_applications'):
    """
    Create a dual-axis plot of approval rate and application count by a factor
    
    Parameters:
    data (pd.DataFrame): Dataframe with factor, approval rate and application count
    factor_col (str): Column name for the factor
    rate_col (str): Column name for approval rate
    count_col (str): Column name for application count
    
    Returns:
    fig: Plotly figure object
    """
    if data.empty:
        return go.Figure().update_layout(
            title=f"No data available for approval rate by {factor_col}",
            xaxis_title=factor_col,
            yaxis_title="Rate / Count"
        )
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add approval rate line
    fig.add_trace(
        go.Scatter(
            x=data[factor_col],
            y=data[rate_col].round(3),
            name="Approval Rate",
            line=dict(color="#2E86C1", width=3),
            mode="lines+markers",
            yaxis="y"
        )
    )
    
    # Add application volume bars
    fig.add_trace(
        go.Bar(
            x=data[factor_col],
            y=data[count_col],
            name="Application Volume",
            marker_color="#AED6F1",
            opacity=0.7,
            yaxis="y2"
        )
    )
    
    # Set x-axis title
    fig.update_xaxes(title_text=factor_col)
    
    # Update layout for dual y-axes
    fig.update_layout(
        title_text=f"Approval Rate by {factor_col}",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(
            title="Approval Rate",
            range=[0, max(1.0, data[rate_col].max() * 1.1)],
            tickformat=".0%"
        ),
        yaxis2=dict(
            title="Number of Applications",
            overlaying="y",
            side="right"
        )
    )
    
    return fig
