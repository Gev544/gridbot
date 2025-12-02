import math, logging
from binance.um_futures import UMFutures

class BinanceUM:
    def __init__(self, key: str, secret: str):
        self.log = logging.getLogger("fgrid.binance")
        self.client = UMFutures(key=key, secret=secret)

    def price(self, symbol: str) -> float:
        t = self.client.ticker_price(symbol)
        return float(t["price"])

    def exchange_filters(self, symbol: str):
        info = self.client.exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                fs = {f["filterType"]: f for f in s["filters"]}
                tick = float(fs["PRICE_FILTER"]["tickSize"])
                step = float(fs["LOT_SIZE"]["stepSize"])
                min_qty = float(fs["LOT_SIZE"]["minQty"])
                return tick, step, min_qty
        raise RuntimeError("Symbol not found in exchange_info")

    def round_price(self, p: float, tick: float) -> float:
        return math.floor(p / tick) * tick

    def round_qty(self, q: float, step: float, min_qty: float) -> float:
        q = math.floor(q / step) * step
        return max(q, min_qty)

    def set_isolated(self, symbol: str, isolated: bool=True):
        try:
            self.client.change_margin_type(symbol=symbol, marginType="ISOLATED" if isolated else "CROSSED")
        except Exception as e:
            self.log.info(f"margin_type: {e}")

    def set_leverage(self, symbol: str, leverage: int=1):
        try:
            self.client.change_leverage(symbol=symbol, leverage=leverage)
        except Exception as e:
            self.log.info(f"leverage: {e}")

    def cancel_all(self, symbol: str, dry: bool=True):
        if dry:
            self.log.info(f"[DRY] cancel all {symbol}")
            return []
        return self.client.cancel_open_orders(symbol=symbol)

    def place_limit(self, symbol: str, side: str, qty: float, price: float, reduce_only: bool=False, dry: bool=True):
        if dry:
            self.log.info(f"[DRY] LIMIT {side} {qty} {symbol} @ {price} reduceOnly={reduce_only}")
            return {"orderId":"DRY"}
        return self.client.new_order(symbol=symbol, side=side, type="LIMIT", quantity=str(qty),
                                     price=f"{price:.8f}", timeInForce="GTC",
                                     reduceOnly="true" if reduce_only else "false",
                                     newOrderRespType="RESULT")

    def get_open_orders(self, symbol: str):
        return self.client.get_open_orders(symbol=symbol)
