import os
import importlib.util
import time
import signal
import sys
from SmartApi.smartWebSocketV2 import SmartWebSocketV2

class AngelOneStreamer:
    def __init__(self, api_key, auth_token, feed_token, client_code):
        self.sws = SmartWebSocketV2(auth_token, api_key, client_code, feed_token)
        
        # Setup signal handling for graceful exit (Ctrl+C)
        signal.signal(signal.SIGINT, self._graceful_exit)
        signal.signal(signal.SIGTERM, self._graceful_exit)

        self.sws.on_open = self._on_open
        self.sws.on_data = self._on_data
        self.sws.on_error = self._on_error
        self.sws.on_close = self._on_close

    def _on_open(self, wsapp):
        print("✔ WebSocket Connected.")
        try:
            # Load your filtered stock file
            file_path = os.path.join("nse_data", "ETF.py")
            spec = importlib.util.spec_from_file_location("ETF", file_path)
            etf_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(etf_module)
            
            token = etf_module.stock_data[0]['token']
            print(f"🎯 Monitoring Full Data for Token: {token}")

            # Mode 2 = Quote (LTP + Bid/Ask + Volume)
            # Mode 3 = Snapquote (5 Depth)
            correlation_id = "full_data_test"
            subscription_list = [{"exchangeType": 1, "tokens": [token]}]
            self.sws.subscribe(correlation_id, 2, subscription_list)
            
        except Exception as e:
            print(f"❌ Selection Error: {e}")

    def _on_data(self, wsapp, message):
        # In Mode 2, the message structure changes to include bid/ask
        try:
            # Note: Fields names might vary slightly depending on SDK version
            # Common fields: ltp, best_bid_price, best_ask_price, last_traded_quantity
            ltp = message.get('last_traded_price', 0) / 100
            bid = message.get('best_bid_price', 0) / 100
            ask = message.get('best_ask_price', 0) / 100
            qty = message.get('last_traded_quantity', 0)
            
            print(f"🕒 {time.strftime('%H:%M:%S')} | LTP: {ltp:.2f} | Bid: {bid:.2f} | Ask: {ask:.2f} | Qty: {qty}")
        except Exception as e:
            print(f"Tick Parsing Error: {e}")

    def _on_error(self, wsapp, error):
        print(f"❗ Error: {error}")

    def _on_close(self, wsapp):
        print("🛑 WebSocket Connection Closed.")

    def _graceful_exit(self, signum, frame):
        """This function runs when you stop the script"""
        print("\n👋 Shutdown signal received. Cleaning up...")
        try:
            self.sws.close_connection() # Closes the socket properly
        except:
            pass
        sys.exit(0)

    def start(self):
        self.sws.connect()