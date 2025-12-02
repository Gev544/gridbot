from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd

from src.bot.engine.grid import BothSidesGrid, build_both_sides

@dataclass
class BacktestConfig:
    symbol: str
    levels: int
    step_pct: float
    tp_pct: float
    order_usdt: float
    effective_exposure: float
    max_range_pct: float
    funding_bps_8h: float = 0.0  # basis points per 8h (e.g., 1.0 = 0.01%)

@dataclass
class BacktestResult:
    cycles_long: int
    cycles_short: int
    pnl_long: float
    pnl_short: float
    total_pnl: float
    winrate: float
    bars: int
    stopped_by_breakout: bool

@dataclass
class LevelState:
    entry: float
    tp: float
    open: bool = False  # True once entry is filled and TP is resting
    done: bool = False  # True once TP hit; we do not re-arm the level in this simple bot

def _build_states(grid: BothSidesGrid) -> Tuple[List[LevelState], List[LevelState]]:
    longs = [LevelState(entry=e, tp=tp) for e, tp in zip(grid.longs.entries, grid.longs.tps)]
    shorts = [LevelState(entry=e, tp=tp) for e, tp in zip(grid.shorts.entries, grid.shorts.tps)]
    return longs, shorts

def backtest(df: pd.DataFrame, cfg: BacktestConfig) -> BacktestResult:
    # Sort to be safe even if the fetcher returns ordered data
    df = df.sort_values("time").reset_index(drop=True)
    if df.empty:
        raise ValueError(f"No candles to backtest for {cfg.symbol}")

    mid = float(df.iloc[0]["close"])
    grid = build_both_sides(mid, cfg.levels, cfg.step_pct, cfg.tp_pct)
    long_levels, short_levels = _build_states(grid)
    qty = (cfg.order_usdt * cfg.effective_exposure) / mid

    low_guard = mid * (1 - cfg.max_range_pct/100.0)
    high_guard = mid * (1 + cfg.max_range_pct/100.0)

    pnl_long = 0.0
    pnl_short = 0.0
    cycles_long = 0
    cycles_short = 0
    stopped = False

    # Track fills per level so we don't double-count if price sits below/above an entry for many bars
    bars_processed = 0

    for row in df.itertuples(index=False):
        bars_processed += 1
        low = float(row.low)
        high = float(row.high)

        if low < low_guard or high > high_guard:
            stopped = True
            break

        for lvl in long_levels:
            if not lvl.done and not lvl.open and low <= lvl.entry:
                lvl.open = True
        for lvl in short_levels:
            if not lvl.done and not lvl.open and high >= lvl.entry:
                lvl.open = True

        for lvl in long_levels:
            if lvl.open and high >= lvl.tp:
                pnl_long += qty * (lvl.tp - lvl.entry)
                cycles_long += 1
                lvl.open = False
                lvl.done = True

        for lvl in short_levels:
            if lvl.open and low <= lvl.tp:
                pnl_short += qty * (lvl.entry - lvl.tp)
                cycles_short += 1
                lvl.open = False
                lvl.done = True

    total_pnl = pnl_long + pnl_short
    total_cycles = cycles_long + cycles_short
    winrate = 100.0 if total_cycles else 0.0

    return BacktestResult(
        cycles_long=cycles_long,
        cycles_short=cycles_short,
        pnl_long=pnl_long,
        pnl_short=pnl_short,
        total_pnl=total_pnl,
        winrate=winrate,
        bars=bars_processed,
        stopped_by_breakout=stopped
    )
