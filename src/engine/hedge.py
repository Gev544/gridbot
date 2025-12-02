import logging
from math import floor

class HedgeManager:
    def __init__(self, bybit, symbol: str, hedge_ratio: float):
        self.bybit = bybit
        self.symbol = symbol
        self.hedge_ratio = hedge_ratio
        self.log = logging.getLogger("gridbot.hedge")

    def sync(self, spot_base_qty: float, lot_size: float, dry_run: bool=True):
        # Target short size = hedge_ratio * spot_qty
        target = self.hedge_ratio * spot_base_qty
        current = -self.bybit.get_position_qty(self.symbol)  # short is positive for us
        diff = target - current
        # Round to lot size; respect contract minimums (avoid Bybit 10001 errors)
        min_contract = 0.01 if "ETH" in self.symbol else 0.001 if "BTC" in self.symbol else max(lot_size, 1e-4)
        if lot_size > 0:
            units = floor(abs(diff)/lot_size) * lot_size
        else:
            units = abs(diff)
        if units < min_contract and abs(diff) > 0:
            units = min_contract  # bump to minimum to actually place the hedge
        side = "Sell" if diff > 0 else "Buy"
        return self.bybit.market_order(self.symbol, side, units, dry_run=dry_run)
