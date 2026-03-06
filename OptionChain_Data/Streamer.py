import time
import threading
from datetime import datetime
from tabulate import tabulate
from SmartApi.smartWebSocketV2 import SmartWebSocketV2


class AngelOneStreamer:

    def __init__(self, smartApi, api_key, auth_token, feed_token, client_code):

        self.smartApi = smartApi
        self.sws = SmartWebSocketV2(auth_token, api_key, client_code, feed_token)

        self.running = True
        self.live_data = {}
        self.token_map = {}

        self.spot_price = 0
        self.current_atm = 0
        self.expiry_str = ""

        self.api_error_log = "Initializing..."

        self.sws.on_open = self._on_open
        self.sws.on_data = self._on_data

    # ---------------------------------------------------------
    # WebSocket Data Handler
    # ---------------------------------------------------------

    def _on_data(self, wsapp, message):

        if not isinstance(message, dict):
            return

        token = message.get("token")

        if not token:
            return

        if token in self.token_map:

            strike, otype = self.token_map[token]

            ltp = message.get("last_traded_price", 0)
            vol = message.get("volume_trade_for_the_day", 0)
            oi = message.get("open_interest", 0)

            self.live_data[strike][otype].update({

                "ltp": ltp / 100 if ltp else 0,
                "vol": vol,
                "oi": oi

            })

    # ---------------------------------------------------------
    # Fetch Greeks from Angel API
    # ---------------------------------------------------------

    def _fetch_greeks(self):

        if not self.expiry_str:
            return

        try:

            payload = {
                "name": "NIFTY",
                "expirydate": self.expiry_str
            }

            res = self.smartApi.optionGreek(payload)

            if res.get("status") and res.get("data"):

                self.api_error_log = "Greeks OK"

                for item in res["data"]:

                    strike = float(item.get("strikePrice", 0))
                    otype = item.get("optionType")

                    if strike in self.live_data:

                        self.live_data[strike][otype].update({

                            "iv": round(float(item.get("impliedVolatility", 0)), 2),
                            "delta": round(float(item.get("delta", 0)), 3)

                        })

            else:

                self.api_error_log = f"Greek API Error: {res.get('message')}"

        except Exception as e:

            self.api_error_log = f"Greek Exception: {str(e)}"

    # ---------------------------------------------------------
    # Watchdog Loop (refresh chain every 15s)
    # ---------------------------------------------------------

    def _watchdog_loop(self):

        from DataFetcher import AngelDataFetcher

        fetcher = AngelDataFetcher()

        while self.running:

            new_list, new_atm, spot = fetcher.get_dynamic_nifty_chain(self.smartApi)

            if new_list:

                self.spot_price = spot
                self.current_atm = new_atm
                self.expiry_str = new_list[0]["expiry"]

                tokens = []

                for item in new_list:

                    token = str(item["token"])
                    strike = item["strike_val"]

                    otype = "CE" if item["symbol"].endswith("CE") else "PE"

                    self.token_map[token] = (strike, otype)

                    if strike not in self.live_data:

                        self.live_data[strike] = {
                            "CE": self._empty(),
                            "PE": self._empty()
                        }

                    tokens.append(token)

                # Subscribe WebSocket
                self.sws.subscribe(
                    "nifty",
                    3,
                    [{"exchangeType": 2, "tokens": tokens}]
                )

            time.sleep(15)

    # ---------------------------------------------------------
    # Empty data template
    # ---------------------------------------------------------

    def _empty(self):

        return {
            "ltp": 0,
            "vol": 0,
            "oi": 0,
            "iv": 0,
            "delta": 0
        }

    # ---------------------------------------------------------
    # Dashboard display
    # ---------------------------------------------------------

    def _dashboard_loop(self):

        while self.running:

            self._fetch_greeks()

            print("\033c", end="")

            print(
                f"📊 NIFTY OPTION CHAIN | SPOT: {self.spot_price} | "
                f"EXPIRY: {self.expiry_str} | {self.api_error_log}"
            )

            headers = [
                "OI", "VOL", "IV", "DELTA", "LTP (PE)",
                "STRIKE",
                "LTP (CE)", "DELTA", "IV", "VOL", "OI"
            ]

            rows = []

            for strike in sorted(self.live_data.keys()):

                pe = self.live_data[strike]["PE"]
                ce = self.live_data[strike]["CE"]

                strike_label = (
                    f"[{strike}]" if strike == self.current_atm else strike
                )

                rows.append([
                    pe["oi"], pe["vol"], pe["iv"], pe["delta"], pe["ltp"],
                    strike_label,
                    ce["ltp"], ce["delta"], ce["iv"], ce["vol"], ce["oi"]
                ])

            print(tabulate(rows, headers=headers, tablefmt="psql", stralign="center"))

            print(f"\nLast Update: {datetime.now().strftime('%H:%M:%S')}")

            time.sleep(1)

    # ---------------------------------------------------------
    # WebSocket Open Event
    # ---------------------------------------------------------

    def _on_open(self, wsapp):

        threading.Thread(target=self._watchdog_loop, daemon=True).start()
        threading.Thread(target=self._dashboard_loop, daemon=True).start()

    # ---------------------------------------------------------
    # Start streamer
    # ---------------------------------------------------------

    def start(self):

        self.sws.connect()