import pandas as pd
import requests


class AngelDataFetcher:

    def __init__(self):

        self.scrip_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

        self.df = None

        self._load_scrip_master()

    def _load_scrip_master(self):

        try:

            data = requests.get(self.scrip_url).json()

            df = pd.DataFrame(data)

            df["strike"] = pd.to_numeric(df["strike"], errors="coerce") / 100

            df = df[df["exch_seg"] == "NFO"]

            df = df[df["name"] == "NIFTY"]

            df = df.copy()

            df["expiry_dt"] = pd.to_datetime(df["expiry"], errors="coerce")

            self.df = df

        except Exception as e:

            print(f"Scrip Master Load Error: {e}")

    def get_dynamic_nifty_chain(self, smartApi, range_strikes=10):

        try:

            ltp_data = smartApi.ltpData("NSE", "NIFTY", "99926000")

            spot = ltp_data["data"]["ltp"]

            atm_strike = round(spot / 50) * 50

            nearest_expiry = self.df["expiry_dt"].min()

            expiry_str = nearest_expiry.strftime("%d%b%Y").upper()

            chain = self.df[self.df["expiry_dt"] == nearest_expiry]

            chain = chain[
                (chain["strike"] >= atm_strike - range_strikes * 50)
                & (chain["strike"] <= atm_strike + range_strikes * 50)
            ]

            token_list = []

            for _, row in chain.iterrows():

                token_list.append({
                    "token": row["token"],
                    "symbol": row["symbol"],
                    "strike_val": row["strike"],
                    "expiry": expiry_str
                })

            return token_list, atm_strike, spot

        except Exception as e:

            print(f"Chain Fetch Error: {e}")

            return [], 0, 0