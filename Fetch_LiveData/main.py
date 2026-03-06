# from SmartApi import SmartConnect
# import pyotp
# from logzero import logger
# from dotenv import load_dotenv
# import os
# from AngleOneDataFetch_function import AngelDataFetcher

# from AngelOneWebSocket import AngelOneStreamer

# load_dotenv()

# API_KEY_HISTORICAL_DATA = os.getenv("API_KEY_mHISTORICAL_DATA")
# API_KEY_MARKET_DATA = os.getenv("API_KEY_MARKET_DATA")
# username = os.getenv("ANGEL_USERNAME")
# pwd = os.getenv("PWD")

# smartApi_Historical = SmartConnect(API_KEY_HISTORICAL_DATA)

# try:
#     token = os.getenv("TOKEN")
#     totp = pyotp.TOTP(token).now()
# except Exception as e:
#     logger.error("Invalid Token")
#     raise e

# data = smartApi_Historical.generateSession(username, pwd, totp)

# authToken = data['data']['jwtToken']
# feedToken = smartApi_Historical.getfeedToken()

# # pass token to constructor
# fetcher = AngelDataFetcher(feedToken)

# fetcher.fetch_nifty_options()
# fetcher.ETFList()

# fetcher = AngelDataFetcher(feedToken)
# fetcher.fetch_nifty_options()
# fetcher.ETFList()

# # We pass the existing credentials from the session we just created
# streamer = AngelOneStreamer(
#     api_key=API_KEY_MARKET_DATA,
#     auth_token=authToken,
#     feed_token=feedToken,
#     client_code=username
# )

# print("Starting live tick data...")
# streamer.start()

import os
import pyotp
import re
from logzero import logger
from dotenv import load_dotenv
from SmartApi import SmartConnect

from AngleOneDataFetch_function import AngelDataFetcher
from AngelOneWebSocket import AngelOneStreamer

load_dotenv()
HIST_KEY = os.getenv("API_KEY_HISTORICAL_DATA")
MRKT_KEY = os.getenv("API_KEY_MARKET_DATA")
USER_ID  = os.getenv("ANGEL_USERNAME")
PASSWORD = os.getenv("PWD")
TOTP_STR = os.getenv("TOKEN")

smartApi = SmartConnect(api_key=HIST_KEY)

try:
    # Sanitizing TOTP_STR to prevent Base32 errors
    clean_token = re.sub(r'[^a-zA-Z2-7]', '', TOTP_STR).upper()
    totp = pyotp.TOTP(clean_token).now()
    
    session_data = smartApi.generateSession(USER_ID, PASSWORD, totp)
    
    if not session_data.get('status'):
        raise Exception(session_data.get('message'))

    authToken = session_data['data']['jwtToken']
    feedToken = smartApi.getfeedToken()
    
    print(f"✔ Login Successful: {USER_ID}")
except Exception as e:
    logger.error(f"Login Failed: {e}")
    os._exit(1)

print("Fetching initial data...")
fetcher = AngelDataFetcher(feedToken)
fetcher.ETFList()  
print("Initial data fetch complete. Starting live tick data...")


streamer = AngelOneStreamer(
    api_key=MRKT_KEY,
    auth_token=authToken,
    feed_token=feedToken,
    client_code=USER_ID
)

streamer.start()