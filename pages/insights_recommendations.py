import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Import custom modules
from utils import create_date_filters, filter_dataframe, display_metric_card, download_dataframe, download_excel
from statistics import (
    calculate_summary_metrics, 
    detect_trends, 
    identify_bottlenecks, 
    generate_insights,
    generate_recommendations
)

# Set page configuration
st.set_page_config(
    page_title="Insights & Recommendations",
    page_icon="💡",
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
st.title("Loan Origination Insights & Recommendations")
st.markdown("Generate actionable insights and recommendations based on loan origination data analysis.")

# Sidebar for filters
st.sidebar.header("Filters")

# Date range filter
start_date, end_date = create_date_filters(data, 'application_date', st.sidebar)

# Apply filters
filters = {}
if start_date and end_date:
    filters['application_date'] = (pd.Timestamp(start_date), pd.Timestamp(end_date) + timedelta(days=1) - timedelta(microseconds=1))

filtered_data = filter_dataframe(data, filters)

# Display warning if filtered data is empty
if filtered_data.empty:
    st.warning("No data available with the selected filters. Please adjust your filters.")
    st.stop()

# Calculate summary metrics
summary_metrics = calculate_summary_metrics(filtered_data)

# Calculate trend information
if 'application_yearmonth' in filtered_data.columns:
    # Generate monthly approval rate data
    approval_trend_data = processor.get_approval_rate(time_period='monthly')
    approval_trend_info = detect_trends(approval_trend_data, 'approval_rate')
    
    # Generate monthly processing time data
    if 'processing_time_days' in filtered_data.columns:
        # Group by month
        processing_data = filtered_data.dropna(subset=['processing_time_days'])
        grouped = processing_data.groupby('application_yearmonth')
        
        processing_time_trend = pd.DataFrame({
            'mean_days': grouped['processing_time_days'].mean(),
            'median_days': grouped['processing_time_days'].median()
        }).reset_index()
        
        processing_time_trend_info = detect_trends(processing_time_trend, 'mean_days')
    else:
        processing_time_trend_info = {'trend': 'insufficient data'}
else:
    approval_trend_info = {'trend': 'insufficient data'}
    processing_time_trend_info = {'trend': 'insufficient data'}

# Identify bottlenecks
bottlenecks = identify_bottlenecks(filtered_data)

# Generate insights and recommendations
insights = generate_insights(
    filtered_data,
    approval_trend=approval_trend_info,
    processing_time_trend=processing_time_trend_info,
    bottlenecks=bottlenecks
)

recommendations = generate_recommendations(insights)

# Display summary metrics
st.header("Summary Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    display_metric_card("Total Applications", summary_metrics['total_applications'])

with col2:
    display_metric_card("Approval Rate", summary_metrics['overall_approval_rate'])

with col3:
    display_metric_card("Avg. Processing Time", f"{summary_metrics['avg_processing_time']:.1f} days")

with col4:
    display_metric_card("Median Processing Time", f"{summary_metrics['median_processing_time']:.1f} days")

# Display key trends
st.header("Key Trends")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Approval Rate Trend")
    
    if approval_trend_info['trend'] != 'insufficient data':
        trend_emoji = "🔼" if approval_trend_info['trend'] == 'increasing' else "🔽" if approval_trend_info['trend'] == 'decreasing' else "➡️"
        confidence = approval_trend_info['confidence']
        
        st.markdown(f"""
        {trend_emoji} **{approval_trend_info['trend'].title()}** with {confidence} confidence
        """)
        
        if approval_trend_info['recent_change'] is not None:
            recent_change = approval_trend_info['recent_change'] * 100
            if abs(recent_change) > 1:
                direction = "increased" if recent_change > 0 else "decreased"
                st.markdown(f"Recent change: {direction} by {abs(recent_change):.1f}%")
    else:
        st.markdown("❓ Insufficient data for trend analysis")

with col2:
    st.subheader("Processing Time Trend")
    
    if processing_time_trend_info['trend'] != 'insufficient data':
        trend_emoji = "🔼" if processing_time_trend_info['trend'] == 'increasing' else "🔽" if processing_time_trend_info['trend'] == 'decreasing' else "➡️"
        confidence = processing_time_trend_info['confidence']
        
        st.markdown(f"""
        {trend_emoji} **{processing_time_trend_info['trend'].title()}** with {confidence} confidence
        """)
        
        if processing_time_trend_info['recent_change'] is not None:
            recent_change = processing_time_trend_info['recent_change'] * 100
            if abs(recent_change) > 1:
                direction = "increased" if recent_change > 0 else "decreased"
                st.markdown(f"Recent change: {direction} by {abs(recent_change):.1f}%")
    else:
        st.markdown("❓ Insufficient data for trend analysis")

# Display bottlenecks
if bottlenecks:
    st.header("Process Bottlenecks")
    
    for bottleneck in bottlenecks:
        severity = bottleneck.get('severity', 'medium')
        emoji = "🔴" if severity == 'high' else "🟠" if severity == 'medium' else "🟡"
        
        st.markdown(f"{emoji} **{bottleneck['description']}**")
else:
    st.header("Process Bottlenecks")
    st.markdown("✅ No significant bottlenecks identified in the current data")

# Display key insights
st.header("Key Insights")

if insights:
    for i, insight in enumerate(insights):
        category = insight.get('category', '')
        description = insight.get('description', '')
        
        emoji = "📊" if category == 'approval_rate' else \
              "⏱️" if category == 'processing_time' else \
              "❗" if category == 'bottleneck' else \
              "🔍" if category == 'correlation' else "💡"
        
        st.markdown(f"{emoji} **Insight {i+1}:** {description}")
else:
    st.markdown("No significant insights identified from the current data.")

# Display recommendations
st.header("Recommendations")

if recommendations:
    high_priority = [r for r in recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
    low_priority = [r for r in recommendations if r.get('priority') == 'low']
    
    if high_priority:
        st.subheader("High Priority")
        for i, rec in enumerate(high_priority):
            st.markdown(f"🔴 **{rec['description']}**")
    
    if medium_priority:
        st.subheader("Medium Priority")
        for i, rec in enumerate(medium_priority):
            st.markdown(f"🟠 **{rec['description']}**")
    
    if low_priority:
        st.subheader("Low Priority")
        for i, rec in enumerate(low_priority):
            st.markdown(f"🟡 **{rec['description']}**")
else:
    st.markdown("No recommendations available based on the current data.")

# Export section
st.header("Export Analysis")

export_format = st.radio(
    "Select export format",
    ("Excel", "CSV", "PDF"),
    horizontal=True
)

# Prepare export data
export_data = {
    "Summary Metrics": pd.DataFrame([summary_metrics]),
    "Insights": pd.DataFrame(insights) if insights else pd.DataFrame(),
    "Recommendations": pd.DataFrame(recommendations) if recommendations else pd.DataFrame(),
    "Processed Data": filtered_data
}

if st.button("Generate Export"):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"loan_analysis_{now}"
    
    if export_format == "Excel":
        excel_bytes = io.BytesIO()
        
        with pd.ExcelWriter(excel_bytes, engine='xlsxwriter') as writer:
            # Write each dataframe to a different worksheet
            for sheet_name, df in export_data.items():
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Adjust column width
                    worksheet = writer.sheets[sheet_name]
                    for i, col in enumerate(df.columns):
                        max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, max_len)
        
        excel_bytes.seek(0)
        
        st.download_button(
            label="Download Excel",
            data=excel_bytes,
            file_name=f"{filename}.xlsx",
            mime="application/vnd.ms-excel"
        )
    
    elif export_format == "CSV":
        # For CSV, we'll create a zip of multiple CSVs
        import zipfile
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            for sheet_name, df in export_data.items():
                if not df.empty:
                    csv_data = df.to_csv(index=False)
                    zip_file.writestr(f"{sheet_name.lower().replace(' ', '_')}.csv", csv_data)
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="Download CSV Files",
            data=zip_buffer,
            file_name=f"{filename}.zip",
            mime="application/zip"
        )
    
    elif export_format == "PDF":
        # Create PDF buffer
        pdf_buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, 
                               rightMargin=72, leftMargin=72, 
                               topMargin=72, bottomMargin=18)
        
        # Container for elements to build PDF
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading1']
        subheading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Add title
        elements.append(Paragraph("Loan Origination Analysis Report", title_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add date range
        if start_date and end_date:
            date_range = f"Analysis Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        else:
            date_range = f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}"
        
        elements.append(Paragraph(date_range, normal_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add summary metrics
        elements.append(Paragraph("Summary Metrics", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        metrics_data = [
            ["Metric", "Value"],
            ["Total Applications", f"{summary_metrics['total_applications']:,}"],
            ["Approved Applications", f"{summary_metrics['approved_count']:,}"],
            ["Rejected Applications", f"{summary_metrics['rejected_count']:,}"],
            ["Overall Approval Rate", f"{summary_metrics['overall_approval_rate']:.1%}"],
            ["Average Processing Time", f"{summary_metrics['avg_processing_time']:.1f} days"],
            ["Median Processing Time", f"{summary_metrics['median_processing_time']:.1f} days"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add key trends
        elements.append(Paragraph("Key Trends", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        trend_data = [
            ["Metric", "Trend", "Confidence"],
            ["Approval Rate", 
             approval_trend_info['trend'].title() if approval_trend_info['trend'] != 'insufficient data' else "Insufficient Data",
             approval_trend_info['confidence'] if approval_trend_info['trend'] != 'insufficient data' else "N/A"],
            ["Processing Time", 
             processing_time_trend_info['trend'].title() if processing_time_trend_info['trend'] != 'insufficient data' else "Insufficient Data",
             processing_time_trend_info['confidence'] if processing_time_trend_info['trend'] != 'insufficient data' else "N/A"]
        ]
        
        trend_table = Table(trend_data, colWidths=[2*inch, 2*inch, 1.5*inch])
        trend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (2, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (2, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (2, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (2, 0), 12),
            ('BOTTOMPADDING', (0, 0), (2, 0), 12),
            ('BACKGROUND', (0, 1), (2, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(trend_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add insights
        elements.append(Paragraph("Key Insights", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        if insights:
            for i, insight in enumerate(insights):
                elements.append(Paragraph(f"{i+1}. {insight['description']}", normal_style))
                elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph("No significant insights identified from the current data.", normal_style))
        
        elements.append(Spacer(1, 0.25*inch))
        
        # Add recommendations
        elements.append(Paragraph("Recommendations", heading_style))
        elements.append(Spacer(1, 0.1*inch))
        
        if recommendations:
            # High priority
            high_priority = [r for r in recommendations if r.get('priority') == 'high']
            if high_priority:
                elements.append(Paragraph("High Priority", subheading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for i, rec in enumerate(high_priority):
                    elements.append(Paragraph(f"{i+1}. {rec['description']}", normal_style))
                    elements.append(Spacer(1, 0.05*inch))
                
                elements.append(Spacer(1, 0.1*inch))
            
            # Medium priority
            medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
            if medium_priority:
                elements.append(Paragraph("Medium Priority", subheading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for i, rec in enumerate(medium_priority):
                    elements.append(Paragraph(f"{i+1}. {rec['description']}", normal_style))
                    elements.append(Spacer(1, 0.05*inch))
        else:
            elements.append(Paragraph("No recommendations available based on the current data.", normal_style))
        
        # Build the PDF document
        doc.build(elements)
        
        # Get PDF data
        pdf_data = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        # Provide download button
        st.download_button(
            label="Download PDF",
            data=pdf_data,
            file_name=f"{filename}.pdf",
            mime="application/pdf"
        )
