import streamlit as st
import pandas as pd
import os
from data_processor import DataProcessor
from utils import format_time, get_unique_values, download_dataframe
from sample_data import get_sample_data
from bi_integration import render_bi_export_ui

# Set page configuration
st.set_page_config(
    page_title="Loan Origination Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application title and description
st.title("Loan Origination Data Analysis Platform")
st.markdown("""
This platform provides interactive visualizations for tracking loan application metrics:
- Approval rates over time
- Processing time analysis
- Rejection factors identification
- Insights and recommendations
""")

# Initialize session state for storing data and analysis results
if 'data' not in st.session_state:
    st.session_state.data = None
if 'processor' not in st.session_state:
    st.session_state.processor = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'using_sample_data' not in st.session_state:
    st.session_state.using_sample_data = False

# File upload section
st.header("Data Upload")
upload_tab, sample_tab = st.tabs(["Upload Your Data", "Use Sample Data"])

with upload_tab:
    uploaded_file = st.file_uploader("Upload loan origination data (CSV, Excel)", 
                                    type=['csv', 'xlsx', 'xls'])
    
    # Sample format information
    with st.expander("Expected data format"):
        st.markdown("""
        Your data should include these columns (column names can vary):
        - Application ID (unique identifier)
        - Application Date (when the loan application was submitted)
        - Decision Date (when the decision was made)
        - Status (approved, rejected, etc.)
        - Loan Amount (requested amount)
        - Applicant details (income, credit score, etc.)
        - Rejection Reason (if applicable)
        
        The platform will attempt to identify these fields automatically.
        """)

with sample_tab:
    st.markdown("""
    Don't have your own data yet? Use our sample loan origination dataset to explore the platform's capabilities.
    
    The sample dataset includes:
    - 1,000 loan applications
    - Realistic approval patterns
    - Processing time variations
    - Various rejection reasons
    - Applicant demographic information
    """)
    
    if st.button("Load Sample Data"):
        # Get sample data
        data = get_sample_data()
        
        # Store in session state
        st.session_state.data = data
        st.session_state.using_sample_data = True
        
        # Display data preview
        st.subheader("Sample Data Preview")
        st.dataframe(data.head())
        
        # Display basic statistics
        st.subheader("Data Summary")
        st.write(f"Total records: {len(data)}")
        st.write(f"Columns: {', '.join(data.columns)}")
        
        # Initialize data processor with predefined column mapping for sample data
        processor = DataProcessor(data)
        processor.set_column_mapping({
            'application_id': 'application_id',
            'application_date': 'application_date',
            'decision_date': 'decision_date',
            'status': 'status',
            'loan_amount': 'loan_amount',
            'income': 'annual_income',
            'credit_score': 'credit_score',
            'rejection_reason': 'rejection_reason'
        })
        
        # Process the data
        with st.spinner("Processing sample data..."):
            processor.preprocess_data()
            st.session_state.processor = processor
            st.session_state.analysis_complete = True
            st.success("Sample data loaded and processed successfully!")
            st.markdown("""
            ### Next Steps
            
            Use the sidebar to navigate to specific analysis pages:
            - Approval Rate Analysis
            - Processing Time Analysis
            - Rejection Factors Analysis
            - Insights & Recommendations
            """)
            st.rerun()

# Process uploaded data
if uploaded_file is not None and not st.session_state.using_sample_data:
    try:
        # Determine file type and read accordingly
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension == '.csv':
            data = pd.read_csv(uploaded_file)
        elif file_extension in ['.xlsx', '.xls']:
            data = pd.read_excel(uploaded_file)
        
        # Store in session state
        st.session_state.data = data
        st.session_state.using_sample_data = False
        
        # Display data preview
        st.subheader("Data Preview")
        st.dataframe(data.head())
        
        # Display basic statistics
        st.subheader("Data Summary")
        st.write(f"Total records: {len(data)}")
        st.write(f"Columns: {', '.join(data.columns)}")
        
        # Initialize data processor
        processor = DataProcessor(data)
        st.session_state.processor = processor
        
        # Column mapping interface
        st.subheader("Column Mapping")
        st.markdown("Please map your data columns to the required fields:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            app_id = st.selectbox("Application ID", 
                                [''] + list(data.columns),
                                index=processor.suggest_column(['application_id', 'loan_id', 'id', 'app_id']))
            
            app_date = st.selectbox("Application Date", 
                                   [''] + list(data.columns),
                                   index=processor.suggest_column(['application_date', 'app_date', 'date', 'submission_date']))
            
            decision_date = st.selectbox("Decision Date", 
                                        [''] + list(data.columns),
                                        index=processor.suggest_column(['decision_date', 'approval_date', 'completed_date']))
            
            status = st.selectbox("Application Status", 
                                 [''] + list(data.columns),
                                 index=processor.suggest_column(['status', 'decision', 'approval_status', 'result']))
            
        with col2:
            loan_amount = st.selectbox("Loan Amount", 
                                      [''] + list(data.columns),
                                      index=processor.suggest_column(['loan_amount', 'amount', 'requested_amount']))
            
            income = st.selectbox("Income", 
                                 [''] + list(data.columns),
                                 index=processor.suggest_column(['income', 'annual_income', 'yearly_income', 'monthly_income']))
            
            credit_score = st.selectbox("Credit Score", 
                                       [''] + list(data.columns),
                                       index=processor.suggest_column(['credit_score', 'fico', 'credit', 'score']))
            
            rejection_reason = st.selectbox("Rejection Reason", 
                                           [''] + list(data.columns),
                                           index=processor.suggest_column(['rejection_reason', 'decline_reason', 'reason', 'notes']))
        
        # Process data button
        if st.button("Process Data"):
            if not all([app_id, app_date, decision_date, status]):
                st.error("Please map at least Application ID, Application Date, Decision Date, and Status columns!")
            else:
                # Set column mapping in processor
                processor.set_column_mapping({
                    'application_id': app_id,
                    'application_date': app_date,
                    'decision_date': decision_date,
                    'status': status,
                    'loan_amount': loan_amount if loan_amount else None,
                    'income': income if income else None,
                    'credit_score': credit_score if credit_score else None,
                    'rejection_reason': rejection_reason if rejection_reason else None
                })
                
                # Process the data
                with st.spinner("Processing data..."):
                    processor.preprocess_data()
                    st.session_state.analysis_complete = True
                    st.success("Data processed successfully!")
                    st.markdown("""
                    ### Next Steps
                    
                    Use the sidebar to navigate to specific analysis pages:
                    - Approval Rate Analysis
                    - Processing Time Analysis
                    - Rejection Factors Analysis
                    - Insights & Recommendations
                    """)
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

# There is already navigation at the top of the page, so no need for sidebar navigation
        
# Sample data notice
if st.session_state.analysis_complete and st.session_state.using_sample_data:
    st.sidebar.markdown("---")
    st.sidebar.info("You are currently using sample data. Upload your own data for custom analysis.")
