import argparse
from src.backtest.fetch import fetch_futures_klines
from src.backtest.engine import BacktestConfig, backtest

def parse_args():
    ap = argparse.ArgumentParser(description="Both-sides Binance Futures grid backtester")
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--interval", default="1m")
    ap.add_argument("--start", required=True, help="e.g., 2024-01-01")
    ap.add_argument("--end", required=True, help="e.g., 2024-06-01")
    ap.add_argument("--levels", type=int, default=20)
    ap.add_argument("--step-pct", type=float, default=0.25)
    ap.add_argument("--tp-pct", type=float, default=0.20)
    ap.add_argument("--order-usdt", type=float, default=20.0)
    ap.add_argument("--max-range-pct", type=float, default=4.0)
    ap.add_argument("--effective-exposure", type=float, default=1.2)
    ap.add_argument("--funding-bps-8h", type=float, default=0.0)
    return ap.parse_args()

def main():
    args = parse_args()
    df = fetch_futures_klines(args.symbol, args.interval, args.start, args.end)
    cfg = BacktestConfig(
        symbol=args.symbol,
        levels=args.levels,
        step_pct=args.step_pct,
        tp_pct=args.tp_pct,
        order_usdt=args.order_usdt,
        effective_exposure=args.effective_exposure,
        max_range_pct=args.max_range_pct,
        funding_bps_8h=args.funding_bps_8h,
    )
    res = backtest(df, cfg)
    print("=== BOTH-SIDES GRID BACKTEST ===")
    print(f"Symbol:            {args.symbol}")
    print(f"Interval:          {args.interval}")
    print(f"Period:            {args.start} -> {args.end}  (bars={res.bars})")
    print(f"Levels/side:       {args.levels}")
    print(f"Step % / TP %:     {args.step_pct} / {args.tp_pct}")
    print(f"Order USDT:        {args.order_usdt}  (effective x{args.effective_exposure})")
    print(f"Max range %:       {args.max_range_pct}")
    print(f"Cycles (long/short): {res.cycles_long} / {res.cycles_short}")
    print(f"PnL     (long/short): {res.pnl_long:.4f} / {res.pnl_short:.4f} USDT")
    print(f"TOTAL PnL:            {res.total_pnl:.4f} USDT")
    print(f"Winrate (cycles):     {res.winrate:.2f}%")
    print(f"Stopped by breakout:  {res.stopped_by_breakout}")

if __name__ == "__main__":
    main()
