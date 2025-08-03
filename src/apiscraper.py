"""
API Scraper Module
==================
Fetches Medicaid Managed Care data from CMS API
"""
# Imports
import requests
import pandas as pd
import os
import time
from datetime import datetime


class MedicaidAPIScraper:
    def __init__(self):
        self.api_url = "https://data.cms.gov/data-api/v1/dataset/a93f5362-2fe6-4b4d-8260-118be0d618e0/data"
        self.data_dir = "data"
        self.current_file = os.path.join(self.data_dir, "medicaid_data_current.csv")
        self.backup_file = os.path.join(self.data_dir, "medicaid_data_backup.csv")
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def fetch_from_api(self):
        """Fetch complete dataset from CMS API with pagination"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting API fetch...")
        
        all_data = []
        offset = 0
        limit = 1000
        expected_min = 23000  # Minimum expected rows
        
        try:
            start_time = time.time()
            
            while True:
                params = {'offset': offset, 'limit': limit}
                print(f"  Fetching rows {offset + 1:,} to {offset + limit:,}...", end='')
                
                response = requests.get(self.api_url, params=params, timeout=60)
                
                if response.status_code == 200:
                    batch = response.json()
                    
                    if not batch:
                        break
                    
                    all_data.extend(batch)
                    print(f" ✓ ({len(all_data):,} total)")
                    
                    if len(batch) < limit:
                        break
                    
                    offset += limit
                else:
                    print(f"\n✗ API Error: Status {response.status_code}")
                    return None
            
            elapsed = time.time() - start_time
            print(f"\n✓ Fetch complete: {len(all_data):,} rows in {elapsed:.1f}s")
            
            if len(all_data) < expected_min:
                print(f"⚠ Warning: Expected at least {expected_min:,} rows")
            
            return pd.DataFrame(all_data)
            
        except Exception as e:
            print(f"\n✗ Error: {type(e).__name__}: {e}")
            return None
    
    def save_data(self, df):
        """Save data and rotate files"""
        # Rotate files: current -> backup
        if os.path.exists(self.current_file):
            if os.path.exists(self.backup_file):
                os.remove(self.backup_file)
            os.rename(self.current_file, self.backup_file)
            print("  Rotated: current → backup")
        
        # Save new data
        df.to_csv(self.current_file, index=False)
        print(f"✓ Saved: {self.current_file} ({len(df):,} rows)")
    
    def load_current_data(self):
        """Load current data file if it exists"""
        if os.path.exists(self.current_file):
            df = pd.read_csv(self.current_file)
            print(f"✓ Loaded: {self.current_file} ({len(df):,} rows)")
            return df
        else:
            print("✗ No current data file found")
            return None
    
    def fetch_or_load(self, force_refresh=False):
        """Main method: fetch new data or load existing"""
        if force_refresh or not os.path.exists(self.current_file):
            print("Fetching fresh data from API...")
            df = self.fetch_from_api()
            if df is not None:
                self.save_data(df)
            return df
        else:
            return self.load_current_data()


# Convenience function for direct module usage
def get_data(force_refresh=False):
    scraper = MedicaidAPIScraper()
    return scraper.fetch_or_load(force_refresh)