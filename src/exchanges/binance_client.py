import asyncio
import logging
import math
from binance import AsyncClient, BinanceSocketManager
from binance.client import Client as SpotSync

class BinanceSpot:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self._client = None
        self._spot_sync = None
        self._filters = {}
        self.log = logging.getLogger("gridbot.binance")

    async def connect(self):
        # Async client for market data; sync client for order/cancel
        self._client = await AsyncClient.create(self.api_key, self.api_secret)
        self._spot_sync = SpotSync(self.api_key, self.api_secret)

    async def close(self):
        if self._client:
            await self._client.close_connection()

    async def get_price(self, symbol: str) -> float:
        # Use REST to keep it simple and robust
        ticker = await self._client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    def load_symbol_filters(self, symbol: str):
        info = self._spot_sync.get_symbol_info(symbol=symbol)
        filters = {}
        for f in info["filters"]:
            if f["filterType"] == "PRICE_FILTER":
                filters["tickSize"] = float(f["tickSize"])
            elif f["filterType"] == "LOT_SIZE":
                filters["stepSize"] = float(f["stepSize"])
                filters["minQty"] = float(f["minQty"])
            elif f["filterType"] == "MIN_NOTIONAL":
                filters["minNotional"] = float(f["minNotional"])
        self._filters[symbol] = filters

    def _ensure_filters(self, symbol: str):
        if symbol not in self._filters:
            self.load_symbol_filters(symbol)

    def _round_price(self, symbol: str, price: float) -> float:
        self._ensure_filters(symbol)
        tick = self._filters[symbol].get("tickSize", 0.01)
        return math.floor(price / tick) * tick

    def _round_qty(self, symbol: str, qty: float) -> float:
        self._ensure_filters(symbol)
        step = self._filters[symbol].get("stepSize", 0.001)
        min_qty = self._filters[symbol].get("minQty", step)
        qty = math.floor(qty / step) * step
        if qty < min_qty:
            qty = min_qty
        return qty

    def _ensure_notional(self, symbol: str, qty: float, price: float) -> float:
        self._ensure_filters(symbol)
        min_notional = self._filters[symbol].get("minNotional")
        step = self._filters[symbol].get("stepSize", 0.001)
        if min_notional and qty * price < min_notional:
            qty = math.ceil(min_notional / price / step) * step
        return qty

    async def get_klines(self, symbol: str, interval: str="1h", limit: int=200):
        # Returns raw kline rows as provided by Binance
        return await self._client.get_klines(symbol=symbol, interval=interval, limit=limit)

    def place_limit_buy(self, symbol: str, quantity: float, price: float, dry_run: bool=True):
        price = self._round_price(symbol, price)
        quantity = self._round_qty(symbol, quantity)
        quantity = self._ensure_notional(symbol, quantity, price)
        if dry_run:
            self.log.info(f"[DRY] BINANCE BUY {symbol} qty={quantity} @ {price}")
            return {"orderId":"DRY"}
        return self._spot_sync.create_order(symbol=symbol, side="BUY", type="LIMIT", timeInForce="GTC",
                                            quantity=quantity, price=f"{price:.8f}")

    def place_limit_sell(self, symbol: str, quantity: float, price: float, dry_run: bool=True):
        price = self._round_price(symbol, price)
        quantity = self._round_qty(symbol, quantity)
        quantity = self._ensure_notional(symbol, quantity, price)
        if dry_run:
            self.log.info(f"[DRY] BINANCE SELL {symbol} qty={quantity} @ {price}")
            return {"orderId":"DRY"}
        return self._spot_sync.create_order(symbol=symbol, side="SELL", type="LIMIT", timeInForce="GTC",
                                            quantity=quantity, price=f"{price:.8f}")

    async def cancel_all(self, symbol: str, dry_run: bool=True):
        if dry_run:
            self.log.info(f"[DRY] BINANCE Cancel all for {symbol}")
            return []
        orders = await self._client.get_open_orders(symbol=symbol)
        results = []
        for o in orders:
            try:
                res = await self._client.cancel_order(symbol=symbol, orderId=o["orderId"])
                results.append(res)
            except Exception as exc:
                self.log.warning(f"Failed to cancel order {o.get('orderId')} for {symbol}: {exc}")
        return results

    def get_open_orders(self, symbol: str):
        return self._spot_sync.get_open_orders(symbol=symbol)

    def get_balances(self):
        acc = self._spot_sync.get_account()
        return {b["asset"]: float(b["free"]) + float(b["locked"]) for b in acc["balances"]}
