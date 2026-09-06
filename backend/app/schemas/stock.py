from pydantic import BaseModel
from typing import Optional, List


class StockInfo(BaseModel):
    symbol: str
    name: str
    sector: Optional[str] = None
    exchange: str = "NSE"
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    open_price: Optional[float] = None


class StockHistoryPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockSearchResult(BaseModel):
    symbol: str
    name: str
    sector: Optional[str] = None
    exchange: str = "NSE"
    current_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
