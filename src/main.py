import asyncio, os, math, logging
from dotenv import load_dotenv
from src.utils.config import Settings
from src.utils.logging import setup_logger
from src.exchanges.binance_client import BinanceSpot
from src.exchanges.bybit_client import BybitFutures
from src.engine.grid import build_grid, auto_range_from_series
from src.engine.hedge import HedgeManager

async def run():
    load_dotenv()
    log = setup_logger()
    cfg = Settings()

    log.info("Starting Hedged Grid Bot (Binance Spot + Bybit Futures)")
    log.info(f"Symbol={cfg.symbol} Range=({cfg.grid_min}, {cfg.grid_max}) Levels={cfg.grid_levels} OrderUSD={cfg.grid_order_size_usdt} DRY_RUN={cfg.dry_run}")

    # Clients
    binance = BinanceSpot(cfg.binance_key, cfg.binance_secret)
    await binance.connect()
    binance.load_symbol_filters(cfg.symbol)
    bybit = BybitFutures(cfg.bybit_key, cfg.bybit_secret)

    try:
        # Auto-grid: pull recent prices to set band
        if cfg.auto_grid:
            klines = await binance.get_klines(cfg.symbol, interval=cfg.auto_grid_interval, limit=cfg.auto_grid_limit)
            closes = [float(k[4]) for k in klines]
            cfg.grid_min, cfg.grid_max = auto_range_from_series(closes, cfg.auto_grid_low_pct, cfg.auto_grid_high_pct)
            log.info(f"Auto grid from {cfg.auto_grid_limit}x{cfg.auto_grid_interval} closes: min={cfg.grid_min:.2f}, max={cfg.grid_max:.2f}")

        cfg.validate_range()

        # Get mid price
        mid = await binance.get_price(cfg.symbol)
        grid = build_grid(cfg.grid_min, cfg.grid_max, cfg.grid_levels, mid)

        # Determine quantity per order based on USDT size, rounded to exchange filters
        filters = binance.get_filters(cfg.symbol)
        lot_step = filters.get("stepSize", 0.0001 if "BTC" in cfg.symbol else 0.001)
        min_qty = filters.get("minQty", lot_step)
        qty_per_order = cfg.grid_order_size_usdt / mid
        qty_per_order = math.floor(qty_per_order / lot_step) * lot_step
        if qty_per_order < min_qty:
            qty_per_order = min_qty
        lot = lot_step
        log.info(f"Mid price: {mid:.2f}. Grid step ~ {grid.step:.2f}. Qty/order ≈ {qty_per_order}")

        # Cancel any leftovers
        await binance.cancel_all(cfg.symbol, dry_run=cfg.dry_run)

        # Get balances once before placing orders to respect available base for sells
        balances = binance.get_balances()
        base_qty = float(balances.get(cfg.base, 0.0))

        # Place initial ladder
        placed = 0
        buy_levels = grid.buy_levels[: len(grid.buy_levels)//2]
        quote_qty = float(balances.get(cfg.quote, 0.0))
        max_buys = math.floor(quote_qty / cfg.grid_order_size_usdt) if cfg.grid_order_size_usdt > 0 else 0
        if max_buys < len(buy_levels):
            log.warning(f"Not enough {cfg.quote} to place all buy orders. Have {quote_qty}, each buy ≈ {cfg.grid_order_size_usdt} {cfg.quote}. Placing {max_buys}/{len(buy_levels)} buys.")
        for p in buy_levels[: max_buys]:
            binance.place_limit_buy(cfg.symbol, qty_per_order, p, dry_run=cfg.dry_run)
            placed += 1

        sell_levels = grid.sell_levels[: len(grid.sell_levels)//2]
        max_sells = math.floor(base_qty / qty_per_order) if qty_per_order > 0 else 0
        if max_sells < len(sell_levels):
            log.warning(f"Not enough {cfg.base} to place all sell orders. Have {base_qty}, each sell qty {qty_per_order}. Placing {max_sells}/{len(sell_levels)} sells.")
        for p in sell_levels[: max_sells]:
            binance.place_limit_sell(cfg.symbol, qty_per_order, p, dry_run=cfg.dry_run)
            placed += 1

        log.info(f"Placed {placed} initial grid orders (buys + sells within balance).")

        # Hedge based on current base balance (may have reduced sells)
        balances = binance.get_balances()
        base_qty = float(balances.get(cfg.base, 0.0))
        hedge = HedgeManager(bybit, cfg.symbol, cfg.hedge_ratio)
        hedge.sync(base_qty, lot, dry_run=cfg.dry_run)

        log.info("""RUNNING LOOP:
- Monitors price and exit conditions
- Rebalances hedge against spot base inventory
- (Simplified) — converts fills monitoring into periodic sync
Press Ctrl+C to stop.
""")
        # Simple supervisor loop (polling)
        while True:
            price = await binance.get_price(cfg.symbol)
            if cfg.exit_on_breakout and (price < cfg.grid_min*0.98 or price > cfg.grid_max*1.02):
                log.warning(f"Breakout detected @ {price:.2f}. Exiting session...")
                await binance.cancel_all(cfg.symbol, dry_run=cfg.dry_run)
                # NOTE: For safety, we do NOT market-close inventory automatically in this skeleton.
                # User can extend: market sell base and close hedge here.
                break

            # re-read balances and sync hedge
            balances = binance.get_balances()
            base_qty = float(balances.get(cfg.base, 0.0))
            hedge.sync(base_qty, lot, dry_run=cfg.dry_run)
            await asyncio.sleep(5)

    finally:
        await binance.close()
        log.info("Stopped.")

if __name__ == "__main__":
    asyncio.run(run())
