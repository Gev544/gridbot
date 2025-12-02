from src.engine.hedge import HedgeManager


class DummyBybit:
    def __init__(self, position_qty=0.0):
        self.position_qty = position_qty
        self.orders = []

    def get_position_qty(self, symbol):
        return self.position_qty

    def market_order(self, symbol, side, qty, dry_run=True):
        self.orders.append({"symbol": symbol, "side": side, "qty": qty, "dry_run": dry_run})
        return {"symbol": symbol, "side": side, "qty": qty, "dry_run": dry_run}


def test_no_change_when_diff_smaller_than_lot():
    bybit = DummyBybit(position_qty=0.0)
    hedge = HedgeManager(bybit, symbol="BTCUSDT", hedge_ratio=0.5)

    res = hedge.sync(spot_base_qty=0.0, lot_size=0.1, dry_run=True)

    assert res["detail"] == "no change"
    assert bybit.orders == []


def test_order_is_rounded_down_to_lot_size():
    bybit = DummyBybit(position_qty=0.0)
    hedge = HedgeManager(bybit, symbol="BTCUSDT", hedge_ratio=0.5)

    res = hedge.sync(spot_base_qty=1.23, lot_size=0.1, dry_run=True)

    assert res["qty"] == 0.6
    assert bybit.orders[0]["side"] == "Sell"
