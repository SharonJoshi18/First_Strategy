import requests
import pandas as pd

class AngelDataFetcher:
    def __init__(self, feed_token):
        self.feed_token = feed_token

    def fetch_nifty_options(self):
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        data = requests.get(url).json()

        df = pd.DataFrame(data)

        nifty_options = df[
            (df['name'] == 'NIFTY') &
            (df['exch_seg'] == 'NFO') &
            (df['instrumenttype'] == 'OPTIDX')
        ]

        print(nifty_options)
        # print(nifty_options[['symbol','token','expiry','strike']])