import asyncio
from binance import AsyncClient, BinanceSocketManager
from binance.spot import Spot as SpotSync
import logging

class BinanceSpot:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self._client = None
        self._spot_sync = None
        self.log = logging.getLogger("gridbot.binance")

    async def connect(self):
        self._client = await AsyncClient.create(self.api_key, self.api_secret)
        self._spot_sync = SpotSync(key=self.api_key, secret=self.api_secret)

    async def close(self):
        if self._client:
            await self._client.close_connection()

    async def get_price(self, symbol: str) -> float:
        # Use REST to keep it simple and robust
        ticker = await self._client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    async def get_klines(self, symbol: str, interval: str="1h", limit: int=200):
        # Returns raw kline rows as provided by Binance
        return await self._client.get_klines(symbol=symbol, interval=interval, limit=limit)

    def place_limit_buy(self, symbol: str, quantity: float, price: float, dry_run: bool=True):
        if dry_run:
            self.log.info(f"[DRY] BINANCE BUY {symbol} qty={quantity} @ {price}")
            return {"orderId":"DRY"}
        return self._spot_sync.new_order(symbol=symbol, side="BUY", type="LIMIT", timeInForce="GTC",
                                         quantity=quantity, price=f"{price:.8f}")

    def place_limit_sell(self, symbol: str, quantity: float, price: float, dry_run: bool=True):
        if dry_run:
            self.log.info(f"[DRY] BINANCE SELL {symbol} qty={quantity} @ {price}")
            return {"orderId":"DRY"}
        return self._spot_sync.new_order(symbol=symbol, side="SELL", type="LIMIT", timeInForce="GTC",
                                         quantity=quantity, price=f"{price:.8f}")

    def cancel_all(self, symbol: str, dry_run: bool=True):
        if dry_run:
            self.log.info(f"[DRY] BINANCE Cancel all for {symbol}")
            return []
        return self._spot_sync.cancel_open_orders(symbol=symbol)

    def get_open_orders(self, symbol: str):
        return self._spot_sync.get_open_orders(symbol=symbol)

    def get_balances(self):
        acc = self._spot_sync.account()
        return {b["asset"]: float(b["free"]) + float(b["locked"]) for b in acc["balances"]}
