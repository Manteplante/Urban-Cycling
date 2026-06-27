import pandas as pd
from pathlib import Path

SILVER = Path("../02_data/02_silver")
GOLD = Path("../02_data/03_gold")
GOLD.mkdir(exist_ok=True)

# Aggregate trips by city, month, day

def create_gold_trips_summary():
    
    all_data = []
    for city in ["Oslo", "Bergen", "Trondheim"]:
        city_files = (SILVER / city).glob("*.csv")
        for file in city_files:
            df = pd.read_csv(file)
            df['city'] = city
            all_data.append(df)
    
    combined = pd.concat(all_data, ignore_index=True)
    combined['start_datetime'] = pd.to_datetime(combined['start_datetime'])
    
    # Aggregations
    gold_trips = combined.groupby([
        'city', 
        pd.Grouper(key='start_datetime', freq='D')
    ]).agg({
        'trip_id': 'count',
        'seconds': ['mean', 'median', 'sum']
    }).reset_index()
    
    gold_trips.columns = ['city', 'date', 'total_trips', 'avg_duration', 'median_duration', 'total_duration']
    gold_trips.to_csv(GOLD / "trips_summary.csv", index=False)
    

# Create station master table with metrics

def create_gold_stations():
    
    # Combine all unique stations with their locations and trip counts
    # ... your logic here
    pass

if __name__ == "__main__":
    create_gold_trips_summary()
    create_gold_stations()