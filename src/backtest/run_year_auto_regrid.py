# src/backtest/run_year_auto_regrid.py
import argparse
import pandas as pd
from src.backtest.fetch import fetch_futures_klines
from src.backtest.engine import BacktestConfig, backtest

def sessionize(df: pd.DataFrame, cfg: BacktestConfig):
    i = 0
    total_long = total_short = 0.0
    cycles_l = cycles_s = 0
    sessions = 0

    while i < len(df):
        # Run one session from i → end
        slice_df = df.iloc[i:].reset_index(drop=True)
        res = backtest(slice_df, cfg)
        sessions += 1
        total_long += res.pnl_long
        total_short += res.pnl_short
        cycles_l += res.cycles_long
        cycles_s += res.cycles_short

        if not res.stopped_by_breakout:
            break  # reached end with no breakout

        # Find breakout bar relative to this slice's mid/guards
        mid = float(slice_df.iloc[0]["close"])
        low_guard  = mid * (1 - cfg.max_range_pct/100.0)
        high_guard = mid * (1 + cfg.max_range_pct/100.0)

        j = 0
        while j < len(slice_df):
            low = float(slice_df.iloc[j]["low"])
            high = float(slice_df.iloc[j]["high"])
            if low < low_guard or high > high_guard:
                j += 1  # advance past breakout bar
                break
            j += 1

        if j <= 0:
            j = 1  # safety
        i += j   # start next session after the breakout

    return {
        "sessions": sessions,
        "cycles_long": cycles_l,
        "cycles_short": cycles_s,
        "pnl_long": total_long,
        "pnl_short": total_short,
        "total_pnl": total_long + total_short,
    }

def parse_args():
    ap = argparse.ArgumentParser(description="Year backtest with auto-regrid sessions")
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--interval", default="1m")
    ap.add_argument("--start", default="2025-01-01")
    ap.add_argument("--end", default="2025-12-31")
    ap.add_argument("--levels", type=int, default=20)
    ap.add_argument("--step-pct", type=float, default=0.25)
    ap.add_argument("--tp-pct", type=float, default=0.20)
    ap.add_argument("--order-usdt", type=float, default=20.0)
    ap.add_argument("--max-range-pct", type=float, default=12.0)
    ap.add_argument("--effective-exposure", type=float, default=1.2)
    return ap.parse_args()

def main():
    a = parse_args()
    df = fetch_futures_klines(a.symbol, a.interval, a.start, a.end)
    cfg = BacktestConfig(
        symbol=a.symbol,
        levels=a.levels,
        step_pct=a.step_pct,
        tp_pct=a.tp_pct,
        order_usdt=a.order_usdt,
        effective_exposure=a.effective_exposure,
        max_range_pct=a.max_range_pct,
    )
    out = sessionize(df, cfg)
    print("=== YEAR AUTO-REGRID BACKTEST ===")
    print(f"Symbol: {a.symbol}  Period: {a.start} -> {a.end}  Interval: {a.interval}")
    print(f"Levels: {a.levels}  Step/TP: {a.step_pct}/{a.tp_pct}  Range: ±{a.max_range_pct}%")
    print(f"Order USDT: {a.order_usdt}  Eff. exposure: x{a.effective_exposure}")
    print(f"Sessions: {out['sessions']}")
    print(f"Cycles (L/S): {out['cycles_long']} / {out['cycles_short']}")
    print(f"PnL     (L/S): {out['pnl_long']:.4f} / {out['pnl_short']:.4f} USDT")
    print(f"TOTAL PnL:     {out['total_pnl']:.4f} USDT")

if __name__ == "__main__":
    main()

