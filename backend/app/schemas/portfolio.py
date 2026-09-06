from pydantic import BaseModel
from typing import Optional, List


# ============================================================
# HOLDING RESPONSE
# ============================================================

class HoldingResponse(BaseModel):
    """
    Represents a single stock holding in the user's portfolio.
    """

    stock_symbol: str
    stock_name: str
    sector: Optional[str] = None

    quantity: int

    avg_buy_price: float
    current_price: float

    invested_value: float
    current_value: float

    pnl: float
    pnl_percent: float


# ============================================================
# PORTFOLIO SUMMARY
# ============================================================

class PortfolioSummary(BaseModel):
    """
    Represents the overall portfolio summary.
    """

    balance: float

    total_invested: float
    portfolio_value: float

    total_pnl: float
    total_pnl_percent: float

    holdings_count: int


# ============================================================
# COMPLETE PORTFOLIO RESPONSE
# ============================================================

class PortfolioResponse(BaseModel):
    """
    Complete portfolio response containing:

    1. Portfolio summary
    2. Individual stock holdings
    """

    summary: PortfolioSummary

    holdings: List[HoldingResponse]