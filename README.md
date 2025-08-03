# Michigan Medicaid Behavioral Health Analysis
A comprehensive data analysis pipeline and interactive dashboard examining Michigan's Medicaid Managed Care behavioral health services from 2020-2025.

## Project Information

- **Author**: Kevin Fowler, HP2366
- **University**: Wayne State University, Mike Ilitch School of Business
- **Course**: INF 6050 - Honors Project
- **Date**: August 2025

## Project Overview

This project analyzes 5 years of Medicaid Managed Care data to provide insights into:
- Behavioral health service utilization patterns
- MCO (Managed Care Organization) market dynamics
- Provider network evolution
- County-level performance metrics
- Impact of Medicaid unwinding on enrollment

### Key Findings
- 234,658 active behavioral health patients in Michigan (2025)
- 9.7% overall utilization rate
- Meridian leads market with 19.0% share
- Significant enrollment changes due to end of COVID-19 continuous enrollment

## Quick Start

### Prerequisites
- Python 3.12 or higher
- pip (or conda)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/k9fowler/michigan-medicaid-bh-dashboard.git
cd michigan-medicaid-bh-dashboard
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt # Anaconda Users: conda install -r requirements.txt
```

## Running the Analysis 
**Note**: Must be run from terminal/command prompt, not from within Spyder or Jupyter! 

From the project root directory, run:
```bash
python analyze.py
```

The analysis will:
- Fetch/load data from CMS API
- Clean and filter for Michigan behavioral health
- Generate console analysis report
- Launch interactive dashboard

## View Dashboard 
**Note**: WSL Users must manually open localhost:8501 - no browsers in linux subsystem 

Open your browser to: http://localhost:8501 (if dashboard does not automatically open)



## Project Structure - cat tree.txt to view in terminal
```bash
honorsproject/
├── analyze.py              # Main analysis script
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── src/
│   ├── apiscraper.py      # CMS API data fetcher
│   ├── datacleaner.py     # Data cleaning pipeline
│   └── dashboard.py       # Streamlit dashboard
├── data/
│   ├── medicaid_data_current.csv    # Latest data
│   ├── medicaid_data_backup.csv     # Previous fetch
│   └── medicaid_data_dictionary.pdf # CMS data definitions
└── assets/
    └── university_logo.png # Wayne State branding
```

## Tech Stack
Data Processing: pandas, numpy
API Integration: requests
Visualization: Plotly, Streamlit
Dashboard Framework: Streamlit

## Dashboard Features
Key Performance Indicators
- Total eligible patients with year-over-year change
- Active behavioral health patients
- Utilization rate trends
- Market leader identification

Interactive Visualizations
- Enrollment Timeline: Dual-axis view of eligible vs active patients
- Plan Type Analysis: MCO vs PIHP distribution
- Market Share: Top 5 MCO breakdown
- Provider Networks: Evolution from 2020-2025
- County Performance: Top counties by utilization
- Service Intensity: Services per patient by MCO

Data Tables
- MCO summary with accurate eligible patient counts
- County-level detail views
- Time series analysis by organization

## Command Line Options
```bash
# Force refresh data from API
python analyze.py --refresh

# Analyze full dataset (skip Michigan filtering)
python analyze.py --full

# Save cleaned data
python analyze.py --save-clean
```

## Data Source
CMS Medicaid Managed Care Dataset

API: https://data.cms.gov/data-api/v1/dataset/a93f5362-2fe6-4b4d-8260-118be0d618e0/data
Updated: Quarterly
Records: ~23,000 (filtered to ~11,000 for Michigan behavioral health)

## Important Notes
Data Quality: Eligible patient counts are aggregated from county-level data due to inconsistencies in state-level reporting
Plan Types: Analysis focuses on Comprehensive MCOs and PIHPs, excluding PAHPs
Time Period: 2025 data reflects post-pandemic Medicaid unwinding impact
This project is submitted as part of academic coursework at Wayne State University.
---
For questions or issues, contact: hp2366@wayne.edu