from dataclasses import dataclass
import numpy as np

@dataclass
class GridPlan:
    buy_levels: list
    sell_levels: list
    step: float

def build_grid(min_price: float, max_price: float, levels: int, mid: float) -> GridPlan:
    prices = np.linspace(min_price, max_price, levels)
    # split around mid price
    buys = [p for p in prices if p < mid]
    sells = [p for p in prices if p > mid]
    step = (max_price - min_price) / (levels - 1)
    return GridPlan(buy_levels=buys[::-1], sell_levels=sells, step=step)


def auto_range_from_series(series: list, low_pct: float, high_pct: float) -> tuple:
    """Compute price band using percentiles over a series of prices."""
    if not series:
        raise ValueError("Price series is empty")
    low = float(np.quantile(series, low_pct))
    high = float(np.quantile(series, high_pct))
    if low == high:
        high = low * 1.01
    return low, high
