from SmartApi import SmartConnect
import pyotp
from logzero import logger
from dotenv import load_dotenv
import os
from AngleOneDataFetch_function import AngelDataFetcher

load_dotenv()

api_key = os.getenv("API_KEY")
username = os.getenv("ANGEL_USERNAME")
pwd = os.getenv("PWD")

smartApi = SmartConnect(api_key)

try:
    token = os.getenv("TOKEN")
    totp = pyotp.TOTP(token).now()
except Exception as e:
    logger.error("Invalid Token")
    raise e

data = smartApi.generateSession(username, pwd, totp)

authToken = data['data']['jwtToken']
feedToken = smartApi.getfeedToken()

# pass token to constructor
fetcher = AngelDataFetcher(feedToken)

fetcher.fetch_nifty_options()
fetcher.ETFList()