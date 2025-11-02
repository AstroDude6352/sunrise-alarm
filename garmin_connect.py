"""
Garmin Connect API Integration for Real-Time Sleep Data
Install: pip install garminconnect
"""

import os
from datetime import datetime, timedelta
from garminconnect import Garmin, GarminConnectAuthenticationError
import pandas as pd
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GarminSleepFetcher:
    def __init__(self, email=None, password=None):
        """Initialize Garmin Connect client"""
        self.email = email or os.getenv("GARMIN_EMAIL")
        self.password = password or os.getenv("GARMIN_PASSWORD")
        self.client = None
        self.token_store = "garmin_tokens.json"
        
    def authenticate(self):
        """Login to Garmin Connect with token caching"""
        try:
            self.client = Garmin(self.email, self.password)
            
            # Try to load saved tokens
            if os.path.exists(self.token_store):
                try:
                    with open(self.token_store, 'r') as f:
                        tokens = json.load(f)
                    self.client.login(tokens.get('oauth1'), tokens.get('oauth2'))
                    print("Logged in using saved tokens")
                except:
                    # If token login fails, do fresh login
                    self.client.login()
                    print("Logged in to Garmin Connect")
            else:
                # Fresh login
                self.client.login()
                print("Logged in to Garmin Connect")
                    
        except GarminConnectAuthenticationError as e:
            print(f"Authentication failed: {e}")
            # Delete invalid tokens
            if os.path.exists(self.token_store):
                os.remove(self.token_store)
            raise
            
    def get_sleep_data(self, days=30):
        """Fetch sleep data for the last N days"""
        if not self.client:
            self.authenticate()
            
        sleep_records = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"Fetching sleep data from {start_date.date()} to {end_date.date()}...")
        
        for day_offset in range(days):
            date = end_date - timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")
            
            try:
                sleep_data = self.client.get_sleep_data(date_str)
                
                if sleep_data and 'dailySleepDTO' in sleep_data:
                    sleep_info = sleep_data['dailySleepDTO']
                    
                    # Extract relevant metrics
                    record = {
                        'Date': date_str,
                        'Avg Score': sleep_info.get('sleepScores', {}).get('overall', {}).get('value'),
                        'Avg Duration': self._format_duration(sleep_info.get('sleepTimeSeconds', 0)),
                        'Avg Sleep Need': self._format_duration(sleep_info.get('sleepNeedSeconds', 0)),
                        'Avg Bedtime': self._format_time(sleep_info.get('sleepStartTimestampGMT')),
                        'Avg Wake Time': self._format_time(sleep_info.get('sleepEndTimestampGMT')),
                        'Deep Sleep': sleep_info.get('deepSleepSeconds', 0) / 3600,
                        'Light Sleep': sleep_info.get('lightSleepSeconds', 0) / 3600,
                        'REM Sleep': sleep_info.get('remSleepSeconds', 0) / 3600,
                        'Awake': sleep_info.get('awakeSleepSeconds', 0) / 3600
                    }
                    
                    sleep_records.append(record)
                    print(f"  {date_str}: Score {record['Avg Score']}")
                    
            except Exception as e:
                print(f"  {date_str}: No data ({e})")
                continue
                
        df = pd.DataFrame(sleep_records)
        return df
    
    def _format_duration(self, seconds):
        """Convert seconds to '6h 30min' format"""
        if not seconds:
            return None
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}min"
    
    def _format_time(self, timestamp_ms):
        """Convert timestamp to time string"""
        if not timestamp_ms:
            return None
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%H:%M")
    
    def save_to_csv(self, df, filename="sleep_data.csv"):
        """Save DataFrame to CSV"""
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} records to {filename}")


def update_sleep_data(days=30):
    """Main function to fetch and update sleep data"""
    fetcher = GarminSleepFetcher()
    
    try:
        fetcher.authenticate()
        df = fetcher.get_sleep_data(days=days)
        
        if not df.empty:
            fetcher.save_to_csv(df)
            return df
        else:
            print("No sleep data retrieved")
            return None
            
    except Exception as e:
        print(f"Error updating sleep data: {e}")
        return None


if __name__ == "__main__":
    # Test the connection
    print("Garmin Connect Login")
    print("Ensure environment variables: GARMIN_EMAIL and GARMIN_PASSWORD")
    print("Or create a .env file with these credentials\n")
    
    update_sleep_data(days=30)
