import os
from pydantic import BaseModel, Field

def _b(v, d=False):
    if v is None:
        return d
    return str(v).strip().lower() in {"1","true","yes","on"}

class Settings(BaseModel):
    api_key: str = Field(default_factory=lambda: os.getenv("BINANCE_API_KEY",""))
    api_secret: str = Field(default_factory=lambda: os.getenv("BINANCE_API_SECRET",""))
    symbol: str = Field(default_factory=lambda: os.getenv("SYMBOL","BTCUSDT"))
    grid_levels: int = Field(default_factory=lambda: int(os.getenv("GRID_LEVELS","20")))
    step_pct: float = Field(default_factory=lambda: float(os.getenv("STEP_PCT","0.25")))
    tp_pct: float = Field(default_factory=lambda: float(os.getenv("TP_PCT","0.20")))
    order_usdt: float = Field(default_factory=lambda: float(os.getenv("ORDER_USDT","20")))
    max_range_pct: float = Field(default_factory=lambda: float(os.getenv("MAX_RANGE_PCT","4.0")))
    effective_exposure: float = Field(default_factory=lambda: float(os.getenv("EFFECTIVE_EXPOSURE","1.2")))
    isolated: bool = Field(default_factory=lambda: _b(os.getenv("ISOLATED","true"), True))
    dry_run: bool = Field(default_factory=lambda: _b(os.getenv("DRY_RUN","true"), True))

    def validate(self):
        if self.grid_levels < 2:
            raise ValueError("GRID_LEVELS must be >= 2")
        if self.step_pct <= 0:
            raise ValueError("STEP_PCT must be > 0")
        if self.tp_pct <= 0:
            raise ValueError("TP_PCT must be > 0")
