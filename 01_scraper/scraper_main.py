import os
import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests
from enabler import fetch_html, parse_html
from csv_fetcher import fetch_csv_files
from csv_cleaner import clean_csv_file, process_directory # clean_csv_file imported even though not used


# Calculate the previous month and year

def get_previous_month():
    
    today = datetime.datetime.now()
    first_of_month = datetime.datetime(today.year, today.month, 1)
    last_of_prev_month = first_of_month - datetime.timedelta(days=1)
    
    # Return year and month name
    return str(last_of_prev_month.year), last_of_prev_month.strftime('%B').lower()

# Scrape CSV files for a specific month

def scrape_csv_for_month(base_url, target_year, target_month):
    print(f"Looking for data for {target_month} {target_year}...")

    # Fetch HTML and parse it
    html_content = fetch_html(base_url)
    soup = parse_html(html_content)
    all_csv_files = fetch_csv_files(soup)

    # Download ALL files (no filtering)
    return all_csv_files

# Save CSV files to disk

def save_to_file(csv_files, folder_path):
    
    saved_files = []
    for csv_file in csv_files:
        url = csv_file['URL']
        month_year = csv_file['MonthYear'].replace(' ', '_').replace('Oppdatert_daglig', '').strip()
        # Split month and year to reformat the filename
        month, year = month_year.split('_')
        file_name = f"{year}_{month}.csv"
        file_path = os.path.join(folder_path, file_name)
        
        # Check if file already exists
        if os.path.exists(file_path):
            print(f"File already exists: {file_path} - Skipping download")
            saved_files.append(file_path)
            continue
            
        response = requests.get(url)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Saved CSV file to {file_path}")
        saved_files.append(file_path)
    return saved_files

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def resolve_env_path(*keys, default_relative):
    for key in keys:
        value = os.getenv(key)
        if value and value.strip():
            candidate = Path(value.strip()).expanduser()
            if not candidate.is_absolute():
                candidate = PROJECT_ROOT / candidate
            return str(candidate.resolve())

    fallback = Path(default_relative)
    if not fallback.is_absolute():
        fallback = PROJECT_ROOT / fallback
    return str(fallback.resolve())

# Process the monthly update for the previous month

def process_monthly_update():
    # Get the target month and year (previous month)
    target_year, target_month = get_previous_month()
    print(f"Running monthly update for {target_month} {target_year}")
    
    base_urls = {
        "Oslo": "https://oslobysykkel.no/apne-data/historisk",
        "Bergen": "https://bergenbysykkel.no/apne-data/historisk",
        "Trondheim": "https://trondheimbysykkel.no/apne-data/historisk"
    }

    # Load folder paths from environment variables
    folder_paths = {
        "Oslo": resolve_env_path("BRONZE_OSLO_PATH", "OSLO", default_relative="02_data/bronze/oslo"),
        "Bergen": resolve_env_path("BRONZE_BERGEN_PATH", "BERGEN", default_relative="02_data/bronze/bergen"),
        "Trondheim": resolve_env_path("BRONZE_TRONDHEIM_PATH", "TRONDHEIM", default_relative="02_data/bronze/trondheim"),
    }
    
    # Check that all paths exist, create if not
    for city, path in folder_paths.items():
        os.makedirs(path, exist_ok=True)
    
    # Scrape and save for each city
    all_saved_files = []
    for city, url in base_urls.items():
        print(f"\n===== Scraping data for {city} ({target_month} {target_year}) =====")
        csv_files = scrape_csv_for_month(url, target_year, target_month)
        if csv_files:
            saved_files = save_to_file(csv_files, folder_paths[city])
            all_saved_files.extend(saved_files)
            print(f"Completed scraping for {city}. Downloaded {len(saved_files)} files.")
        else:
            print(f"No files to download for {city}.")
    
    # Clean all directories with the new files
    print("\n===== Starting data cleaning process =====")
    cleaned_directories = []
    for city, path in folder_paths.items():
        print(f"\nCleaning files in {city} directory: {path}")
        try:
            # Process the entire directory, which handles city name extraction properly
            cleaned_files = process_directory(path)
            if cleaned_files:
                print(f"Successfully cleaned {len(cleaned_files)} files in {city} directory")
                cleaned_directories.append(city)
            else:
                print(f"No files were cleaned in {city} directory")
        except Exception as e:
            print(f"Error cleaning {city} directory: {str(e)}")
    
    print(f"\nMonthly update complete!")
    print(f"- Downloaded: {len(all_saved_files)} files")
    print(f"- Cleaned directories: {', '.join(cleaned_directories)}")
    
    return all_saved_files

if __name__ == "__main__":
    process_monthly_update()