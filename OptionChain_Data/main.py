import os
import pyotp
import re
from logzero import logger
from dotenv import load_dotenv
from SmartApi import SmartConnect
from Streamer import AngelOneStreamer

# Load environment variables
load_dotenv()


def run_trading_app():

    API_KEY = os.getenv("API_KEY_MARKET_DATA")
    USER_ID = os.getenv("ANGEL_USERNAME")
    PASSWD = os.getenv("PWD")
    TOTP_SECRET = os.getenv("TOKEN")

    # Validate environment variables
    if not all([API_KEY, USER_ID, PASSWD, TOTP_SECRET]):
        logger.error("❌ Setup Error: Missing environment variables in .env file.")
        return

    smartApi = SmartConnect(api_key=API_KEY)

    try:

        # Clean TOTP Secret
        clean_totp = re.sub(r"[^A-Z2-7]", "", TOTP_SECRET.upper())
        totp_code = pyotp.TOTP(clean_totp).now()

        # Generate session
        session = smartApi.generateSession(USER_ID, PASSWD, totp_code)

        if not session.get("status"):
            logger.error(f"❌ Login Failed: {session.get('message')}")
            return

        # Safe extraction
        auth_token = session.get("data", {}).get("jwtToken")

        if not auth_token:
            logger.error("❌ JWT Token missing in login response.")
            return

        feed_token = smartApi.getfeedToken()

        # Safe login time extraction
        login_time = session.get("data", {}).get("lastLoginTime", "N/A")

        print("✔ Login Successful")
        print(f"✔ User: {USER_ID}")
        print(f"✔ Login Time: {login_time}")
        print("-" * 50)

        # Start Streamer
        streamer = AngelOneStreamer(
            smartApi=smartApi,
            api_key=API_KEY,
            auth_token=auth_token,
            feed_token=feed_token,
            client_code=USER_ID
        )

        streamer.start()

    except Exception as e:
        logger.error(f"❌ Critical Error: {str(e)}")


if __name__ == "__main__":
    run_trading_app()