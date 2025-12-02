import time
from dotenv import load_dotenv
from src.bot.utils.logging import setup_logger
from src.bot.utils.config import Settings
from src.bot.exchange.binance import BinanceUM
from src.bot.engine.grid import build_both_sides

def main():
    load_dotenv()
    log = setup_logger("fgrid")
    cfg = Settings()
    cfg.validate()

    um = BinanceUM(cfg.api_key, cfg.api_secret)
    um.set_isolated(cfg.symbol, cfg.isolated)
    um.set_leverage(cfg.symbol, leverage=1)

    tick, step, min_qty, min_notional = um.exchange_filters(cfg.symbol)

    mid = um.price(cfg.symbol)
    grid = build_both_sides(mid, cfg.grid_levels, cfg.step_pct, cfg.tp_pct)

    notional = cfg.order_usdt * cfg.effective_exposure
    qty = max(notional / mid, min_qty)
    qty = um.round_qty(qty, step, min_qty, min_notional=min_notional, price=mid)

    log.info(f"Start BOTH-SIDES GRID {cfg.symbol} mid={mid:.2f} levels/side={cfg.grid_levels} "
             f"step={cfg.step_pct}% tp={cfg.tp_pct}% qty≈{qty} DRY={cfg.dry_run}")

    um.cancel_all(cfg.symbol, dry=cfg.dry_run)

    placed = 0
    for entry, tp in zip(grid.longs.entries, grid.longs.tps):
        e = um.round_price(entry, tick, side="BUY"); t = um.round_price(tp, tick, side="SELL")
        um.place_limit(cfg.symbol, "BUY", qty, e, reduce_only=False, dry=cfg.dry_run)
        um.place_limit(cfg.symbol, "SELL", qty, t, reduce_only=True, dry=cfg.dry_run)
        placed += 2
    for entry, tp in zip(grid.shorts.entries, grid.shorts.tps):
        e = um.round_price(entry, tick, side="SELL"); t = um.round_price(tp, tick, side="BUY")
        um.place_limit(cfg.symbol, "SELL", qty, e, reduce_only=False, dry=cfg.dry_run)
        um.place_limit(cfg.symbol, "BUY", qty, t, reduce_only=True, dry=cfg.dry_run)
        placed += 2

    low = mid * (1 - cfg.max_range_pct/100.0)
    high = mid * (1 + cfg.max_range_pct/100.0)
    log.info(f"Placed {placed} orders. Breakout guard [{low:.2f}, {high:.2f}]")

    try:
        while True:
            p = um.price(cfg.symbol)
            if p < low or p > high:
                log.warning(f"Breakout {p:.2f} — cancel all")
                um.cancel_all(cfg.symbol, dry=cfg.dry_run)
                break
            time.sleep(5)
    except KeyboardInterrupt:
        log.info("Interrupted. Cancelling...")
        um.cancel_all(cfg.symbol, dry=cfg.dry_run)

if __name__ == "__main__":
    main()
