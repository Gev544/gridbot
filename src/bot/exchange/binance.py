import logging
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from typing import Optional, Tuple

from binance.um_futures import UMFutures

class BinanceUM:
    def __init__(self, key: str, secret: str):
        self.log = logging.getLogger("fgrid.binance")
        self.client = UMFutures(key=key, secret=secret)

    def price(self, symbol: str) -> float:
        t = self.client.ticker_price(symbol)
        return float(t["price"])

    def exchange_filters(self, symbol: str) -> Tuple[float, float, float, Optional[float]]:
        info = self.client.exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                fs = {f["filterType"]: f for f in s["filters"]}
                tick = float(fs["PRICE_FILTER"]["tickSize"])
                step = float(fs["LOT_SIZE"]["stepSize"])
                min_qty = float(fs["LOT_SIZE"]["minQty"])
                min_notional = None
                if "MIN_NOTIONAL" in fs:
                    # Futures MIN_NOTIONAL is sometimes present; guard so small orders do not get rejected
                    min_notional = float(fs["MIN_NOTIONAL"]["notional"])
                return tick, step, min_qty, min_notional
        raise RuntimeError("Symbol not found in exchange_info")

    @staticmethod
    def _quantize(value: float, step: float, rounding) -> float:
        step_dec = Decimal(str(step))
        return float(
            (Decimal(str(value)) / step_dec).to_integral_value(rounding=rounding) * step_dec
        )

    def round_price(self, price: float, tick: float, side: str) -> float:
        """Round price to Binance tick; SELL rounds up for better TP, BUY rounds down for better entry."""
        rounding = ROUND_DOWN if side.upper() == "BUY" else ROUND_UP
        return self._quantize(price, tick, rounding)

    def round_qty(
        self,
        qty: float,
        step: float,
        min_qty: float,
        min_notional: Optional[float] = None,
        price: Optional[float] = None,
    ) -> float:
        """Round quantity to lot size and respect minQty/minNotional."""
        q = self._quantize(qty, step, ROUND_DOWN)
        q = max(q, min_qty)
        if min_notional and price:
            min_by_notional = Decimal(str(min_notional)) / Decimal(str(price))
            q = max(q, float(self._quantize(min_by_notional, step, ROUND_UP)))
        return q

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
