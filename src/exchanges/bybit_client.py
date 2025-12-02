import logging
from pybit.unified_trading import HTTP

class BybitFutures:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = HTTP(testnet=False, api_key=api_key, api_secret=api_secret)
        self.log = logging.getLogger("gridbot.bybit")

    def get_mark_price(self, symbol: str="BTCUSDT") -> float:
        res = self.session.get_tickers(category="linear", symbol=symbol)
        return float(res["result"]["list"][0]["markPrice"])

    def get_position_qty(self, symbol: str="BTCUSDT") -> float:
        res = self.session.get_positions(category="linear", symbol=symbol)
        for p in res["result"]["list"]:
            if p["symbol"] == symbol:
                return float(p["size"]) if p["side"] == "Sell" else -float(p["size"])
        return 0.0

    def market_order(self, symbol: str, side: str, qty: float, dry_run: bool=True):
        if dry_run:
            self.log.info(f"[DRY] BYBIT {side} {qty} {symbol} (market)")
            return {"orderId": "DRY"}
        return self.session.place_order(category="linear", symbol=symbol, side=side,
                                        orderType="Market", qty=str(qty))

    def close_all(self, symbol: str="BTCUSDT", dry_run: bool=True):
        pos = self.get_position_qty(symbol)
        if abs(pos) > 0:
            side = "Buy" if pos > 0 else "Sell"
            return self.market_order(symbol, side, abs(pos), dry_run=dry_run)
        return {"status":"ok","detail":"no position"}
