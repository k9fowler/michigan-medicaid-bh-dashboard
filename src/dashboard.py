"""
Dashboard Module
==================
Creates interactive dashboard using streamlit/plotly
"""
# Imports
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from apiscraper import MedicaidAPIScraper
from datacleaner import MedicaidDataCleaner

# Page config
st.set_page_config(
    page_title="Michigan Medicaid Analysis",
    page_icon="🏥",
    layout="wide"
)

# Load and process data using existing pipeline
@st.cache_data
def load_and_process_data():
    """Use the existing data pipeline"""
    # Step 1: Get data 
    scraper = MedicaidAPIScraper()
    df = scraper.fetch_or_load()
    
    # Step 2: Clean data 
    cleaner = MedicaidDataCleaner()
    df_clean = cleaner.clean_michigan_behavioral(df)
    
    return df_clean

# Run the same calculations as analyze.py
@st.cache_data
def calculate_metrics(df, selected_year):
    """Calculate metrics matching analyze.py logic"""
    
    # Filter for the selected year
    current_data = df[df['Calendar Year'] == selected_year]
    
    # State-level totals (MCO Name == 'All')
    state_data = current_data[current_data['MCO Name'] == 'All']
    total_eligible = state_data['Number of Eligible MCO Patients'].sum()
    total_active = state_data['Number of Active Patients'].sum()
    
    # Previous year for comparison
    prev_data = df[(df['Calendar Year'] == selected_year - 1) & (df['MCO Name'] == 'All')]
    prev_eligible = prev_data['Number of Eligible MCO Patients'].sum()
    prev_active = prev_data['Number of Active Patients'].sum()
    
    # Calculate changes
    change_eligible = ((total_eligible - prev_eligible) / prev_eligible * 100) if prev_eligible > 0 else 0
    change_active = ((total_active - prev_active) / prev_active * 100) if prev_active > 0 else 0
    
    # Utilization rate (matching analyze.py calculation)
    utilization = (total_active / total_eligible * 100) if total_eligible > 0 else 0
    
    # Previous year utilization for comparison
    prev_utilization = (prev_active / prev_eligible * 100) if prev_eligible > 0 else 0
    utilization_change = utilization - prev_utilization  # PP change
    
    # Top MCO (Comprehensive MCO only, County == 'All')
    mco_data = current_data[(current_data['County'] == 'All') & 
                           (current_data['MCO Name'] != 'All') & 
                           (current_data['Plan Category'] == 'Comprehensive MCO')]
    
    if not mco_data.empty:
        top_mco = mco_data.nlargest(1, 'Number of Active Patients').iloc[0]
        top_mco_name = top_mco['MCO Name']
        # Calculate market share
        top_mco_share = (top_mco['Number of Active Patients'] / mco_data['Number of Active Patients'].sum() * 100)
    else:
        top_mco_name = "N/A"
        top_mco_share = 0
    
    return {
        'total_eligible': total_eligible,
        'total_active': total_active,
        'change_eligible': change_eligible,
        'change_active': change_active,
        'utilization': utilization,
        'utilization_change': utilization_change,
        'top_mco_name': top_mco_name,
        'top_mco_share': top_mco_share
    }

# Title
st.title("Michigan Medicaid Behavioral Health Analysis")
st.markdown("2020-2025 Comprehensive Report")

# Load the cleaned data
df = load_and_process_data()

# Sidebar
st.sidebar.image("assets/university_logo.png", width=200)
st.sidebar.markdown("---")
st.sidebar.header("🔧 Filters")
selected_year = st.sidebar.selectbox(
    "Select Year",
    options=sorted(df['Calendar Year'].unique(), reverse=True)
)

# Add divider
st.sidebar.markdown("---")

# Add download section
st.sidebar.header("📚 Resources")

# Read PDF file (data dictionary)
with open("data/medicaid_data_dictionary.pdf", "rb") as pdf_file:
    pdf_bytes = pdf_file.read()

st.sidebar.download_button(
    label="📄 Download Data Dictionary (PDF)",
    data=pdf_bytes,
    file_name="medicaid_data_dictionary.pdf",
    mime="application/pdf"
)

# Calculate metrics using analyze.py logic
metrics = calculate_metrics(df, selected_year)

# Key Metrics Row
st.header("📊 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Eligible Patients", 
        f"{metrics['total_eligible']:,.0f}", 
        f"{metrics['change_eligible']:+.1f}%"
    )

with col2:
    st.metric(
        "Active BH Patients", 
        f"{metrics['total_active']:,.0f}", 
        f"{metrics['change_active']:+.1f}%"
    )

with col3:
    st.metric(
        "Utilization Rate", 
        f"{metrics['utilization']:.1f}%", 
        f"{metrics['utilization_change']:+.1f}pp"
    )

with col4:
    st.metric(
        label="Market Leader",
        value=metrics['top_mco_name'],
        delta=f"{metrics['top_mco_share']:.1f}% market share",
        delta_color="normal"
    )

# Charts Section
st.header("📈 Trends & Analysis")

# Row 1: Enrollment Timeline
# Enrollment over time 
yearly_data = df[df['MCO Name'] == 'All'].groupby('Calendar Year').agg({
    'Number of Eligible MCO Patients': 'sum',
    'Number of Active Patients': 'sum'
}).reset_index()

# Create figure with secondary y-axis
from plotly.subplots import make_subplots

fig_enrollment = make_subplots(
    specs=[[{"secondary_y": True}]],
    subplot_titles=[""]
)

# Add eligible patients trace (left y-axis)
fig_enrollment.add_trace(
    go.Scatter(
        x=yearly_data['Calendar Year'],
        y=yearly_data['Number of Eligible MCO Patients'],
        name='Eligible Patients',
        line=dict(color='#00B4D8', width=3),
        mode='lines+markers',
        marker=dict(size=8)
    ),
    secondary_y=False,
)

# Add active patients trace (right y-axis)
fig_enrollment.add_trace(
    go.Scatter(
        x=yearly_data['Calendar Year'],
        y=yearly_data['Number of Active Patients'],
        name='Active Patients',
        line=dict(color='#F72585', width=3),
        mode='lines+markers',
        marker=dict(size=8)
    ),
    secondary_y=True,
)

# Update layout
fig_enrollment.update_layout(
    title='Enrollment & Utilization Timeline',
    hovermode='x unified',
    height=400,
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

# Update axes labels
fig_enrollment.update_xaxes(title_text="Calendar Year")
fig_enrollment.update_yaxes(title_text="Eligible Patients", secondary_y=False, tickformat=",")
fig_enrollment.update_yaxes(title_text="Active Patients", secondary_y=True, tickformat=",")

st.plotly_chart(fig_enrollment, use_container_width=True)

# Row 2: Plan Type Comparison and MCO Utilization
col1, col2 = st.columns(2)

with col1:
    # PIHP vs Comprehensive MCO comparison
    plan_comparison = df[(df['Calendar Year'] == selected_year) & 
                        (df['County'] == 'All') & 
                        (df['MCO Name'] != 'All')].groupby('Plan Category').agg({
                        'Number of Active Patients': 'sum'
                    }).reset_index()
    
    # Filter to just the two main categories
    plan_comparison = plan_comparison[
        plan_comparison['Plan Category'].isin([
            'Comprehensive MCO',
            'Behavioral Health Inpatient Specialty Plan (PIHP)'
        ])
    ]
    
    if not plan_comparison.empty:
        # Simplify names for display
        plan_comparison['Display Name'] = plan_comparison['Plan Category'].map({
            'Comprehensive MCO': 'Comprehensive',
            'Behavioral Health Inpatient Specialty Plan (PIHP)': 'PIHP'
        })
        
        fig_plan_type = px.pie(
            plan_comparison,
            values='Number of Active Patients',
            names='Display Name',
            title='Active Patients by MCO Category',
        )
        fig_plan_type.update_traces(
            textposition='inside',
            textinfo='percent+label+value',
            texttemplate='%{label}<br>%{value:,.0f}<br>(%{percent})',
            marker=dict(colors=['#00B4D8', '#F72585'])
        )
        st.plotly_chart(fig_plan_type, use_container_width=True)

with col2:
    # Top 5 MCOs utilization visualization
    mco_util_data = df[(df['County'] != 'All') & 
                       (df['Calendar Year'] == selected_year) & 
                       (df['MCO Name'] != 'All') & 
                       (df['Plan Category'] == 'Comprehensive MCO')].groupby('MCO Name').agg({
                       'Number of Active Patients': 'sum',
                       'Number of Eligible MCO Patients': 'sum'
                   }).reset_index()
    
    # Calculate utilization rate
    mco_util_data['Utilization Rate'] = (
        mco_util_data['Number of Active Patients'] / 
        mco_util_data['Number of Eligible MCO Patients'] * 100
    ).round(1)
    
    # Get top 5 by active patients
    top_5_util = mco_util_data.nlargest(5, 'Number of Active Patients')
    
    # Create stacked bar chart
    fig_utilization = go.Figure()

    # Add active patients first (bottom of stack)
    fig_utilization.add_trace(go.Bar(
        name='Active Patients',
        x=top_5_util['MCO Name'],
        y=top_5_util['Number of Active Patients'],
        marker_color='#00B4D8',
        text=top_5_util['Number of Active Patients'].apply(lambda x: f'{x:,.0f}'),
        textposition='inside',
        textfont=dict(size=10, color='white'),
        hovertemplate='Active: %{y:,.0f}<extra></extra>'
    ))

    # Add inactive patients second (top of stack)
    fig_utilization.add_trace(go.Bar(
        name='Inactive Patients',
        x=top_5_util['MCO Name'],
        y=top_5_util['Number of Eligible MCO Patients'] - top_5_util['Number of Active Patients'],
        marker_color='lightgray',
        text=[f"{rate:.1f}%" for rate in top_5_util['Utilization Rate']],
        textposition='outside',
        textfont=dict(size=12, color='black'),
        hovertemplate='Inactive: %{y:,.0f}<extra></extra>'
    ))

    fig_utilization.update_layout(
        title='Top 5 Comprehensive MCOs - Utilization Analysis',
        barmode='stack',
        showlegend=True,
        yaxis_title='Number of Patients',
        xaxis_tickangle=-45,
        yaxis=dict(
            range=[0, top_5_util['Number of Eligible MCO Patients'].max() * 1.1]  # Add 10% padding
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_utilization, use_container_width=True)

# Row 3: Market Share and Provider Network
col1, col2 = st.columns(2)

with col1:
    # Market share donut (Top 5 Comprehensive MCOs)
    mco_data = df[(df['County'] == 'All') & 
                  (df['Calendar Year'] == selected_year) & 
                  (df['MCO Name'] != 'All') & 
                  (df['Plan Category'] == 'Comprehensive MCO')]
    
    if not mco_data.empty:
        # Get top 5 and calculate "Others"
        top_5_mcos = mco_data.nlargest(5, 'Number of Active Patients')
        others_total = mco_data[~mco_data['MCO Name'].isin(top_5_mcos['MCO Name'])]['Number of Active Patients'].sum()
        
        # Create a dataframe for the pie chart
        pie_data = pd.concat([
            top_5_mcos[['MCO Name', 'Number of Active Patients']],
            pd.DataFrame({'MCO Name': ['Others'], 'Number of Active Patients': [others_total]})
        ])
        
        fig_market = px.pie(
            pie_data, 
            values='Number of Active Patients', 
            names='MCO Name',
            title=f'{selected_year} Market Share - All Comprehensive MCOs',
            hole=0.4
        )
        st.plotly_chart(fig_market, use_container_width=True)

with col2:
    # Provider Network Evolution (2020-2025)
    # Get top 5 MCOs from current year
    if not mco_data.empty:
        top_5_mco_names = mco_data.nlargest(5, 'Number of Active Patients')['MCO Name'].tolist()
        
        # Calculate provider changes
        provider_changes = []
        for mco_name in top_5_mco_names:
            mco_all_years = df[(df['MCO Name'] == mco_name) & (df['County'] == 'All')]
            
            # Get 2020 and current year data
            prov_2020 = mco_all_years[mco_all_years['Calendar Year'] == 2020]['Number of Providers'].values
            prov_current = mco_all_years[mco_all_years['Calendar Year'] == selected_year]['Number of Providers'].values
            
            if len(prov_2020) > 0 and len(prov_current) > 0:
                change = ((prov_current[0] - prov_2020[0]) / prov_2020[0]) * 100
                provider_changes.append({
                    'MCO': mco_name,
                    'Change': change,
                    'Color': 'green' if change > 0 else 'red'
                })
        
        if provider_changes:
            change_df = pd.DataFrame(provider_changes)
            
            # Create lollipop chart
            fig_providers = px.scatter(
                change_df,
                x='Change',
                y='MCO',
                title=f'Provider Network Evolution (2020-{selected_year})',
                labels={'Change': 'Provider Network Change (%)'},
                color='Color',
                color_discrete_map={'green': '#06FFA5', 'red': '#F71735'}
            )
            
            # Add lines from 0 to each point
            for _, row in change_df.iterrows():
                fig_providers.add_shape(
                    type='line',
                    x0=0, x1=row['Change'],
                    y0=row['MCO'], y1=row['MCO'],
                    line=dict(color='lightgray', width=2)
                )
            
            # Add vertical line at 0
            fig_providers.add_vline(x=0, line_dash="dash", line_color="gray")
            
            fig_providers.update_traces(marker_size=12)
            fig_providers.update_layout(showlegend=False)
            st.plotly_chart(fig_providers, use_container_width=True)

# Row 4: County Analysis and Service Intensity
col1, col2 = st.columns(2)

with col1:
    # Top counties by utilization (MCO Name == 'All', County != 'All')
    county_data = df[(df['Calendar Year'] == selected_year) & 
                     (df['MCO Name'] == 'All') & 
                     (df['County'] != 'All')].nlargest(10, 'Percent Of Eligible Patients Receving Services')
    
    if not county_data.empty:
        # Convert to percentage for display
        county_data['Utilization %'] = county_data['Percent Of Eligible Patients Receving Services'] * 100
        
        fig_counties = px.bar(
            county_data, 
            x='Utilization %',
            y='County',
            orientation='h',
            title='Top 10 Counties by Utilization Rate',
            labels={'Utilization %': 'Utilization Rate (%)'}
        )
        fig_counties.update_traces(marker_color='lightblue')
        st.plotly_chart(fig_counties, use_container_width=True)

with col2:
    # Services per patient by MCO (Top 5 Comprehensive MCOs)
    services_data = df[(df['County'] == 'All') & 
                       (df['Calendar Year'] == selected_year) & 
                       (df['MCO Name'] != 'All') & 
                       (df['Plan Category'] == 'Comprehensive MCO')]
    
    if not services_data.empty:
        top_5_services = services_data.nlargest(5, 'Number of Active Patients')
        
        fig_services = px.bar(
            top_5_services,
            x='MCO Name',
            y='Number of Services per Active Patient',
            title='Service Intensity by Top Comprehensive MCOs',
            labels={'Number of Services per Active Patient': 'Services per Patient'}
        )
        fig_services.update_traces(marker_color='lightcoral')
        st.plotly_chart(fig_services, use_container_width=True)

# Data Table Section
st.header("📋 Detailed Data")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["MCO Summary", "County Details", "Time Series"])

with tab1:
    # MCO Summary - hybrid approach for data accuracy
    # Get county-level data for eligible patients (excluding PAHPs)
    mco_county_data = df[(df['Calendar Year'] == selected_year) & 
                         (df['County'] != 'All') & 
                         (df['MCO Name'] != 'All') & 
                         (df['Plan Category'] != 'Outpatient Specialty Health Plan (PAHP)')]
    
    # Get 'All' county data for official active patient counts (excluding PAHPs)
    mco_all_data = df[(df['Calendar Year'] == selected_year) & 
                      (df['County'] == 'All') & 
                      (df['MCO Name'] != 'All') & 
                      (df['Plan Category'] != 'Outpatient Specialty Health Plan (PAHP)')]
    
    if not mco_county_data.empty and not mco_all_data.empty:
        # Aggregate eligible patients from county-level data
        eligible_by_mco = mco_county_data.groupby(['MCO Name', 'Plan Category']).agg({
            'Number of Eligible MCO Patients': 'sum'
        }).reset_index()
        
        # Get official totals from 'All' county rows
        official_totals = mco_all_data[['MCO Name', 'Plan Category', 
                                       'Number of Active Patients', 
                                       'Number of Providers']]
        
        # Merge the data
        mco_totals = official_totals.merge(
            eligible_by_mco, 
            on=['MCO Name', 'Plan Category'], 
            how='left'
        )
        
        # Calculate utilization rate using hybrid data
        mco_totals['Utilization Rate (%)'] = (
            mco_totals['Number of Active Patients'] / 
            mco_totals['Number of Eligible MCO Patients'] * 100
        ).round(1)
        
        # Sort by active patients
        mco_totals = mco_totals.sort_values('Number of Active Patients', ascending=False)
        
        st.dataframe(
            mco_totals[['MCO Name', 'Plan Category', 'Number of Active Patients', 
                       'Number of Eligible MCO Patients', 'Utilization Rate (%)', 
                       'Number of Providers']],
            use_container_width=True
        )
        
        # Add note about data methodology
        st.caption("*Active patients from official MCO totals, eligible patients aggregated from county-level data. PAHPs excluded.")
        
        # Add an expandable section to see county-level detail
        with st.expander("View County-Level Detail"):
            county_detail = mco_county_data[['MCO Name', 'County', 'Plan Category', 
                                           'Number of Active Patients', 
                                           'Number of Eligible MCO Patients', 
                                           'Number of Providers']].sort_values(
                                           ['MCO Name', 'County'])
            st.dataframe(county_detail, use_container_width=True)

with tab2:
    # County Details (County != 'All', MCO == 'All')
    county_details = df[(df['Calendar Year'] == selected_year) & 
                        (df['County'] != 'All') & 
                        (df['MCO Name'] == 'All')]
    
    if not county_details.empty:
        # Calculate utilization percentage for display
        county_details = county_details.copy()
        county_details['Utilization %'] = county_details['Percent Of Eligible Patients Receving Services'] * 100
        
        st.dataframe(
            county_details[['County', 'Number of Active Patients', 'Number of Eligible MCO Patients',
                           'Utilization %']].sort_values('Number of Active Patients', ascending=False),
            use_container_width=True
        )

with tab3:
    # Time series for selected MCO
    mco_list = df[(df['MCO Name'] != 'All') & 
                  (df['Plan Category'] == 'Comprehensive MCO')]['MCO Name'].unique()
    
    selected_mco = st.selectbox("Select MCO for time series", sorted(mco_list))
    
    if selected_mco:
        mco_time_series = df[(df['MCO Name'] == selected_mco) & 
                            (df['County'] == 'All')]
        
        if not mco_time_series.empty:
            fig_time = px.line(
                mco_time_series,
                x='Calendar Year',
                y='Number of Active Patients',
                title=f'{selected_mco} - Patient Volume Over Time'
            )
            st.plotly_chart(fig_time, use_container_width=True)


# Footer
st.markdown("---")
st.markdown("Analysis by Kevin F. Fowler Sr., Wayne State University")
st.markdown("Dashboard built with Streamlit | Data from CMS Medicaid Managed Care")
st.markdown("*Note: Data filtered to Michigan Behavioral Health services only*")