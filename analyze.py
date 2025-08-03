# -*- coding: utf-8 -*-
"""
Created on: August 3, 2025
Author: Kevin Fowler, HP2366
Course: INF 6050
University: Wayne State University, Mike Ilitch School of Business
Assignment: Honors Project - Healthcare Data Analysis

Python Version: 3.13
Required Modules: pandas, numpy, requests, datetime, argparse, sys, os, subprocess

Description: Comprehensive analysis pipeline for Michigan Medicaid Managed Care data focusing on 
             behavioral health services. Fetches data from CMS API, performs data cleansing and 
             filtering for Michigan-specific records, and generates detailed analytical reports on 
             MCO performance, utilization rates, provider networks, and market dynamics across 
             5 years (2020-2025). Automatically launches interactive Streamlit dashboard upon completion.
             
Key Features:
- API data retrieval with pagination support for 23,000+ records
- Intelligent data cleaning and type conversion
- Multi-level aggregation analysis (State, County, MCO levels)
- Time trend analysis
- Market share calculations
- Provider network evolution tracking
- Automated dashboard launch integration
              
Data Source: CMS Medicaid Managed Care Dataset
             API: https://data.cms.gov/data-api/v1/dataset/a93f5362-2fe6-4b4d-8260-118be0d618e0/data
             
Output: Console analysis report + Interactive Streamlit dashboard

"""
# Imports
import argparse
import sys
import os
from datetime import datetime
from src.apiscraper import MedicaidAPIScraper
from src.datacleaner import MedicaidDataCleaner
import subprocess
import webbrowser
import time
import threading


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
    
    # Pre-calculate commonly used metrics for efficiency
    # Calculate 2025 patient counts by plan type
    comprehensive_mco_2025 = df[(df['County'] == 'All') & 
                                (df['MCO Name'] != 'All') & 
                                (df['Plan Category'] == 'Comprehensive MCO') & 
                                (df['Calendar Year'] == 2025)]['Number of Active Patients'].sum()
    
    pihp_2025 = df[(df['County'] == 'All') & 
               (df['MCO Name'] != 'All') & 
               (df['Plan Category'] == 'Behavioral Health Inpatient Specialty Plan (PIHP)') & 
               (df['Calendar Year'] == 2025)]['Number of Active Patients'].sum()
    
    # Calculate state-level metrics once
    state_total_active_2025 = df[(df['MCO Name'] == 'All') & 
                                 (df['Calendar Year'] == 2025) & 
                                 (df['County'] != 'All')]['Number of Active Patients'].sum()
    state_total_eligible_2025 = df[(df['MCO Name'] == 'All') & 
                                   (df['Calendar Year'] == 2025) & 
                                   (df['County'] != 'All')]['Number of Eligible MCO Patients'].sum()
    true_state_utilization_2025 = (state_total_active_2025 / state_total_eligible_2025 * 100) if state_total_eligible_2025 > 0 else 0
    
    # Calculate weighted average services per patient for state
    state_services_weighted = df[(df['MCO Name'] == 'All') & 
                                (df['Calendar Year'] == 2025) & 
                                (df['County'] != 'All')]
    total_services = (state_services_weighted['Number of Active Patients'] * 
                     state_services_weighted['Number of Services per Active Patient']).sum()
    state_avg_services_2025 = total_services / state_total_active_2025 if state_total_active_2025 > 0 else 0
    
    # Total active patients across all plan types for market share calculations
    total_mi_patients_2025 = df[(df['County'] == 'All') & 
                                (df['MCO Name'] != 'All') & 
                                (df['Calendar Year'] == 2025)]['Number of Active Patients'].sum()
    
    # Filter for MCO = "All" for statewide statistics
    all_mco_df = df[df['MCO Name'] == 'All']
    
    print("\nMICHIGAN BEHAVIORAL HEALTH ANALYSIS")
    print("="*40)
    
    # 1. Total Active Patient Volume by Year
    print("\n1. Total Active Patient Volume by Year:")
    yearly_patients = all_mco_df.groupby('Calendar Year')['Number of Active Patients'].sum().sort_index()
    for year, patients in yearly_patients.items():
        print(f"   {year}: {patients:,.0f} patients")
    
    # 2. Total Number of Providers by Year
    print("\n2. Total Number of Providers by Year:")
    yearly_providers = all_mco_df.groupby('Calendar Year')['Number of Providers'].sum().sort_index()
    for year, providers in yearly_providers.items():
        print(f"   {year}: {providers:,.0f} providers")
    
    # 3. Top 5 Counties by Active Patients (2025)
    print("\n3. Top 5 Counties by Active Patients (2025):")
    df_2025 = all_mco_df[all_mco_df['Calendar Year'] == 2025]
    if len(df_2025) > 0:
        top_counties = df_2025.nlargest(5, 'Number of Active Patients')[['County', 'Number of Active Patients']]
        for i, (idx, row) in enumerate(top_counties.iterrows(), 1):
            print(f"   {i}. {row['County']}: {row['Number of Active Patients']:,.0f} patients")
    else:
        print("   No 2025 data available")
    
    # 4. Top 5 Comprehensive MCOs by Active Patients (2025)
    print("\n4. Top 5 Comprehensive MCOs by Active Patients (2025):")
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
    
    # 5. Total Active Patients by Plan Category (2025)
    print("\n5. Total Active Patients by Plan Category (2025):")
    plan_cat_2025 = df[(df['County'] == 'All') & 
                       (df['MCO Name'] != 'All') &
                       (df['Calendar Year'] == 2025)]
    if len(plan_cat_2025) > 0:
        plan_volumes = plan_cat_2025.groupby('Plan Category')['Number of Active Patients'].sum().sort_values(ascending=False)
        for plan_cat, patients in plan_volumes.items():
            print(f"   {plan_cat}: {patients:,.0f} patients")
    else:
        print("   No 2025 plan category data available")
    
    # 6. Average % of Eligible Patients Receiving Services
    print("\n6. Average % of Eligible Patients Receiving Services:")
    
    # Calculate true state utilization from totals for overall
    state_total_active = all_mco_df['Number of Active Patients'].sum()
    state_total_eligible = all_mco_df['Number of Eligible MCO Patients'].sum()
    true_utilization = (state_total_active / state_total_eligible * 100) if state_total_eligible > 0 else 0
    print(f"   Overall average: {true_utilization:.1f}%")
    
    # Show by year using the same approach
    print("   By year:")
    for year in sorted(all_mco_df['Calendar Year'].unique()):
        year_data = all_mco_df[all_mco_df['Calendar Year'] == year]
        year_active = year_data['Number of Active Patients'].sum()
        year_eligible = year_data['Number of Eligible MCO Patients'].sum()
        year_utilization = (year_active / year_eligible * 100) if year_eligible > 0 else 0
        print(f"     {year}: {year_utilization:.1f}%")
    
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
    
    # 8. Deep Dive: Top 5 Comprehensive MCOs
    print("\n8. DEEP DIVE: TOP 5 COMPREHENSIVE MCOs")
    print("="*40)
    
    # Reuse the top_mcos from section 4
    if len(mco_2025) > 0:
        # Get the top 5 MCO names from the earlier analysis
        top_5_mcos = mco_2025.nlargest(5, 'Number of Active Patients')['MCO Name'].tolist()
        
        for rank, mco_name in enumerate(top_5_mcos, 1):
            print(f"\n{rank}. {mco_name.upper()}")
            print("-" * (len(mco_name) + 5))
            
            # Get all data for this MCO
            mco_data = df[df['MCO Name'] == mco_name]
            
            # A. Current Year Summary (2025)
            mco_2025_data = mco_data[mco_data['Calendar Year'] == 2025]
            mco_2025_summary = mco_2025_data[mco_2025_data['County'] == 'All'].iloc[0]
            
            # Calculate eligible patients
            eligible_patients_total = mco_2025_data[mco_2025_data['County'] != 'All']['Number of Eligible MCO Patients'].sum()
            active_patients_total = mco_2025_summary['Number of Active Patients']
            
            print(f"\n   2025 Summary:")
            print(f"   - Active Patients: {active_patients_total:,.0f}")
            print(f"   - Eligible Patients: {eligible_patients_total:,.0f}")
            
            # Calculate utilization from totals
            mco_utilization = (active_patients_total / eligible_patients_total * 100) if eligible_patients_total > 0 else 0
            print(f"   - Utilization Rate: {mco_utilization:.1f}%")
            print(f"   - Providers: {mco_2025_summary['Number of Providers']:,.0f}")
            print(f"   - Services per Patient: {mco_2025_summary['Number of Services per Active Patient']:.1f}")
            
            # B. YoY Growth
            print(f"\n   YoY Patient Growth:")
            yearly_data = mco_data[mco_data['County'] == 'All'].sort_values('Calendar Year')
            prev_year_patients = None
            
            for _, year_row in yearly_data.iterrows():
                year = year_row['Calendar Year']
                patients = year_row['Number of Active Patients']
                
                if prev_year_patients is not None:
                    growth = ((patients - prev_year_patients) / prev_year_patients) * 100
                    print(f"   - {year}: {patients:,.0f} patients ({growth:+.1f}% change)")
                else:
                    print(f"   - {year}: {patients:,.0f} patients (baseline)")
                
                prev_year_patients = patients
            
            # C. Geographic Coverage (Top 5 Counties for this MCO)
            print(f"\n   Top 5 Counties Served (2025):")
            mco_counties = mco_2025_data[mco_2025_data['County'] != 'All'].nlargest(5, 'Number of Active Patients')
            
            for i, (_, county_row) in enumerate(mco_counties.iterrows(), 1):
                county_name = county_row['County']
                county_patients = county_row['Number of Active Patients']
                county_utilization = county_row['Percent Of Eligible Patients Receving Services'] * 100
                print(f"   {i}. {county_name}: {county_patients:,.0f} patients ({county_utilization:.1f}% utilization)")
            
            # D. Performance Metrics vs State Average
            print(f"\n   Performance vs State Average (2025):")
            
            util_diff = mco_utilization - true_state_utilization_2025
            services_diff = mco_2025_summary['Number of Services per Active Patient'] - state_avg_services_2025
            
            print(f"   - Utilization: {mco_utilization:.1f}% (State avg: {true_state_utilization_2025:.1f}%, {util_diff:+.1f}% difference)")
            print(f"   - Services/Patient: {mco_2025_summary['Number of Services per Active Patient']:.1f} (State avg: {state_avg_services_2025:.1f}, {services_diff:+.1f} difference)")
            
            # E. Provider Network Analysis
            print(f"\n   Provider Network:")
            
            # Calculate patients per provider
            if mco_2025_summary['Number of Providers'] > 0:
                patients_per_provider = mco_2025_summary['Number of Active Patients'] / mco_2025_summary['Number of Providers']
                print(f"   - Calculated Patients/Provider: {patients_per_provider:.0f}:1")
            
            # Provider growth over time with error handling
            provider_growth = yearly_data[['Calendar Year', 'Number of Providers']].set_index('Calendar Year')
            provider_2020 = provider_growth.loc[2020, 'Number of Providers'] if 2020 in provider_growth.index else None
            provider_2025 = provider_growth.loc[2025, 'Number of Providers'] if 2025 in provider_growth.index else None
            
            if provider_2020 and provider_2025:
                total_growth = ((provider_2025 - provider_2020) / provider_2020) * 100
                print(f"   - Provider growth 2020-2025: {total_growth:+.1f}%")
            else:
                print(f"   - Provider growth 2020-2025: N/A (insufficient data)")
            
            # F. Market Share Analysis
            print(f"\n   Market Share Analysis:")
            
            # Share of Comprehensive MCO market
            total_comprehensive_mco_2025 = mco_2025['Number of Active Patients'].sum()
            market_share = (mco_2025_summary['Number of Active Patients'] / total_comprehensive_mco_2025) * 100
            print(f"   - Share of Comprehensive MCO market: {market_share:.1f}%")
            
            # Share of total active population (all plan types)
            total_share = (mco_2025_summary['Number of Active Patients'] / total_mi_patients_2025) * 100
            print(f"   - Share of total active population: {total_share:.1f}%")
            
            # Market share by eligible population (potential market)
            mco_eligible_total = eligible_patients_total
            state_eligible_total = df[(df['MCO Name'] == 'All') & 
                         (df['Plan Category'] == 'All') & 
                         (df['Calendar Year'] == 2025)]['Number of Eligible MCO Patients'].sum()
            potential_market_share = (mco_eligible_total / state_eligible_total * 100) if state_eligible_total > 0 else 0
            print(f"   - Share of eligible population: {potential_market_share:.1f}%")
            
            # Geographic dominance (only among Comprehensive MCOs)
            county_rankings = df[(df['Calendar Year'] == 2025) & 
                               (df['County'] != 'All') & 
                               (df['MCO Name'] != 'All') & 
                               (df['Plan Category'] == 'Comprehensive MCO')].copy()
            
            counties_where_leader = 0
            for county in county_rankings['County'].unique():
                county_data = county_rankings[county_rankings['County'] == county]
                if len(county_data) > 0:
                    top_mco = county_data.nlargest(1, 'Number of Active Patients')['MCO Name'].iloc[0]
                    if top_mco == mco_name:
                        counties_where_leader += 1
            
            total_counties = len(county_rankings['County'].unique())
            print(f"   - Market leader in {counties_where_leader} of {total_counties} counties ({counties_where_leader/total_counties*100:.1f}%)")
    
    # 9. Deep Dive: Top 5 PIHPs
    print("\n\n9. DEEP DIVE: TOP 5 PIHPs")
    print("\n   NOTE: No 2025 data available for Detroit Wayne Mental Health Authority or Northern Michigan Regional Entity")
    print("         Actual 2025 data may show Detroit Wayne Mental Health Authority having significant market share.")
    print("="*40)

    pihp_2025_data = df[(df['County'] == 'All') & 
                        (df['Calendar Year'] == 2025) & 
                        (df['MCO Name'] != 'All') & 
                        (df['Plan Category'] == 'Behavioral Health Inpatient Specialty Plan (PIHP)')]

    if len(pihp_2025_data) > 0:
        # Get the top 5 PIHPs
        top_5_pihps = pihp_2025_data.nlargest(5, 'Number of Active Patients')['MCO Name'].tolist()
        
        for rank, pihp_name in enumerate(top_5_pihps, 1):
            print(f"\n{rank}. {pihp_name.upper()}")
            print("-" * (len(pihp_name) + 5))
            
            # Get all data for this PIHP
            pihp_data = df[df['MCO Name'] == pihp_name]
            
            # A. Current Year Summary (2025)
            pihp_2025_specific = pihp_data[pihp_data['Calendar Year'] == 2025]
            pihp_2025_summary = pihp_2025_specific[pihp_2025_specific['County'] == 'All'].iloc[0]
            
            # Calculate eligible patients
            eligible_patients_total = pihp_2025_specific[pihp_2025_specific['County'] != 'All']['Number of Eligible MCO Patients'].sum()
            active_patients_total = pihp_2025_summary['Number of Active Patients']
            
            print(f"\n   2025 Summary:")
            print(f"   - Active Patients: {active_patients_total:,.0f}")
            print(f"   - Eligible Patients: {eligible_patients_total:,.0f}")
            
            # Calculate true utilization from totals
            pihp_utilization = (active_patients_total / eligible_patients_total * 100) if eligible_patients_total > 0 else 0
            print(f"   - Utilization Rate: {pihp_utilization:.1f}%")
            print(f"   - Providers: {pihp_2025_summary['Number of Providers']:,.0f}")
            print(f"   - Services per Patient: {pihp_2025_summary['Number of Services per Active Patient']:.1f}")
            
            # B. YoY Growth
            print(f"\n   YoY Patient Growth:")
            yearly_data = pihp_data[pihp_data['County'] == 'All'].sort_values('Calendar Year')
            prev_year_patients = None
            
            for _, year_row in yearly_data.iterrows():
                year = year_row['Calendar Year']
                patients = year_row['Number of Active Patients']
                
                if prev_year_patients is not None:
                    growth = ((patients - prev_year_patients) / prev_year_patients) * 100
                    print(f"   - {year}: {patients:,.0f} patients ({growth:+.1f}% change)")
                else:
                    print(f"   - {year}: {patients:,.0f} patients (baseline)")
                
                prev_year_patients = patients
            
            # C. Geographic Coverage
            print(f"\n   Counties Served (2025):")
            pihp_counties = pihp_2025_specific[pihp_2025_specific['County'] != 'All']
            counties_served = len(pihp_counties)
            print(f"   - Serves {counties_served} counties")
            
            # Top counties by volume
            if len(pihp_counties) > 0:
                top_counties = pihp_counties.nlargest(3, 'Number of Active Patients')
                for i, (_, county_row) in enumerate(top_counties.iterrows(), 1):
                    county_name = county_row['County']
                    county_patients = county_row['Number of Active Patients']
                    county_utilization = county_row['Percent Of Eligible Patients Receving Services'] * 100
                    print(f"   {i}. {county_name}: {county_patients:,.0f} patients ({county_utilization:.1f}% utilization)")
            
            # D. Performance Metrics
            print(f"\n   Performance Metrics:")
            print(f"   - Higher utilization ({pihp_utilization:.1f}%) reflects mandatory/crisis services")
            print(f"   - Services per patient: {pihp_2025_summary['Number of Services per Active Patient']:.1f} (intensive case management)")
            
            # E. Market Share
            print(f"\n   Market Share Analysis:")
            
            # Share of PIHP market
            total_pihp_2025 = pihp_2025_data['Number of Active Patients'].sum()
            pihp_market_share = (pihp_2025_summary['Number of Active Patients'] / total_pihp_2025) * 100
            print(f"   - Share of PIHP market: {pihp_market_share:.1f}%")
            
            # Share of total BH population
            total_share = (pihp_2025_summary['Number of Active Patients'] / total_mi_patients_2025) * 100
            print(f"   - Share of total BH population: {total_share:.1f}%")
    else:
        print("   No PIHP data available for 2025")
    
    # 10. Executive summary and key insights
    print("\n\n" + "="*60)
    print("EXECUTIVE SUMMARY & KEY INSIGHTS")
    print("="*60)

    print("\n📊 UNDERSTANDING THE DATA CONTEXT")
    print("-"*40)
    print("Michigan's Medicaid behavioral health system operates through two primary delivery mechanisms:")

    print(f"\n1. COMPREHENSIVE MCOs ({comprehensive_mco_2025:,.0f} patients in 2025)")
    print("   • Serve general Medicaid population with mild to moderate BH needs")
    print("   • Behavioral health coverage bundled with physical health")
    print("   • Voluntary, self-initiated care")
    print("   • Expected lower utilization (3-6%) due to stigma and access barriers")

    print(f"\n2. PIHPs - Prepaid Inpatient Health Plans ({pihp_2025:,.0f} patients in 2025)")
    print("   • Despite the name, manage BOTH inpatient and outpatient specialty BH services")
    print("   • Primary funding mechanism for Michigan's public mental health system")
    print("   • Serve severely mentally ill, developmentally disabled, and substance use disorders")
    print("   • Contract with CMHSPs and CCBHCs to deliver services")
    print("   • Higher utilization reflects mandatory treatments, crisis interventions, and intensive case management")

    print("\n\n🔍 KEY FINDINGS")
    print("-"*40)

    print("\n1. SERVICE UTILIZATION PATTERNS")
    print("   • Comprehensive MCO utilization (3-6%) reflects normal voluntary care-seeking")
    print("   • Not 'underperformance' - this is expected for general population")
    print("   • Priority Health leads at 6.2%, with Ottawa County reaching 10.4%")
    print("   • Geographic and cultural factors likely drive variation more than MCO performance")

    print("\n2. MARKET DYNAMICS")
    print("   • Meridian remains largest (19.0% market share) despite lower utilization")
    print("   • McLaren HP shows strongest geographic presence (leads in 8 counties)")
    print("   • Market concentration: Top 5 MCOs control 82.3% of Comprehensive MCO market")

    print("\n3. PROVIDER NETWORK TRENDS")
    print("   • Only Priority Health expanded providers (+52.0%)")
    print("   • Other MCOs reduced networks by 10-40%")
    print("   • Current ratios (4-5 patients per provider) suggest excess capacity")

    print("\n\n📈 2025 ENROLLMENT CLIFF: THE MEDICAID UNWINDING")
    print("-"*40)
    print("The 40-50% enrollment drop across ALL behavioral health plans in 2025 represents")
    print("the end of COVID-19 continuous enrollment protections, not a data quality issue.")

    print("\n\n📈 2025 ENROLLMENT CHANGES: THE MEDICAID UNWINDING")
    print("-"*40)
    print("The enrollment changes in 2025 reflect the end of COVID-19 continuous")
    print("enrollment protections, showing a modest decline from peak levels.")

    # Calculate eligible patient changes across all plan types
    baseline_2020_eligible = df[(df['MCO Name'] == 'All') & 
                            (df['Plan Category'] == 'All') & 
                            (df['Calendar Year'] == 2020)]['Number of Eligible MCO Patients'].sum()

    peak_2024_eligible = df[(df['MCO Name'] == 'All') & 
                        (df['Plan Category'] == 'All') & 
                        (df['Calendar Year'] == 2024)]['Number of Eligible MCO Patients'].sum()

    current_2025_eligible = df[(df['MCO Name'] == 'All') & 
                            (df['Plan Category'] == 'All') & 
                            (df['Calendar Year'] == 2025)]['Number of Eligible MCO Patients'].sum()

    # Calculate percentage changes
    peak_growth = ((peak_2024_eligible - baseline_2020_eligible) / baseline_2020_eligible * 100) if baseline_2020_eligible > 0 else 0
    peak_drop = ((current_2025_eligible - peak_2024_eligible) / peak_2024_eligible * 100) if peak_2024_eligible > 0 else 0
    net_change = ((current_2025_eligible - baseline_2020_eligible) / baseline_2020_eligible * 100) if baseline_2020_eligible > 0 else 0

    print("\nMEDICAID ENROLLMENT TIMELINE (All Behavioral Health Plans):")
    print(f"• 2020 Baseline:    {baseline_2020_eligible:,.0f} eligible")
    print(f"• 2024 Peak:        {peak_2024_eligible:,.0f} eligible ({peak_growth:+.1f}% from baseline)")
    print(f"• 2025 Current:     {current_2025_eligible:,.0f} eligible ({peak_drop:.1f}% from peak)")
    print(f"• Net vs 2020:      {net_change:+.1f}% (still well above pre-pandemic levels)")

    # Show impact on actual service delivery
    baseline_2020_active = df[(df['MCO Name'] == 'All') & 
                            (df['Plan Category'] == 'All') & 
                            (df['Calendar Year'] == 2020)]['Number of Active Patients'].sum()

    peak_2024_active = df[(df['MCO Name'] == 'All') & 
                        (df['Plan Category'] == 'All') & 
                        (df['Calendar Year'] == 2024)]['Number of Active Patients'].sum()

    current_2025_active = df[(df['MCO Name'] == 'All') & 
                            (df['Plan Category'] == 'All') & 
                            (df['Calendar Year'] == 2025)]['Number of Active Patients'].sum()

    active_drop = peak_2024_active - current_2025_active
    active_drop_pct = ((current_2025_active - peak_2024_active) / peak_2024_active * 100) if peak_2024_active > 0 else 0

    print("\nIMPACT ON SERVICE DELIVERY:")
    print(f"• ~{int((peak_2024_eligible - current_2025_eligible)/1000)*1000:,} Michiganders lost BH coverage")
    print(f"• Active patients peaked at {peak_2024_active:,.0f} in 2024")
    print(f"• Dropped to {current_2025_active:,.0f} in 2025 ({active_drop_pct:.1f}%)")
    print(f"• {active_drop:,.0f} fewer patients receiving services")

    print("\nKEY OBSERVATIONS:")
    print("• Enrollment remains 88% above pre-pandemic levels")
    print("• The 11% decline is significant but not catastrophic")
    print("• Active patient decline (~31%) exceeds enrollment decline (11%)")
    print("• Suggests access barriers beyond just eligibility")

    print("\nIMPLICATIONS:")
    print("• Medicaid unwinding had a moderate impact, not a cliff")
    print("• Michigan retained most of its expanded BH coverage")
    print("• Bigger concern: Why did utilization drop more than enrollment?")
    print("• May indicate administrative barriers or provider capacity issues")

    print("\n\n💡 STRATEGIC INSIGHTS FOR BEHAVIORAL HEALTH AGENCIES")
    print("-"*40)

    print("\n1. MARKET OPPORTUNITIES")
    print("   • New Providers - Partner with Priority Health (highest utilization, expanding network)")
    print("   • Metro Detroit - Maintain contracts with BCBS, Molina, and Meridian (Top 3 MCOs in Wayne County)")
    print("   • Northern Michigan - Partner with McLaren (strong geographic presence in Flint, Saginaw, Lansing)")
    print("   • Consider PIHP contracts for more stable patient volumes")

    print("\n2. POST-UNWINDING STRATEGIES")
    print("   • Develop sliding-scale programs for those who lost Medicaid")
    print("   • Increase navigator services to help with re-enrollment")
    print("   • Prepare for potential increase in uncompensated care")

    print("\n3. COMPETITIVE POSITIONING")
    print("   • Comprehensive MCOs compete on access and convenience, not utilization")
    print("   • Focus on reducing barriers (telehealth, evening hours, culturally competent care)")
    print("   • Market differentiation matters more than raw patient volume")
            
    # Additional summary statistics
    print("\n" + "="*40)
    print("SUMMARY STATISTICS")
    print("="*40)
    print(f"Total unique MCOs (excluding 'All'): {df[df['MCO Name'] != 'All']['MCO Name'].nunique()}")
    print(f"Total unique counties (excluding 'All'): {df[df['County'] != 'All']['County'].nunique()}")
    print(f"Data spans {len(df['Calendar Year'].unique())} years: {sorted([int(y) for y in df['Calendar Year'].unique()])}")
    

    print("\n" + "="*60)
    print("✓ Analysis complete!")
    print("="*60)

    # Launch dashboard
    print("\n" + "="*60)
    print("Launching interactive dashboard...")
    print("="*60)

    # Function to open browser after delay
    def open_browser():
        time.sleep(3)
        try:
            # Try different methods depending on the system
            import platform
            system = platform.system()
            
            if system == 'Linux':
                os.system('xdg-open http://localhost:8501 2>/dev/null || firefox http://localhost:8501 2>/dev/null || google-chrome http://localhost:8501 2>/dev/null')
            else:
                webbrowser.open('http://localhost:8501')
        except:
            pass

    # Start browser opener in background
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch Streamlit with specific flags to prevent its own browser opening
    dashboard_path = os.path.join("src", "dashboard.py")
    subprocess.run([
        "streamlit", "run", dashboard_path,
        "--server.port", "8501",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ])

    return 0

if __name__ == "__main__":
    # Run the analysis
    result = main()
    
