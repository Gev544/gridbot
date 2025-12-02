# Binance Futures Grid Bot — BOTH SIDES (Long below, Short above)

**Mode:** Futures-only, delta-balanced grid (long-below / short-above).  
**Exchange:** Binance USDⓈ-M Futures.  
**Leverage:** Uses *effective* 1.2× exposure (orders sized accordingly) while account leverage is set to 1× for safety.

**How it works**
- Places **BUY limits below** the mid (opens long) with a paired **SELL TP** above (reduce-only).
- Places **SELL limits above** the mid (opens short) with a paired **BUY TP** below (reduce-only).
- Keeps the book roughly delta-neutral and harvests chop.
- Basic breakout guard: if price moves beyond `MID ± MAX_RANGE_%`, cancels grid.

> ⚠️ This is a minimal, educational skeleton. Extend with: ADX/ATR filters, liquidation-distance checks, funding tracking, and alerting before going live.
