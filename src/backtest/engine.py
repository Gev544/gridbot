from dataclasses import dataclass
import pandas as pd

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

def build_levels(mid: float, levels: int, step_pct: float, tp_pct: float):
    step = step_pct / 100.0
    tp = tp_pct / 100.0
    long_entries = [mid * (1 - i*step) for i in range(1, levels+1)]
    long_tps     = [e * (1 + tp) for e in long_entries]
    short_entries = [mid * (1 + i*step) for i in range(1, levels+1)]
    short_tps     = [e * (1 - tp) for e in short_entries]
    return long_entries, long_tps, short_entries, short_tps

def backtest(df: pd.DataFrame, cfg: BacktestConfig) -> BacktestResult:
    mid = float(df.iloc[0]["close"])
    long_entries, long_tps, short_entries, short_tps = build_levels(mid, cfg.levels, cfg.step_pct, cfg.tp_pct)
    qty = (cfg.order_usdt * cfg.effective_exposure) / mid

    low_guard = mid * (1 - cfg.max_range_pct/100.0)
    high_guard = mid * (1 + cfg.max_range_pct/100.0)

    pnl_long = 0.0
    pnl_short = 0.0
    cycles_long = 0
    cycles_short = 0
    stopped = False

    open_longs = []
    open_shorts = []

    for _, row in df.iterrows():
        low = float(row["low"])
        high = float(row["high"])

        if low < low_guard or high > high_guard:
            stopped = True
            break

        for e, tp in zip(long_entries, long_tps):
            if low <= e:
                open_longs.append(e)
        for e, tp in zip(short_entries, short_tps):
            if high >= e:
                open_shorts.append(e)

        for e, tp in zip(long_entries, long_tps):
            while open_longs and high >= tp:
                ent = open_longs.pop(0)
                pnl_long += qty * (tp - ent)
                cycles_long += 1

        for e, tp in zip(short_entries, short_tps):
            while open_shorts and low <= tp:
                ent = open_shorts.pop(0)
                pnl_short += qty * (ent - tp)
                cycles_short += 1

    total_pnl = pnl_long + pnl_short
    total_cycles = cycles_long + cycles_short
    winrate = (total_cycles / max(total_cycles, 1)) * 100.0

    return BacktestResult(
        cycles_long=cycles_long,
        cycles_short=cycles_short,
        pnl_long=pnl_long,
        pnl_short=pnl_short,
        total_pnl=total_pnl,
        winrate=winrate,
        bars=len(df),
        stopped_by_breakout=stopped
    )
