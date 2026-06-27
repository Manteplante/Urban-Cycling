import time

def fetch_csv_files(soup):
    csv_files = []
    print("Fetching CSV files...")

    month_year_divs = soup.find_all('div', class_='sc-AxhUy dsJejt')

    # Extract 10 files at a time
    for index, div in enumerate(month_year_divs):
        month_year = div.text.strip()

    for div in month_year_divs:
        month_year = div.text.strip()

        # Ignore entries with "Oppdatert daglig" until test is over. Change then to daily updates instead of ignoring. 
        if "Oppdatert daglig" in month_year:
            print(f"Ignored entry: {month_year}")
            continue

        print(f"Found month and year: {month_year}")

        # Find the CSV button corresponding to the month and year
        csv_button = div.find_next('button', {'itemprop': 'contentUrl', 'content': lambda x: x and x.endswith('.csv')})
        if csv_button:
            csv_url = csv_button['content']
            print(f"Found CSV URL: {csv_url}")

            csv_files.append({'MonthYear': month_year, 'URL': csv_url})
        
        #Add a 1-second delay after every 10 files
        if (index + 1) % 10 == 0:
            print("Pausing for 1 second to avoid overloading...")
            time.sleep(2)

############## Dummy implementation ################
        # Dummy implementation to simulate fetching data
        
        # Fetch HTML (dummy implementation here)
        #html_content = requests.get(url).text
        #print(f"Fetched data from {url}")

        # Save dummy data as an example (replace with your actual logic)
        #file_path = os.path.join(folder_paths[city], f"{city}_data.txt")
        #with open(file_path, "w") as f:
            #f.write(f"Dummy data for {city} from {url}")

        #print(f"Data saved to {file_path}")


    return csv_files