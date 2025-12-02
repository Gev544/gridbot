# src/backtest/fetch_ratio.py
import pandas as pd
import numpy as np
from pandas.api.types import is_datetime64_any_dtype, is_datetime64tz_dtype
from src.backtest.fetch import fetch_futures_klines

def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or len(df) == 0:
        raise ValueError("Empty dataframe from fetch_futures_klines")
    df = df.copy()

    # Find time column
    time_candidates = ["open_time","openTime","timestamp","time","t","open_time_ms"]
    ts_col = next((c for c in time_candidates if c in df.columns), None)
    if ts_col is None:
        if df.index.name in time_candidates:
            df = df.reset_index()
            ts_col = df.columns[0]
        else:
            # fallback: first column if it looks time-ish
            first = df.columns[0]
            if "time" in first.lower():
                ts_col = first
            else:
                raise KeyError("No suitable time column found in klines dataframe")

    ts = df[ts_col]

    # Normalize to integer milliseconds in column "ts"
    if is_datetime64tz_dtype(ts) or (is_datetime64_any_dtype(ts) and getattr(ts.dt, 'tz', None) is not None):
        # timezone-aware -> drop tz then cast to ns -> ms
        df["ts"] = (ts.dt.tz_convert(None).astype("int64") // 1_000_000).astype("int64")
    elif is_datetime64_any_dtype(ts):
        # tz-naive datetime64[ns]
        df["ts"] = (ts.astype("int64") // 1_000_000).astype("int64")
    else:
        # numeric/strings -> coerce, then detect sec vs ms
        ts_num = pd.to_numeric(ts, errors="coerce")
        if ts_num.dropna().median() < 10_000_000_000:  # looks like seconds
            ts_num = (ts_num * 1000).astype("int64")
        df["ts"] = ts_num.astype("int64")

    # Pick OHLC
    def pick(*cands):
        for c in cands:
            if c in df.columns:
                return c
            lc = c.lower()
            for col in df.columns:
                if col.lower() == lc:
                    return col
        return None

    close_col = pick("close","c")
    high_col  = pick("high","h") or close_col
    low_col   = pick("low","l")  or close_col
    if close_col is None:
        raise KeyError("close column not found in klines dataframe")

    out = pd.DataFrame({
        "ts":   df["ts"].values,
        "close": pd.to_numeric(df[close_col], errors="coerce").values,
        "high":  pd.to_numeric(df[high_col],  errors="coerce").values,
        "low":   pd.to_numeric(df[low_col],   errors="coerce").values,
    }).dropna(subset=["ts","close"]).drop_duplicates(subset=["ts"]).sort_values("ts").reset_index(drop=True)
    return out

def fetch_ratio_klines(start, end, interval="1m"):
    btc = _normalize(fetch_futures_klines("BTCUSDT", interval, start, end))
    eth = _normalize(fetch_futures_klines("ETHUSDT", interval, start, end))
    df = pd.merge(btc, eth, on="ts", how="inner", suffixes=("_btc","_eth"))
    ratio = df["close_btc"] / df["close_eth"]
    return pd.DataFrame({
        "open_time": df["ts"],  # what your engine expects
        "close": ratio,
        "low":   ratio,
        "high":  ratio,
    })

