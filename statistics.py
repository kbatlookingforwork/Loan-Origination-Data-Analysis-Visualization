import pandas as pd
import numpy as np
from scipy import stats

def calculate_summary_metrics(data):
    """
    Calculate summary metrics for the loan origination process
    
    Parameters:
    data (pd.DataFrame): Processed loan data
    
    Returns:
    dict: Dictionary of summary metrics
    """
    if data is None or data.empty:
        return {
            'total_applications': 0,
            'approved_count': 0,
            'rejected_count': 0,
            'overall_approval_rate': 0,
            'avg_processing_time': 0,
            'median_processing_time': 0
        }
    
    # Total applications
    total = len(data)
    
    # Approval counts
    if 'status_standardized' in data.columns:
        approved = data['status_standardized'].eq('approved').sum()
        rejected = data['status_standardized'].eq('rejected').sum()
        approval_rate = approved / total if total > 0 else 0
    else:
        approved = 0
        rejected = 0
        approval_rate = 0
    
    # Processing time
    if 'processing_time_days' in data.columns:
        processing_time = data['processing_time_days'].dropna()
        avg_time = processing_time.mean() if not processing_time.empty else 0
        median_time = processing_time.median() if not processing_time.empty else 0
    else:
        avg_time = 0
        median_time = 0
    
    return {
        'total_applications': total,
        'approved_count': approved,
        'rejected_count': rejected,
        'overall_approval_rate': approval_rate,
        'avg_processing_time': avg_time,
        'median_processing_time': median_time
    }

def detect_trends(time_series_data, value_col):
    """
    Detect trends in time series data using Mann-Kendall test
    
    Parameters:
    time_series_data (pd.DataFrame): Time series data with values
    value_col (str): Column name for values to analyze
    
    Returns:
    dict: Dictionary with trend information
    """
    if time_series_data is None or time_series_data.empty or value_col not in time_series_data.columns:
        return {
            'trend': 'insufficient data',
            'p_value': None,
            'confidence': None,
            'recent_change': None
        }
    
    values = time_series_data[value_col].dropna().values
    
    if len(values) < 3:
        return {
            'trend': 'insufficient data',
            'p_value': None,
            'confidence': None,
            'recent_change': None
        }
    
    # Calculate Mann-Kendall test
    try:
        trend, p_value, _ = stats.mannkendall(values)
        
        # Determine trend direction and confidence
        if p_value <= 0.05:
            confidence = 'high'
        elif p_value <= 0.1:
            confidence = 'moderate'
        else:
            confidence = 'low'
            
        # Get trend direction
        if trend > 0:
            trend_direction = 'increasing'
        elif trend < 0:
            trend_direction = 'decreasing'
        else:
            trend_direction = 'stable'
            
        # Calculate recent change (last 3 periods if available)
        if len(values) >= 3:
            recent_values = values[-3:]
            recent_change = (recent_values[-1] - recent_values[0]) / recent_values[0] if recent_values[0] != 0 else 0
        else:
            recent_change = None
            
        return {
            'trend': trend_direction,
            'p_value': p_value,
            'confidence': confidence,
            'recent_change': recent_change
        }
        
    except:
        # If test fails, return basic trend calculation
        if len(values) >= 2:
            slope = (values[-1] - values[0]) / (len(values) - 1)
            
            if slope > 0.01:
                trend_direction = 'increasing'
            elif slope < -0.01:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
                
            recent_change = (values[-1] - values[0]) / values[0] if values[0] != 0 else 0
                
            return {
                'trend': trend_direction,
                'p_value': None,
                'confidence': 'low',
                'recent_change': recent_change
            }
        else:
            return {
                'trend': 'insufficient data',
                'p_value': None,
                'confidence': None,
                'recent_change': None
            }

def identify_bottlenecks(data):
    """
    Identify bottlenecks in the loan origination process
    
    Parameters:
    data (pd.DataFrame): Processed loan data
    
    Returns:
    list: List of potential bottlenecks with descriptions
    """
    bottlenecks = []
    
    if data is None or data.empty:
        return bottlenecks
    
    # Check processing time outliers
    if 'processing_time_days' in data.columns:
        processing_time = data['processing_time_days'].dropna()
        
        if not processing_time.empty:
            q3 = processing_time.quantile(0.75)
            q1 = processing_time.quantile(0.25)
            iqr = q3 - q1
            upper_bound = q3 + (1.5 * iqr)
            
            outliers = processing_time[processing_time > upper_bound]
            outlier_percent = len(outliers) / len(processing_time) * 100
            
            if outlier_percent > 10:
                bottlenecks.append({
                    'type': 'processing_time',
                    'description': f"Significant processing time outliers detected ({outlier_percent:.1f}% of applications)",
                    'severity': 'high' if outlier_percent > 20 else 'medium'
                })
    
    # Check rejection reasons distribution
    if 'rejection_reason' in data.columns and 'status_standardized' in data.columns:
        rejected = data[data['status_standardized'] == 'rejected']
        
        if not rejected.empty and 'rejection_reason' in rejected.columns:
            rejection_reasons = rejected['rejection_reason'].dropna()
            
            if not rejection_reasons.empty:
                # Check if one reason dominates
                top_reason_pct = rejection_reasons.value_counts(normalize=True).iloc[0] * 100
                
                if top_reason_pct > 50:
                    top_reason = rejection_reasons.value_counts().index[0]
                    bottlenecks.append({
                        'type': 'rejection_reason',
                        'description': f"'{top_reason}' accounts for {top_reason_pct:.1f}% of rejections",
                        'severity': 'high' if top_reason_pct > 70 else 'medium'
                    })
    
    # Check monthly volume fluctuations
    if 'application_yearmonth' in data.columns:
        monthly_volume = data.groupby('application_yearmonth').size()
        
        if len(monthly_volume) > 2:
            monthly_changes = monthly_volume.pct_change().dropna().abs()
            significant_changes = monthly_changes[monthly_changes > 0.3]
            
            if not significant_changes.empty:
                bottlenecks.append({
                    'type': 'volume_fluctuation',
                    'description': f"Significant monthly volume fluctuations detected in {len(significant_changes)} months",
                    'severity': 'medium'
                })
    
    return bottlenecks

def generate_insights(data, approval_trend=None, processing_time_trend=None, bottlenecks=None):
    """
    Generate insights from the data analysis
    
    Parameters:
    data (pd.DataFrame): Processed loan data
    approval_trend (dict): Trend information for approval rates
    processing_time_trend (dict): Trend information for processing times
    bottlenecks (list): List of identified bottlenecks
    
    Returns:
    list: List of insights with descriptions
    """
    insights = []
    
    if data is None or data.empty:
        return insights
    
    # Add approval rate trend insights
    if approval_trend and approval_trend['trend'] != 'insufficient data':
        trend_direction = approval_trend['trend']
        confidence = approval_trend['confidence']
        
        insight = {
            'category': 'approval_rate',
            'description': f"Approval rate shows a {trend_direction} trend with {confidence} confidence"
        }
        
        if approval_trend['recent_change'] is not None:
            recent_change_pct = approval_trend['recent_change'] * 100
            if abs(recent_change_pct) > 5:
                insight['description'] += f" (recent change: {recent_change_pct:.1f}%)"
        
        insights.append(insight)
    
    # Add processing time trend insights
    if processing_time_trend and processing_time_trend['trend'] != 'insufficient data':
        trend_direction = processing_time_trend['trend']
        confidence = processing_time_trend['confidence']
        
        insight = {
            'category': 'processing_time',
            'description': f"Processing time shows a {trend_direction} trend with {confidence} confidence"
        }
        
        if processing_time_trend['recent_change'] is not None:
            recent_change_pct = processing_time_trend['recent_change'] * 100
            if abs(recent_change_pct) > 5:
                insight['description'] += f" (recent change: {recent_change_pct:.1f}%)"
        
        insights.append(insight)
    
    # Add bottleneck insights
    if bottlenecks:
        for bottleneck in bottlenecks:
            insights.append({
                'category': 'bottleneck',
                'description': bottleneck['description'],
                'severity': bottleneck['severity']
            })
    
    # Add correlations insights if available
    if 'status_standardized' in data.columns:
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        potential_factors = ['loan_amount', 'income', 'credit_score', 'processing_time_days']
        available_factors = [col for col in potential_factors if col in numeric_columns]
        
        for factor in available_factors:
            try:
                # Calculate correlation with approval
                df_temp = data[[factor, 'status_standardized']].dropna()
                df_temp['is_approved'] = (df_temp['status_standardized'] == 'approved').astype(int)
                
                if len(df_temp) > 10:  # Minimum sample size
                    corr = df_temp[factor].corr(df_temp['is_approved'])
                    
                    if abs(corr) > 0.2:
                        direction = 'positive' if corr > 0 else 'negative'
                        strength = 'strong' if abs(corr) > 0.5 else 'moderate'
                        
                        insights.append({
                            'category': 'correlation',
                            'description': f"{factor.replace('_', ' ').title()} shows a {strength} {direction} correlation ({corr:.2f}) with approval rates"
                        })
            except:
                continue
    
    return insights

def generate_recommendations(insights):
    """
    Generate recommendations based on insights
    
    Parameters:
    insights (list): List of insights
    
    Returns:
    list: List of recommendations
    """
    recommendations = []
    
    if not insights:
        return recommendations
    
    # Process insights by category
    for insight in insights:
        category = insight.get('category', '')
        description = insight.get('description', '')
        
        # Approval rate recommendations
        if category == 'approval_rate' and 'decreasing' in description:
            recommendations.append({
                'category': 'approval_rate',
                'description': "Investigate reasons for declining approval rates and consider adjusting lending criteria or application processes",
                'priority': 'high'
            })
        
        # Processing time recommendations
        if category == 'processing_time' and 'increasing' in description:
            recommendations.append({
                'category': 'processing_time',
                'description': "Review and optimize loan processing workflow to reduce increasing processing times",
                'priority': 'high'
            })
        elif category == 'processing_time' and 'decreasing' in description:
            recommendations.append({
                'category': 'processing_time',
                'description': "Document and standardize recent process improvements that have led to reduced processing times",
                'priority': 'medium'
            })
        
        # Bottleneck recommendations
        if category == 'bottleneck':
            severity = insight.get('severity', 'medium')
            
            if 'processing_time outliers' in description:
                recommendations.append({
                    'category': 'bottleneck',
                    'description': "Implement process monitoring to identify and address applications with extended processing times",
                    'priority': 'high' if severity == 'high' else 'medium'
                })
            
            if 'rejection_reason' in description:
                recommendations.append({
                    'category': 'bottleneck',
                    'description': "Focus on the dominant rejection reason to improve application quality or adjust lending criteria",
                    'priority': 'high' if severity == 'high' else 'medium'
                })
            
            if 'volume_fluctuation' in description:
                recommendations.append({
                    'category': 'bottleneck',
                    'description': "Develop resource allocation strategy to better handle application volume fluctuations",
                    'priority': 'medium'
                })
        
        # Correlation recommendations
        if category == 'correlation':
            if 'loan amount' in description.lower() and 'negative' in description:
                recommendations.append({
                    'category': 'correlation',
                    'description': "Review lending criteria for higher loan amounts to identify potential barriers to approval",
                    'priority': 'medium'
                })
            
            if 'credit score' in description.lower() and 'positive' in description:
                recommendations.append({
                    'category': 'correlation',
                    'description': "Consider developing specialized products for different credit score segments",
                    'priority': 'medium'
                })
            
            if 'income' in description.lower():
                recommendations.append({
                    'category': 'correlation',
                    'description': "Evaluate income verification procedures and requirements for potential optimization",
                    'priority': 'medium'
                })
    
    # Add general recommendations if specific ones are limited
    if len(recommendations) < 3:
        recommendations.append({
            'category': 'general',
            'description': "Implement regular data analysis reviews to track key metrics and identify trends early",
            'priority': 'medium'
        })
        
        recommendations.append({
            'category': 'general',
            'description': "Develop standardized reporting for loan origination performance to share with stakeholders",
            'priority': 'medium'
        })
    
    return recommendations
