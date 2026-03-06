import os
import importlib.util
import time
import signal
import threading
import queue
import pandas as pd
from datetime import datetime
from SmartApi.smartWebSocketV2 import SmartWebSocketV2

class AngelOneStreamer:
    def __init__(self, api_key, auth_token, feed_token, client_code):
        # Initialize WebSocket V2
        self.sws = SmartWebSocketV2(auth_token, api_key, client_code, feed_token)
        
        self.running = True
        
        # 1. SETUP TARGET FOLDER
        self.target_folder = "DataStored"
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder)
            print(f"📁 Created directory: {self.target_folder}")
        
        # Maps for multi-stock handling
        self.queues = {}      
        self.stock_names = {} 
        self.latest_data = {} 

        # Callbacks
        self.sws.on_open = self._on_open
        self.sws.on_data = self._on_data
        self.sws.on_error = self._on_error
        self.sws.on_close = self._on_close

        # Handle Ctrl+C
        signal.signal(signal.SIGINT, self._interrupt_handler)

    def _on_open(self, wsapp):
        print("✔ WebSocket Connected.")
        try:
            # Load stock metadata from ETF.py
            file_path = os.path.join("nse_data", "ETF.py")
            spec = importlib.util.spec_from_file_location("ETF", file_path)
            etf_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(etf_module)
            
            subscription_tokens = []

            # 2. DYNAMIC THREAD CREATION PER ETF ENTRY
            for stock in etf_module.stock_data:
                token = str(stock['token']) 
                name = stock['name']
                
                self.stock_names[token] = name
                self.queues[token] = queue.Queue()
                self.latest_data[token] = {"ltp": 0.0, "time": "--"}
                subscription_tokens.append(token)
                
                # Start a dedicated worker thread for every ETF in the list
                t = threading.Thread(target=self._data_processor, args=(token,), daemon=True)
                t.start()
                # Debug log to verify all threads start
                print(f"🧵 Worker initialized for {name} (File will be in /{self.target_folder})")

            print(f"🎯 Total Threads Active: {len(subscription_tokens)}")

            # Subscribe to all tokens in Mode 3 (Depth)
            token_list = [{"exchangeType": 1, "tokens": subscription_tokens}]
            self.sws.subscribe("depth_stream_v2", 3, token_list)
            
            # Start dashboard
            threading.Thread(target=self._refresh_dashboard, daemon=True).start()
            
        except Exception as e:
            print(f"❌ Setup Error: {e}")

    def _on_data(self, wsapp, message):
        if isinstance(message, dict):
            token = str(message.get('token'))
            if token in self.queues:
                self.queues[token].put(message)

    def _data_processor(self, token):
        stock_name = self.stock_names[token]
        # 3. SAVE TO DATASTORED FOLDER
        full_path = os.path.join(self.target_folder, f"{stock_name}_Ticks.csv")
        
        while self.running:
            try:
                message = self.queues[token].get(timeout=1)
                
                buys = message.get('best_5_buy_data') or []
                sells = message.get('best_5_sell_data') or []
                
                if buys and sells:
                    ltp = float(message.get('last_traded_price', 0) / 100)
                    now = datetime.now()
                    
                    self.latest_data[token] = {
                        "ltp": ltp, 
                        "time": now.strftime('%H:%M:%S')
                    }

                    row = {
                        "date": now.strftime('%Y-%m-%d'),
                        "time": now.strftime('%H:%M:%S.%f'),
                        "ltp": ltp
                    }
                    
                    for i in range(5):
                        row[f"b_p_{i}"] = float(buys[i]['price']/100)
                        row[f"b_q_{i}"] = int(buys[i]['quantity'])
                        row[f"s_p_{i}"] = float(sells[i]['price']/100)
                        row[f"s_q_{i}"] = int(sells[i]['quantity'])

                    # Thread-safe write to its own file
                    df = pd.DataFrame([row])
                    header_needed = not os.path.exists(full_path)
                    df.to_csv(full_path, mode='a', header=header_needed, index=False)

                self.queues[token].task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def _refresh_dashboard(self):
        """Dashboard to show all stocks simultaneously."""
        while self.running:
            print("\033c", end="") # Clear screen
            print(f"📈 LIVE FEED | Folder: ./{self.target_folder} | {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 70)
            print(f"{'STOCK NAME':<15} | {'PRICE':<10} | {'QUEUE':<8} | {'LAST TICK'}")
            print("-" * 70)
            
            for token, name in self.stock_names.items():
                data = self.latest_data.get(token, {})
                q_size = self.queues[token].qsize()
                ltp = data.get('ltp', 0.0)
                l_time = data.get('time', '--')
                
                print(f"{name:<15} | {ltp:<10.2f} | {q_size:<8} | {l_time}")
            
            print("=" * 70)
            print("Press Ctrl+C to terminate safely.")
            time.sleep(1)

    def _on_error(self, wsapp, error):
        if self.running:
            print(f"\n❗ WebSocket Error: {error}")

    def _on_close(self, wsapp):
        if self.running:
            print("\n🛑 WebSocket Connection Closed.")

    def _interrupt_handler(self, signum, frame):
        self.running = False
        print("\n\n👋 Stopping threads and exiting...")
        os._exit(0) 

    def start(self):
        self.sws.connect()