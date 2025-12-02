# Hedged Grid Bot — Binance Spot + Bybit Futures

Runs a spot grid on Binance and auto-hedges short on Bybit USDT-PERP. 
Optimized for choppy ranges: buy low/sell high on spot, keep delta neutral with a futures hedge.

## Quickstart
- Python 3.10+ recommended. `./run.sh` will create `.venv`, install deps, and copy `.env.sample` if missing.
- Fill `.env` with your API keys and grid settings before turning off `DRY_RUN`.
- Run: `bash run.sh`

## Configuration
- Edit `.env` (based on `.env.sample`): symbol, grid range/levels, order size, hedge ratio, and `DRY_RUN`.
- Safety: `EXIT_ON_BREAKOUT=true` cancels the grid if price exits the band. Drawdown guard is stubbed; extend before live use.
- Testnet: Bybit client defaults to mainnet; adjust `bybit_client.py` if you need testnet.

## Testing
- Dev deps: `python -m pip install -r requirements-dev.txt` (after activating `.venv`).
- Run tests: `pytest`
