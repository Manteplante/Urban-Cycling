import pandas as pd
import os

# Clean CSV data by dropping unnecessary columns, converting datetime formats,
# and renaming columns. Also adds primary and foreign keys.

def clean_csv_file(file_path, city=None):
    
    # Extract year and month from filename
    filename = os.path.basename(file_path)
    year, month = os.path.splitext(filename)[0].split('_')
    
    # Read the CSV file
    data = pd.read_csv(file_path)
    
    # Drop unnecessary columns
    columns_to_drop = ['start_station_id', 'start_station_description', 
                       'end_station_id', 'end_station_description']
    data.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    # Convert the datetime columns to the desired format (ISO8601)
    # Use format='ISO8601' to properly handle timestamps with timezone info
    data['started_at'] = pd.to_datetime(data['started_at'], format='ISO8601').dt.strftime('%Y-%m-%d %H:%M:%S')
    data['ended_at'] = pd.to_datetime(data['ended_at'], format='ISO8601').dt.strftime('%Y-%m-%d %H:%M:%S')

    # Rename columns
    data.rename(columns={
        'started_at': 'start_datetime',
        'ended_at': 'stopp_datetime',
        'start_station_name': 'start', 
        'duration': 'seconds', 
        'end_station_name': 'stopp', 
        'start_station_latitude': 'start_ltd',
        'start_station_longitude': 'start_lon', 
        'end_station_latitude': 'end_ltd', 
        'end_station_longitude': 'end_lon'
    }, inplace=True, errors='ignore')
    
    # Add primary and foreign keys
    if city:
        # Ensure consistent capitalization
        city_proper = city.title() if city.upper() in ["OSLO", "BERGEN", "TRONDHEIM"] else city
        data['city_id'] = city_proper  # Primary key based on city
    
    # Add year and month as foreign keys
    data['year'] = year
    data['month'] = month
    
    # Create a unique trip_id as primary key
    city_lower = city.lower() if city else "unknown"
    data['trip_id'] = [f"{city_lower}_{year}_{month}_{i}" for i in range(len(data))]
    
    return data

# Process all CSV files in a directory.
# Clean files and overwrite the originals.

def process_directory(directory_path):
   
    processed_files = []
    
    # Get the city name from the directory path
    city = os.path.basename(directory_path)
    
    # Make case-insensitive check for city names
    valid_cities = ["OSLO", "BERGEN", "TRONDHEIM"]
    
    # Only process if this is a valid city directory (case insensitive)
    if city.upper() in [c.upper() for c in valid_cities]:
        # Get all CSV files in this directory (no subdirectories)
        try:
            files = [f for f in os.listdir(directory_path) if f.endswith('.csv')]
            print(f"Processing {len(files)} CSV files in {city} directory")
            
            for file in files:
                file_path = os.path.join(directory_path, file)
                try:
                    # Clean the file
                    cleaned_df = clean_csv_file(file_path, city)
                    
                    # Save cleaned data back to the original file (overwrite)
                    cleaned_df.to_csv(file_path, index=False)
                    processed_files.append(file_path)
                    print(f"Cleaned and updated: {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
        except Exception as e:
            print(f"Error accessing directory {directory_path}: {str(e)}")
    else:
        print(f"Skipping directory (not a target city folder): {directory_path}")
        print(f"Valid city names (case-insensitive): {', '.join(valid_cities)}")
    
    return processed_files