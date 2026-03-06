from SmartApi import SmartConnect #or from SmartApi.smartConnect import SmartConnect
import pyotp
from logzero import logger
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY_HISTORICAL_DATA = os.getenv("API_KEY_HISTORICAL_DATA")
username = os.getenv("ANGEL_USERNAME")
pwd = os.getenv("PWD")

smartApi = SmartConnect(API_KEY_HISTORICAL_DATA)

try:
    token = os.getenv("TOKEN")
    totp = pyotp.TOTP(token).now()
except Exception as e:
    logger.error("Invalid Token: The provided token is not valid.")
    raise e

correlation_id = "abcde"
data = smartApi.generateSession(username, pwd, totp)


try:
    historicParam={
        "exchange": "BSE",
        "symboltoken": "24077",
        "interval": "ONE_MINUTE",
        "fromdate": "2026-03-04 09:00", 
        "todate": "2026-03-04 09:16"
    }
   
    print(smartApi.getCandleData(historicParam))
    response = smartApi.getCandleData(historicParam)

    if response['status']:
        formatted_data = []

        for candle in response['data']:
            formatted_data.append({
                "datetime": candle[0],
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5]
            })
        print(formatted_data)
    else:
        print("Error:", response)
except Exception as e:
    logger.exception(f"Historic Api failed: {e}")
