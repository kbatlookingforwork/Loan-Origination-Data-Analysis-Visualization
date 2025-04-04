import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sample_loan_data(num_records=500, start_date=None, end_date=None):
    """
    Generate sample loan origination data for demonstration purposes.
    
    Parameters:
    num_records (int): Number of loan records to generate
    start_date (datetime): Start date for the loan applications (default: 1 year ago)
    end_date (datetime): End date for the loan applications (default: today)
    
    Returns:
    pd.DataFrame: DataFrame containing sample loan origination data
    """
    # Set default date range if not provided
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=365)
    
    # Date range in days
    date_range = (end_date - start_date).days
    
    # Generate random application IDs
    application_ids = [f"LOAN-{i:06d}" for i in range(1, num_records + 1)]
    
    # Generate random application dates
    application_dates = [start_date + timedelta(days=random.randint(0, date_range)) 
                         for _ in range(num_records)]
    application_dates.sort()  # Sort chronologically
    
    # Loan amounts (normally distributed around mean of 25000)
    loan_amounts = np.random.normal(25000, 10000, num_records)
    loan_amounts = np.maximum(5000, loan_amounts)  # Minimum loan of 5000
    loan_amounts = np.minimum(100000, loan_amounts)  # Maximum loan of 100000
    loan_amounts = np.round(loan_amounts, -2)  # Round to nearest 100
    
    # Credit scores (normally distributed)
    credit_scores = np.random.normal(680, 75, num_records)
    credit_scores = np.clip(credit_scores, 300, 850)
    credit_scores = np.round(credit_scores)
    
    # Income values (lognormal distribution)
    incomes = np.random.lognormal(mean=11, sigma=0.5, size=num_records)
    incomes = np.round(incomes, -2)  # Round to nearest 100
    
    # Process different loan purposes
    loan_purposes = np.random.choice(
        ["Home Improvement", "Debt Consolidation", "Business", "Education", 
         "Auto Purchase", "Medical Expenses", "Vacation", "Other"],
        num_records,
        p=[0.25, 0.3, 0.1, 0.05, 0.15, 0.05, 0.05, 0.05]
    )
    
    # Determine loan approval probability based on credit score and income
    def get_approval_probability(credit_score, income, loan_amount):
        # Base probability
        prob = 0.5
        
        # Adjust based on credit score
        if credit_score >= 750:
            prob += 0.3
        elif credit_score >= 700:
            prob += 0.2
        elif credit_score >= 650:
            prob += 0.1
        elif credit_score < 600:
            prob -= 0.2
        elif credit_score < 550:
            prob -= 0.3
            
        # Adjust based on income-to-loan ratio
        if income > loan_amount * 0.5:
            prob += 0.15
        elif income < loan_amount * 0.25:
            prob -= 0.15
            
        # Ensure probability is between 0.1 and 0.9
        return max(0.1, min(0.9, prob))
    
    # Determine loan status and decision dates
    statuses = []
    decision_dates = []
    rejection_reasons = []
    
    for i in range(num_records):
        app_date = application_dates[i]
        credit_score = credit_scores[i]
        income = incomes[i]
        loan_amount = loan_amounts[i]
        
        # Calculate processing time (normally distributed)
        if credit_score > 750:  # Better credit scores get processed faster
            process_days = max(1, np.random.normal(5, 2))
        elif credit_score > 650:
            process_days = max(1, np.random.normal(10, 4))
        else:
            process_days = max(1, np.random.normal(15, 7))
            
        # Add some outliers with very long processing times
        if random.random() < 0.05:  # 5% chance of outlier
            process_days *= random.uniform(2, 4)
            
        # Ensure decision date doesn't exceed current date
        decision_date = min(app_date + timedelta(days=int(process_days)), end_date)
        
        # For very recent applications, some might still be pending
        if (end_date - app_date).days < 7 and random.random() < 0.3:
            status = "Pending"
            decision_date = None
            rejection_reason = None
        else:
            # Determine approval based on probability
            prob = get_approval_probability(credit_score, income, loan_amount)
            if random.random() < prob:
                status = "Approved"
                rejection_reason = None
            else:
                status = "Rejected"
                
                # Determine rejection reason
                if credit_score < 600:
                    rejection_reason = "Low Credit Score"
                elif income < loan_amount * 0.25:
                    rejection_reason = "Insufficient Income"
                elif loan_amount > 50000 and random.random() < 0.3:
                    rejection_reason = "Loan Amount Too High"
                elif random.random() < 0.2:
                    rejection_reason = "Incomplete Documentation"
                elif random.random() < 0.15:
                    rejection_reason = "High Existing Debt"
                elif random.random() < 0.1:
                    rejection_reason = "Unstable Employment History"
                else:
                    rejection_reason = "Other"
        
        statuses.append(status)
        decision_dates.append(decision_date)
        rejection_reasons.append(rejection_reason)
    
    # Create DataFrame
    data = {
        "application_id": application_ids,
        "application_date": application_dates,
        "decision_date": decision_dates,
        "status": statuses,
        "loan_amount": loan_amounts,
        "credit_score": credit_scores,
        "annual_income": incomes,
        "loan_purpose": loan_purposes,
        "rejection_reason": rejection_reasons
    }
    
    df = pd.DataFrame(data)
    
    # Add a few more categorical features to make the dataset more interesting
    df["employment_type"] = np.random.choice(
        ["Full-time", "Part-time", "Self-employed", "Retired", "Unemployed"],
        num_records,
        p=[0.65, 0.15, 0.1, 0.05, 0.05]
    )
    
    df["home_ownership"] = np.random.choice(
        ["Own", "Mortgage", "Rent", "Other"],
        num_records,
        p=[0.3, 0.4, 0.25, 0.05]
    )
    
    return df

def get_sample_data():
    """
    Returns a ready-to-use sample dataset for the loan origination analysis
    """
    # Generate sample data
    sample_data = generate_sample_loan_data(1000)
    
    # Add feature to identify this as sample data
    sample_data['is_sample_data'] = True
    
    return sample_data
