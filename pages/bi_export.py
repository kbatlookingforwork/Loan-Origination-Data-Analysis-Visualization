import streamlit as st
from bi_integration import render_bi_export_ui

# Set page configuration
st.set_page_config(
    page_title="BI Tool Integration",
    page_icon="📊",
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
st.title("Business Intelligence Tool Integration")
st.markdown("Export your loan origination data and connect with popular BI tools like Tableau and Power BI.")

# Call the BI export UI renderer
render_bi_export_ui(data)
