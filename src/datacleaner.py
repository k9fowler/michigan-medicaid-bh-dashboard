"""
Data Cleaner Module
===================
Filters Medicaid data for Michigan behavioral health services
"""

import pandas as pd
import numpy as np


class MedicaidDataCleaner:
    def __init__(self):
        self.state_filter = 'Michigan'
        self.behavioral_health_category = 'Behavioral Health'
        self.expected_rows = 11808  # Expected after filtering
        
    def clean_datatypes(self, df):
        """Convert string columns to appropriate numeric types"""
        numeric_columns = [
            'Number of Active Patients',
            'Number of Eligible MCO Patients', 
            'Number of Providers',
            'Percent Of Eligible Patients Receving Services',
            'Number of Services per Active Patient',
            'Calendar Year'
        ]
        
        df = df.copy()
        
        for col in numeric_columns:
            if col in df.columns:
                # Remove commas and convert
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(',', ''), 
                    errors='coerce'
                )
        
        return df
    
    def filter_michigan(self, df):
        """Filter for Michigan records only"""
        michigan_df = df[df['State'] == self.state_filter].copy()
        print(f"  Michigan filter: {len(df):,} → {len(michigan_df):,} rows")
        return michigan_df
    
    def filter_behavioral_health(self, df):
        """Filter for behavioral health services"""
        behavioral_df = df[df['Service Category'] == self.behavioral_health_category].copy()
        print(f"  Behavioral filter: {len(df):,} → {len(behavioral_df):,} rows")
        return behavioral_df
    
    def get_summary_stats(self, df):
        """Generate quick summary statistics"""
        stats = {
            'total_rows': len(df),
            'states': df['State'].nunique() if 'State' in df.columns else 0,
            'mcos': df['MCO Name'].nunique(),
            'counties': df['County'].nunique() if 'County' in df.columns else 0,
            'service_categories': df['Service Category'].nunique(),
            'years': sorted(df['Calendar Year'].unique()) if 'Calendar Year' in df.columns else [],
            'total_patients': df['Number of Active Patients'].sum() if 'Number of Active Patients' in df.columns else 0
        }
        return stats
    
    def clean_michigan_behavioral(self, df):
        """Main cleaning pipeline for Michigan behavioral health"""
        print("\nCleaning data...")
        
        # Clean data types first
        df = self.clean_datatypes(df)
        
        # Apply filters
        df = self.filter_michigan(df)
        if len(df) == 0:
            print("✗ No Michigan data found!")
            return None
            
        df = self.filter_behavioral_health(df)
        if len(df) == 0:
            print("✗ No behavioral health data found!")
            return None
        
        # Verify row count
        if len(df) >= 11000:
            print(f"✓ Row count verified: {len(df):,} rows")
        else:
            print(f"⚠ Row count warning: {len(df):,} rows (expected 11000+)")
        
        return df


# Convenience function for direct module usage
def clean_for_michigan_behavioral(df):
    cleaner = MedicaidDataCleaner()
    return cleaner.clean_michigan_behavioral(df)