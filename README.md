# Futures Grid — Unified Project (Live Bot + Backtester)

This repository includes **both**:
1) **Live BOTH-SIDES Futures Grid Bot** for **Binance USDⓈ-M** (long below / short above, reduce-only TPs, breakout guard).  
2) **Offline Backtester** that downloads Binance Futures klines and simulates the same grid logic (touch-to-fill).

> **Mode:** Futures-only, both-sides grid (delta-balanced).  
> **Leverage:** Account leverage fixed to 1×; *effective* 1.2× exposure is achieved via order sizing.

---

## Quick Start — Live Bot (Binance Futures)
```bash
cp .env.sample .env
# Edit .env and set your Binance Futures API key/secret
# Keep DRY_RUN=true for a smoke test

./run_bot.sh
# When ready for live trading, set DRY_RUN=false in .env and run again
```

What the bot does:
- Places BUY entries below mid (opens long) + paired SELL reduce-only TPs above.
- Places SELL entries above mid (opens short) + paired BUY reduce-only TPs below.
- Cancels entire grid if price exits `MID ± MAX_RANGE_PCT` (breakout guard).
- Uses ISOLATED margin and **1×** leverage (safer; 1.2× is simulated by order sizing).

> **Do NOT enable Hedge Mode** on Binance for this bot. Use default One-Way mode.

---

## Quick Start — Backtester (Offline)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt

# Example: BTCUSDT, 1m candles, Jan→Jun 2024
python -m src.backtest.run_backtest   --symbol BTCUSDT   --interval 1m   --start 2024-01-01   --end 2024-06-01   --levels 20   --step-pct 0.25   --tp-pct 0.20   --order-usdt 20   --max-range-pct 4.0   --effective-exposure 1.2
```

The backtester prints:
- PnL long/short/total
- Completed cycles
- Winrate (per cycle)
- Whether the session was stopped by the breakout guard

> **Note:** This is a simplified simulator (touch = fill, no partial fills, no slippage).
> Extend with funding, liquidation-distance, ADX/ATR filters for realism.

---

## Files
- `.env.sample` — config for live bot  
- `run_bot.sh` — creates venv, installs deps, runs bot  
- `run_backtest.sh` — helper to run a simple backtest demo  
- `src/bot/*` — live bot code  
- `src/backtest/*` — backtester code  
- `requirements.txt` — shared dependencies

---

## Safety Notes
- Start in **DRY_RUN=true** to validate orders/filters.
- Keep **One-way Mode** on Binance (no Hedge Mode).
- Uses **ISOLATED** margin and **1×** leverage by default.
- This is a baseline framework; add ADX/ATR filters, liquidation tracking, and alerts for production.
