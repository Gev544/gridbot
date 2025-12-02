from pydantic import BaseModel, Field
import os

def _to_bool(v: str, default: bool=False) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in {"1","true","yes","on"}

class Settings(BaseModel):
    binance_key: str = Field(default_factory=lambda: os.getenv("BINANCE_API_KEY",""))
    binance_secret: str = Field(default_factory=lambda: os.getenv("BINANCE_API_SECRET",""))
    bybit_key: str = Field(default_factory=lambda: os.getenv("BYBIT_API_KEY",""))
    bybit_secret: str = Field(default_factory=lambda: os.getenv("BYBIT_API_SECRET",""))
    symbol: str = Field(default_factory=lambda: os.getenv("SYMBOL","BTCUSDT"))
    quote: str = Field(default_factory=lambda: os.getenv("QUOTE","USDT"))
    base: str = Field(default_factory=lambda: os.getenv("BASE","BTC"))
    grid_min: float = Field(default_factory=lambda: float(os.getenv("GRID_MIN_PRICE","56000")))
    grid_max: float = Field(default_factory=lambda: float(os.getenv("GRID_MAX_PRICE","62000")))
    grid_levels: int = Field(default_factory=lambda: int(os.getenv("GRID_LEVELS","40")))
    grid_order_size_usdt: float = Field(default_factory=lambda: float(os.getenv("GRID_ORDER_SIZE_USDT","25")))
    hedge_ratio: float = Field(default_factory=lambda: float(os.getenv("HEDGE_RATIO","0.6")))
    session_max_dd_pct: float = Field(default_factory=lambda: float(os.getenv("SESSION_MAX_DD_PCT","3")))
    exit_on_breakout: bool = Field(default_factory=lambda: _to_bool(os.getenv("EXIT_ON_BREAKOUT","true"), True))
    dry_run: bool = Field(default_factory=lambda: _to_bool(os.getenv("DRY_RUN","true"), True))
    auto_grid: bool = Field(default_factory=lambda: _to_bool(os.getenv("AUTO_GRID","false"), False))
    auto_grid_interval: str = Field(default_factory=lambda: os.getenv("AUTO_GRID_INTERVAL","1h"))
    auto_grid_limit: int = Field(default_factory=lambda: int(os.getenv("AUTO_GRID_LIMIT","200")))
    auto_grid_low_pct: float = Field(default_factory=lambda: float(os.getenv("AUTO_GRID_LOW_PCT","0.1")))
    auto_grid_high_pct: float = Field(default_factory=lambda: float(os.getenv("AUTO_GRID_HIGH_PCT","0.9")))

    def validate_range(self):
        if self.grid_min >= self.grid_max:
            raise ValueError("GRID_MIN_PRICE must be < GRID_MAX_PRICE")
        if self.grid_levels < 2:
            raise ValueError("GRID_LEVELS must be >= 2")
        if self.auto_grid_low_pct <= 0 or self.auto_grid_high_pct >= 1 or self.auto_grid_low_pct >= self.auto_grid_high_pct:
            raise ValueError("AUTO_GRID_LOW_PCT must be < AUTO_GRID_HIGH_PCT and within (0,1)")
