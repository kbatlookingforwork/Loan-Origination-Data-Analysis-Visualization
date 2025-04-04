import pandas as pd
import streamlit as st
import base64
import io
from datetime import datetime

def generate_tableau_data_extract(df, filename=None):
    """
    Generate a Tableau Data Extract (TDE) from a pandas DataFrame.
    Since we can't directly create TDE files without TableauSDK, 
    we'll export as CSV which can be imported into Tableau.
    
    Parameters:
    df (pd.DataFrame): Dataframe to convert
    filename (str): Base filename without extension
    
    Returns:
    bytes: CSV file as bytes that can be imported into Tableau
    """
    if filename is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tableau_export_{now}"
    
    # Convert DataFrame to CSV (Tableau can import this)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    return csv_buffer.getvalue()

def generate_power_bi_template(df, filename=None):
    """
    Generate a Power BI template with the data schema.
    Since we can't directly create PBIT files, we'll export as Excel
    which can be imported into Power BI.
    
    Parameters:
    df (pd.DataFrame): Dataframe to use for schema
    filename (str): Base filename without extension
    
    Returns:
    bytes: Excel file as bytes that can be imported into Power BI
    """
    if filename is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"powerbi_export_{now}"
    
    # Convert DataFrame to Excel (Power BI can import this)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Loan Data', index=False)
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Loan Data']
        
        # Add a header format
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Write the column headers with the defined format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Set column widths
        for i, col in enumerate(df.columns):
            max_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_width)
    
    return output.getvalue()

def generate_bi_connection_instructions():
    """
    Returns instructions for connecting to various BI tools
    """
    instructions = {
        "tableau": """
        # Connecting to Tableau
        
        To connect your loan origination data analysis to Tableau:
        
        1. **Export data from this application**:
           - Use the "Export for Tableau" button below to download your data as a CSV file.
           
        2. **Import into Tableau**:
           - Open Tableau Desktop
           - Select "Connect to a file" → "Text file"
           - Browse and select the exported CSV file
           - Tableau will automatically detect the schema
           
        3. **Create Visualizations**:
           - Use the same metrics and dimensions as shown in this application
           - For example, create dashboards for approval rates, processing times, and rejection factors
           
        4. **Set up Automatic Refresh** (optional):
           - If you want to keep your Tableau dashboard updated with the latest data:
           - Schedule regular exports from this application
           - Use Tableau's data refresh capabilities to update automatically
        """,
        
        "powerbi": """
        # Connecting to Power BI
        
        To connect your loan origination data to Power BI:
        
        1. **Export data from this application**:
           - Use the "Export for Power BI" button below to download your data as an Excel file.
           
        2. **Import into Power BI**:
           - Open Power BI Desktop
           - Click "Get Data" → "Excel"
           - Browse and select the exported Excel file
           - Select the "Loan Data" table and click "Load"
           
        3. **Create Reports**:
           - Build similar visualizations as shown in this application
           - Create measures for approval rates, average processing times, etc.
           - Build dashboards with cards, charts, and tables
           
        4. **Schedule Refresh** (optional):
           - If publishing to Power BI Service and want automatic updates:
           - Schedule regular exports from this application
           - Set up scheduled refresh in Power BI Service
        """
    }
    
    return instructions

def render_bi_export_ui(data):
    """
    Render UI for exporting data to BI tools
    
    Parameters:
    data (pd.DataFrame): The dataframe to export
    """
    if data is None or data.empty:
        st.warning("No data available for export. Please process data first.")
        return
    
    st.subheader("Business Intelligence Integration")
    
    tab1, tab2 = st.tabs(["Tableau Integration", "Power BI Integration"])
    
    with tab1:
        st.markdown(generate_bi_connection_instructions()["tableau"])
        
        if st.button("Export for Tableau"):
            csv_data = generate_tableau_data_extract(data)
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tableau_loan_data_{now}.csv"
            
            st.download_button(
                label="Download CSV for Tableau",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
    
    with tab2:
        st.markdown(generate_bi_connection_instructions()["powerbi"])
        
        if st.button("Export for Power BI"):
            excel_data = generate_power_bi_template(data)
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"powerbi_loan_data_{now}.xlsx"
            
            st.download_button(
                label="Download Excel for Power BI",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    st.divider()
    st.subheader("Custom Queries")
    st.markdown("""
    If you need to create custom queries or data transformations for your BI tool:
    
    1. Use the "Raw Data" sections available in each analysis page
    2. Export the filtered data as needed
    3. Write your custom SQL or DAX expressions in your BI tool
    
    For complex integrations or real-time connections, please contact your IT department.
    """)
