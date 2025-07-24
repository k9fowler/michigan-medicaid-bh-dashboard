"""
Medicaid Managed Care Analysis - Main Entry Point
================================================

Analyzes Michigan behavioral health services data
"""

import argparse
import sys
from datetime import datetime

# Import our modules
from src.apiscraper import MedicaidAPIScraper
from src.datacleaner import MedicaidDataCleaner


def print_header():
    """Print a nice header"""
    print("="*60)
    print("Medicaid Managed Care Analysis - Michigan Behavioral Health")
    print("="*60)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def main():
    """Main analysis workflow"""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Analyze Medicaid Managed Care data')
    parser.add_argument('--refresh', action='store_true', 
                       help='Force refresh data from API')
    parser.add_argument('--full', action='store_true',
                       help='Analyze full dataset (skip Michigan/behavioral filtering)')
    parser.add_argument('--save-clean', action='store_true',
                       help='Save cleaned data to CSV')
    
    args = parser.parse_args()
    
    print_header()
    
    # Step 1: Get data
    print("STEP 1: Data Acquisition")
    print("-"*60)
    scraper = MedicaidAPIScraper()
    df = scraper.fetch_or_load(force_refresh=args.refresh)
    
    if df is None:
        print("✗ Failed to load data. Exiting.")
        return 1
    
    print(f"\nDataset shape: {df.shape}")
    print(f"Columns: {', '.join(df.columns)}")
    
    # Step 2: Clean data (unless --full flag is used)
    if not args.full:
        print("\n\nSTEP 2: Data Cleaning")
        print("-"*60)
        cleaner = MedicaidDataCleaner()
        df = cleaner.clean_michigan_behavioral(df)
        
        if df is None:
            print("✗ Failed to clean data. Exiting.")
            return 1
        
        # Optionally save cleaned data
        if args.save_clean:
            filename = f"data/michigan_behavioral_clean_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n✓ Saved cleaned data: {filename}")
    
    # Step 3: Analysis
    print("\n\nSTEP 3: Data Analysis")
    print("-"*60)
    
    # Filter for MCO = "All" for statewide statistics
    all_mco_df = df[df['MCO Name'] == 'All']
    
    print("\nMICHIGAN BEHAVIORAL HEALTH ANALYSIS")
    print("="*40)
    
    # 1. Total Patient Volume by Year
    print("\n1. Total Patient Volume by Year:")
    yearly_patients = all_mco_df.groupby('Calendar Year')['Number of Active Patients'].sum().sort_index()
    for year, patients in yearly_patients.items():
        print(f"   {year}: {patients:,.0f} patients")
    
    # 2. Total Number of Providers by Year
    print("\n2. Total Number of Providers by Year:")
    yearly_providers = all_mco_df.groupby('Calendar Year')['Number of Providers'].sum().sort_index()
    for year, providers in yearly_providers.items():
        print(f"   {year}: {providers:,.0f} providers")
    
    # 3. Top 5 Counties (2025)
    print("\n3. Top 5 Counties by Patient Volume (2025):")
    df_2025 = all_mco_df[all_mco_df['Calendar Year'] == 2025]
    if len(df_2025) > 0:
        top_counties = df_2025.nlargest(5, 'Number of Active Patients')[['County', 'Number of Active Patients']]
        for i, (idx, row) in enumerate(top_counties.iterrows(), 1):
            print(f"   {i}. {row['County']}: {row['Number of Active Patients']:,.0f} patients")
    else:
        print("   No 2025 data available")
    
    # 4. Top 5 MCOs (2025) - Comprehensive MCOs only
    print("\n4. Top 5 MCOs by Patient Volume (2025 - Comprehensive MCOs):")
    mco_2025 = df[(df['County'] == 'All') & 
                  (df['Calendar Year'] == 2025) & 
                  (df['MCO Name'] != 'All') & 
                  (df['Plan Category'] == 'Comprehensive MCO')]
    if len(mco_2025) > 0:
        top_mcos = mco_2025.nlargest(5, 'Number of Active Patients')[['MCO Name', 'Number of Active Patients']]
        for i, (idx, row) in enumerate(top_mcos.iterrows(), 1):
            print(f"   {i}. {row['MCO Name']}: {row['Number of Active Patients']:,.0f} patients")
    else:
        print("   No 2025 Comprehensive MCO data available")
    
    # 5. Total Patient Volume by Plan Category (2025)
    print("\n5. Total Patient Volume by Plan Category (2025):")
    plan_cat_2025 = df[(df['County'] == 'All') & 
                       (df['Plan Category'] != 'Outpatient Specialty Health Plan (PAHP)') &
                       (df['Calendar Year'] == 2025)]
    if len(plan_cat_2025) > 0:
        total_plan_volume = plan_cat_2025['Number of Active Patients'].sum()
        plan_volumes = plan_cat_2025.groupby('Plan Category')['Number of Active Patients'].sum().sort_values(ascending=False)
        for plan_cat, patients in plan_volumes.items():
            print(f"   {plan_cat}: {patients:,.0f} patients")
        print("   No data available for Outpatient Specialty Health Plan (PAHP)")
    else:
        print("   No 2025 plan category data available")
    
    # 6. Average % of Eligible Patients Receiving Services
    print("\n6. Average % of Eligible Patients Receiving Services:")
    avg_utilization = all_mco_df['Percent Of Eligible Patients Receving Services'].mean()
    print(f"   Overall average: {avg_utilization*100:.1f}%")
    
    # Optional: Show by year
    print("   By year:")
    yearly_utilization = all_mco_df.groupby('Calendar Year')['Percent Of Eligible Patients Receving Services'].mean().sort_index()
    for year, pct in yearly_utilization.items():
        print(f"     {year}: {pct*100:.1f}%")
    
    # 7. Average Active Patients per Provider
    print("\n7. Average Active Patients per Provider:")
    
    # Extract number before first colon from the ratio string
    def extract_ratio(ratio_str):
        try:
            # Convert to string and get everything before first colon
            return int(str(ratio_str).split(':')[0])
        except:
            return None
    
    # Create a copy to avoid SettingWithCopyWarning
    all_mco_df = all_mco_df.copy()
    all_mco_df['Patients_Per_Provider'] = all_mco_df['Number of Active Patients per Provider'].apply(extract_ratio)
    
    # Calculate average of valid values
    valid_ratios = all_mco_df['Patients_Per_Provider'].dropna()
    if len(valid_ratios) > 0:
        avg_ratio = valid_ratios.mean()
        print(f"   Overall average: {int(avg_ratio)}:1")
        
        # Show by year
        print("   By year:")
        yearly_ratios = all_mco_df.groupby('Calendar Year')['Patients_Per_Provider'].mean().dropna().sort_index()
        for year, ratio in yearly_ratios.items():
            print(f"     {year}: {int(ratio)}:1")
    else:
        print("   Unable to calculate (no valid ratio data)")
    
    # Additional summary statistics
    print("\n" + "="*40)
    print("SUMMARY STATISTICS")
    print("="*40)
    print(f"Total unique MCOs (excluding 'All'): {df[df['MCO Name'] != 'All']['MCO Name'].nunique()}")
    print(f"Total unique counties (excluding 'All'): {df[df['County'] != 'All']['County'].nunique()}")
    print(f"Data spans {len(df['Calendar Year'].unique())} years: {sorted([int(y) for y in df['Calendar Year'].unique()])}")
    
    print("\n✓ Analysis complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())