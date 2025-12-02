import argparse
from src.backtest.engine import BacktestConfig, backtest
from src.backtest.fetch_ratio import fetch_ratio_klines

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--interval", default="1m")
    ap.add_argument("--levels", type=int)
    ap.add_argument("--step-pct", type=float)
    ap.add_argument("--tp-pct", type=float)
    ap.add_argument("--max-range-pct", type=float)
    ap.add_argument("--order-usdt", type=float)
    ap.add_argument("--effective-exposure", type=float, default=1.0)
    a = ap.parse_args()

    cfg = BacktestConfig(
        symbol="BTCETH_RATIO",
        levels=a.levels,
        step_pct=a.step_pct,
        tp_pct=a.tp_pct,
        order_usdt=a.order_usdt,
        effective_exposure=a.effective_exposure,
        max_range_pct=a.max_range_pct,
    )

    df = fetch_ratio_klines(a.start, a.end, a.interval)
    out = backtest(df, cfg)

    print("=== RATIO GRID BACKTEST ===")
    print(out)

if __name__ == "__main__":
    main()

