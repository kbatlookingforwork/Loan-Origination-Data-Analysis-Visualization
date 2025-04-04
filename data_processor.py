import pandas as pd
import numpy as np
from datetime import datetime
import re

class DataProcessor:
    """
    Class to process and analyze loan origination data
    """
    
    def __init__(self, data):
        """
        Initialize with the dataframe
        
        Parameters:
        data (pd.DataFrame): The loan data dataframe
        """
        self.raw_data = data.copy()
        self.data = None
        self.column_mapping = {}
        self.approval_terms = ['approved', 'accept', 'funded', 'complete']
        self.rejection_terms = ['rejected', 'denied', 'declined', 'refuse']
        
    def suggest_column(self, possible_names):
        """
        Suggests a column from the dataframe that might match one of the possible names
        
        Parameters:
        possible_names (list): List of possible column name patterns
        
        Returns:
        int: Index of the suggested column in the dataframe columns list, or 0 if no match
        """
        columns = list(self.raw_data.columns)
        
        # Try exact match first
        for name in possible_names:
            if name in columns:
                return columns.index(name) + 1  # +1 because we'll add an empty string at index 0
        
        # Try case-insensitive match
        for name in possible_names:
            for col in columns:
                if name.lower() == col.lower():
                    return columns.index(col) + 1
        
        # Try partial match
        for name in possible_names:
            for col in columns:
                if name.lower() in col.lower() or col.lower() in name.lower():
                    return columns.index(col) + 1
                
        return 0  # No match found
    
    def set_column_mapping(self, mapping):
        """
        Set the mapping between standard column names and actual dataframe columns
        
        Parameters:
        mapping (dict): Dictionary mapping standard names to actual column names
        """
        self.column_mapping = mapping
    
    def _parse_date(self, date_str):
        """
        Attempt to parse a date string into a datetime object
        
        Parameters:
        date_str: The date string to parse
        
        Returns:
        datetime object or None if parsing fails
        """
        if pd.isna(date_str):
            return None
            
        # If already a datetime
        if isinstance(date_str, (datetime, pd.Timestamp)):
            return date_str
            
        # Common date formats to try
        formats = [
            '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y',
            '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M:%S', '%m-%d-%Y %H:%M:%S',
            '%Y/%m/%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S',
            '%b %d %Y', '%d %b %Y', '%B %d %Y', '%d %B %Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
                
        # If all formats fail, try pandas to_datetime
        try:
            return pd.to_datetime(date_str)
        except:
            return None
    
    def _standardize_status(self, status):
        """
        Standardize loan status values
        
        Parameters:
        status: The status value to standardize
        
        Returns:
        str: 'approved', 'rejected', or 'pending'
        """
        if pd.isna(status):
            return 'unknown'
            
        status_lower = str(status).lower()
        
        # Check for approval terms
        for term in self.approval_terms:
            if term in status_lower:
                return 'approved'
                
        # Check for rejection terms
        for term in self.rejection_terms:
            if term in status_lower:
                return 'rejected'
                
        # If it's neither clearly approved nor rejected
        return 'other'
    
    def preprocess_data(self):
        """
        Preprocess the data using the column mapping
        - Convert dates
        - Standardize status
        - Calculate processing time
        - Clean and prepare data for analysis
        
        Returns:
        pd.DataFrame: The processed dataframe
        """
        # Create a copy of the raw data
        df = self.raw_data.copy()
        
        # Extract mapped columns (using original names from mapping)
        mapped_columns = {std_name: col_name for std_name, col_name in self.column_mapping.items() if col_name}
        
        # Create a new dataframe with standardized column names
        processed_df = pd.DataFrame()
        
        # Copy mapped columns to the new dataframe with standard names
        for std_name, orig_name in mapped_columns.items():
            processed_df[std_name] = df[orig_name]
        
        # Convert date columns
        date_columns = ['application_date', 'decision_date']
        for col in date_columns:
            if col in processed_df.columns:
                processed_df[col] = processed_df[col].apply(self._parse_date)
        
        # Standardize status
        if 'status' in processed_df.columns:
            processed_df['status_standardized'] = processed_df['status'].apply(self._standardize_status)
        
        # Calculate processing time in days
        if all(col in processed_df.columns for col in date_columns):
            processed_df['processing_time_days'] = (
                processed_df['decision_date'] - processed_df['application_date']
            ).dt.total_seconds() / (24 * 60 * 60)
            
            # Handle negative or extremely large values
            processed_df.loc[processed_df['processing_time_days'] < 0, 'processing_time_days'] = np.nan
            processed_df.loc[processed_df['processing_time_days'] > 365, 'processing_time_days'] = np.nan
        
        # Extract month and year for trend analysis
        if 'application_date' in processed_df.columns:
            processed_df['application_month'] = processed_df['application_date'].dt.month
            processed_df['application_year'] = processed_df['application_date'].dt.year
            processed_df['application_yearmonth'] = processed_df['application_date'].dt.strftime('%Y-%m')
        
        # Store the processed data
        self.data = processed_df
        return processed_df
    
    def get_approval_rate(self, group_by=None, time_period=None):
        """
        Calculate approval rate, optionally grouped by a column
        
        Parameters:
        group_by (str): Column to group by
        time_period (str): Time period for grouping ('monthly', 'quarterly', 'yearly')
        
        Returns:
        pd.DataFrame: Dataframe with approval rates
        """
        if self.data is None:
            raise ValueError("Data has not been processed yet. Call preprocess_data() first.")
        
        df = self.data.copy()
        
        # Define grouping
        if time_period == 'monthly' and 'application_yearmonth' in df.columns:
            grouper = 'application_yearmonth'
        elif time_period == 'quarterly' and 'application_date' in df.columns:
            df['quarter'] = df['application_date'].dt.to_period('Q').astype(str)
            grouper = 'quarter'
        elif time_period == 'yearly' and 'application_year' in df.columns:
            grouper = 'application_year'
        elif group_by is not None and group_by in df.columns:
            grouper = group_by
        else:
            # Overall approval rate
            total = len(df)
            approved = len(df[df['status_standardized'] == 'approved'])
            return pd.DataFrame({
                'total_applications': [total],
                'approved': [approved],
                'approval_rate': [approved / total if total > 0 else 0]
            })
        
        # Group by the selected column
        grouped = df.groupby(grouper)
        
        result = pd.DataFrame({
            'total_applications': grouped.size(),
            'approved': grouped['status_standardized'].apply(lambda x: (x == 'approved').sum()),
        })
        
        result['approval_rate'] = result['approved'] / result['total_applications']
        return result.reset_index()
    
    def get_processing_time_stats(self, group_by=None):
        """
        Calculate processing time statistics
        
        Parameters:
        group_by (str): Column to group by
        
        Returns:
        pd.DataFrame: Dataframe with processing time statistics
        """
        if self.data is None:
            raise ValueError("Data has not been processed yet. Call preprocess_data() first.")
        
        if 'processing_time_days' not in self.data.columns:
            raise ValueError("Processing time not calculated. Check date columns mapping.")
        
        df = self.data.copy()
        
        # Filter out rows with missing processing time
        df = df.dropna(subset=['processing_time_days'])
        
        if group_by is not None and group_by in df.columns:
            grouped = df.groupby(group_by)
            
            result = pd.DataFrame({
                'count': grouped['processing_time_days'].count(),
                'mean_days': grouped['processing_time_days'].mean(),
                'median_days': grouped['processing_time_days'].median(),
                'min_days': grouped['processing_time_days'].min(),
                'max_days': grouped['processing_time_days'].max(),
                'std_days': grouped['processing_time_days'].std()
            })
            
            return result.reset_index()
        else:
            # Overall statistics
            stats = {
                'count': df['processing_time_days'].count(),
                'mean_days': df['processing_time_days'].mean(),
                'median_days': df['processing_time_days'].median(),
                'min_days': df['processing_time_days'].min(),
                'max_days': df['processing_time_days'].max(),
                'std_days': df['processing_time_days'].std()
            }
            
            return pd.DataFrame([stats])
    
    def get_rejection_factors(self, n_top=10):
        """
        Analyze rejection factors
        
        Parameters:
        n_top (int): Number of top rejection reasons to return
        
        Returns:
        pd.DataFrame: Dataframe with rejection reasons and counts
        """
        if self.data is None:
            raise ValueError("Data has not been processed yet. Call preprocess_data() first.")
        
        df = self.data.copy()
        
        # Filter to only rejected applications
        rejected = df[df['status_standardized'] == 'rejected']
        
        if 'rejection_reason' in rejected.columns:
            # Handle null values
            rejected = rejected.dropna(subset=['rejection_reason'])
            
            # Count rejection reasons
            rejection_counts = rejected['rejection_reason'].value_counts().reset_index()
            rejection_counts.columns = ['reason', 'count']
            
            # Calculate percentage
            total_rejections = rejection_counts['count'].sum()
            rejection_counts['percentage'] = (rejection_counts['count'] / total_rejections * 100).round(2)
            
            return rejection_counts.head(n_top)
        else:
            return pd.DataFrame(columns=['reason', 'count', 'percentage'])
    
    def get_correlation_factors(self):
        """
        Calculate correlation between various factors and approval status
        
        Returns:
        pd.DataFrame: Dataframe with correlation coefficients
        """
        if self.data is None:
            raise ValueError("Data has not been processed yet. Call preprocess_data() first.")
        
        df = self.data.copy()
        
        # Create binary approval column (1 for approved, 0 for others)
        df['is_approved'] = (df['status_standardized'] == 'approved').astype(int)
        
        # List of potential numeric factors
        potential_factors = ['loan_amount', 'income', 'credit_score', 'processing_time_days']
        
        # Filter to only include factors that exist and are numeric
        factors = [col for col in potential_factors if col in df.columns 
                  and pd.api.types.is_numeric_dtype(df[col])]
        
        if not factors:
            return pd.DataFrame(columns=['factor', 'correlation_with_approval'])
        
        # Calculate correlation for each factor
        correlations = []
        for factor in factors:
            # Drop NaN values for this specific correlation
            temp_df = df.dropna(subset=[factor, 'is_approved'])
            if len(temp_df) > 0:
                corr = temp_df[factor].corr(temp_df['is_approved'])
                correlations.append({'factor': factor, 'correlation_with_approval': corr})
        
        return pd.DataFrame(correlations)
    
    def get_loan_amount_analysis(self):
        """
        Analyze loan amount statistics by approval status
        
        Returns:
        pd.DataFrame: Dataframe with loan amount statistics by status
        """
        if self.data is None:
            raise ValueError("Data has not been processed yet. Call preprocess_data() first.")
        
        if 'loan_amount' not in self.data.columns:
            return pd.DataFrame(columns=['status', 'count', 'mean', 'median', 'min', 'max'])
        
        df = self.data.copy()
        
        # Group by standardized status
        result = df.groupby('status_standardized')['loan_amount'].agg([
            'count', 'mean', 'median', 'min', 'max'
        ]).reset_index()
        
        result.rename(columns={'status_standardized': 'status'}, inplace=True)
        return result
