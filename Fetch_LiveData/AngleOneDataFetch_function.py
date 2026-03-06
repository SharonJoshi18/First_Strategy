import requests
import pandas as pd
import json
import os

class AngelDataFetcher:
    def __init__(self, feed_token=None):
        # We keep feed_token as an argument to match your main.py call
        self.feed_token = feed_token
        self.url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

    def ETFList(self):
        # Precise list of liquid NSE ETFs for your requested categories
        targets = {
            "GOLD": ["GOLDBEES", "SETFGOLD", "GOLDSHARE"],
            "SILVER": ["SILVERBEES", "MAHESILVER", "SILVERIETF"],
            "BANK": ["BANKBEES", "SETFBNK50", "KOTAKBANK"],
            "LARGECAP": ["NIFTYBEES", "SETFNIF50"],
            "MIDCAP": ["MID150BEES", "MAHMIDCAP", "MIDCAPETF"],
            "SMALLCAP": ["SMLCAPBEES", "SMALLCAP"]
        }
        
        # Flatten the list for filtering
        all_target_symbols = [sym for sublist in targets.values() for sym in sublist]

        try:
            print("Fetching and filtering NSE ETF Master list...")
            response = requests.get(self.url, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame(data)

            # Strict Filtering: 
            # 1. Must be NSE 
            # 2. Symbol must be in our target list (case-insensitive)
            # 3. Only Equity/ETF segment (usually 'NSE')
            filtered_df = df[
                (df['exch_seg'] == 'NSE') & 
                (df['symbol'].str.replace("-EQ", "").isin(all_target_symbols))
            ]

            # Directory and File Setup
            folder_name = "nse_data"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                
            file_path = os.path.join(folder_name, "ETF.py")

            # Format the data for the .py file
            filtered_list = filtered_df.to_dict(orient='records')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Auto-generated NSE ETF List\n")
                f.write("stock_data = ")
                json.dump(filtered_list, f, indent=4)
                
            print(f"✔ Successfully saved {len(filtered_list)} ETFs to {file_path}")
            
            # Optional: Display categories found
            for entry in filtered_list:
                print(f"Found: {entry['symbol']} (Token: {entry['token']})")

        except Exception as e:
            print(f"❌ Error in ETFList: {e}")

    def fetch_nifty_options(self):
        """Maintains compatibility with your existing main.py calls"""
        try:
            response = requests.get(self.url, timeout=60)
            df = pd.DataFrame(response.json())
            nifty_options = df[
                (df['name'] == 'NIFTY') &
                (df['exch_seg'] == 'NFO') &
                (df['instrumenttype'] == 'OPTIDX')
            ]
            print(f"Fetched {len(nifty_options)} Nifty Options records.")
            return nifty_options
        except Exception as e:
            print(f"Error fetching Nifty Options: {e}")