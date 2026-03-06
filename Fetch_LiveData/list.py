import requests
import json
import os

def fetch_specific_instruments():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    # The specific names you are looking for
    target_names = ["MID150CASE", "NIFTYBEES", "SMALL250"]
    
    try:
        print("Fetching data and filtering for specific instruments...")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Filter: keep only if the 'name' is in our target list
        # We use .upper() to ensure the match isn't missed due to case sensitivity
        filtered_list = [
            item for item in data 
            if str(item.get("name")).upper() in target_names
        ]

        # Directory and File Setup
        folder_name = "nse_data"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
        file_path = os.path.join(folder_name, "ETF.py")

        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("stock_data = ")
            json.dump(filtered_list, f, indent=4)
            
        print(f"Success! Found {len(filtered_list)} matching records.")
        print(f"Saved to: {file_path}")
        
        # Print results to console for confirmation
        for entry in filtered_list:
            print(f"Found: {entry['name']} | Token: {entry['token']} | Exch: {entry['exch_seg']}")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    fetch_specific_instruments()