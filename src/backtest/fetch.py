import pandas as pd
from binance.client import Client

def fetch_futures_klines(symbol: str, interval: str, start_str: str, end_str: str) -> pd.DataFrame:
    """Fetch USD-M futures klines from Binance (public). Returns a cleaned DataFrame."""
    cli = Client(api_key=None, api_secret=None)
    raw = cli.futures_historical_klines(symbol=symbol, interval=interval, start_str=start_str, end_str=end_str)
    if not raw:
        raise ValueError(f"No klines returned for {symbol} {interval} {start_str}->{end_str}")
    cols = ["open_time","open","high","low","close","volume","close_time","quote_asset_volume",
            "number_of_trades","taker_buy_base","taker_buy_quote","ignore"]
    df = pd.DataFrame(raw, columns=cols)
    for c in ["open","high","low","close","volume","quote_asset_volume","taker_buy_base","taker_buy_quote"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    return df[["open_time","open","high","low","close","volume","close_time"]].rename(columns={"open_time":"time"})
