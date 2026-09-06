"""
Pydantic schemas for Custom Index operations.

Covers:
- Index creation / update
- Investment (buy/sell units)
- AI advisor request/response
- Rebalance
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================
# INDEX CRUD
# ============================================================

class IndexCreate(BaseModel):
    """Request schema for creating a custom index."""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    sector: Optional[str] = None
    theme: Optional[str] = None
    stock_symbols: List[str] = Field(..., min_length=2)
    top_n: int = Field(..., ge=1)
    weight_strategy: str = Field(default="EQUAL")
    custom_weights: Optional[List[float]] = None


class IndexUpdate(BaseModel):
    """Request schema for updating a custom index."""
    name: Optional[str] = None
    description: Optional[str] = None
    stock_symbols: Optional[List[str]] = None
    top_n: Optional[int] = None
    weight_strategy: Optional[str] = None
    custom_weights: Optional[List[float]] = None


class ConstituentResponse(BaseModel):
    """A single stock in the index universe."""
    symbol: str
    name: str
    sector: Optional[str] = None
    current_price: Optional[float] = None
    change_percent: Optional[float] = None
    market_cap: Optional[float] = None
    weight_percent: Optional[float] = None
    is_active_in_index: bool = True
    rank_position: Optional[int] = None


class IndexResponse(BaseModel):
    """Response schema for a custom index."""
    id: int
    name: str
    description: Optional[str] = None
    sector: Optional[str] = None
    theme: Optional[str] = None
    universe_size: int
    top_n: int
    weight_strategy: str
    rebalance_frequency: str = "SEMI_ANNUAL"
    is_active: bool = True
    nav: Optional[float] = 100.0
    nav_change: Optional[float] = 0.0
    nav_change_percent: Optional[float] = 0.0
    total_invested: Optional[float] = 0.0
    current_value: Optional[float] = 0.0
    pnl: Optional[float] = 0.0
    pnl_percent: Optional[float] = 0.0
    constituents_count: int = 0
    active_stocks_count: int = 0
    created_at: Optional[str] = None


class IndexDetailResponse(BaseModel):
    """Detailed index view with constituents."""
    index: IndexResponse
    constituents: List[ConstituentResponse]
    performance_history: Optional[List[dict]] = None


# ============================================================
# INVESTMENT
# ============================================================

class InvestRequest(BaseModel):
    """Request to invest in a custom index."""
    amount: float = Field(..., gt=0)
    pin: str = Field(..., min_length=4, max_length=4)


class RedeemRequest(BaseModel):
    """Request to redeem (sell) from a custom index."""
    amount: Optional[float] = None
    redeem_all: bool = False
    pin: str = Field(..., min_length=4, max_length=4)


class InvestmentResponse(BaseModel):
    """Investment status response."""
    success: bool
    message: str
    investment: Optional[dict] = None
    new_balance: Optional[float] = None
    allocations: Optional[List[dict]] = None


# ============================================================
# AI ADVISOR
# ============================================================

class AIAdviceRequest(BaseModel):
    """Request for AI trading advice."""
    symbol: Optional[str] = None
    index_id: Optional[int] = None
    action: str = Field(..., pattern="^(BUY|SELL)$")
    amount: Optional[float] = None
    quantity: Optional[int] = None


class AIAdviceResponse(BaseModel):
    """AI advisor recommendation."""
    recommendation: str
    sentiment: str
    confidence: float
    reasoning: str
    market_context: str
    news_summary: str
    risk_assessment: str
    key_factors: List[str]
    price_analysis: Optional[dict] = None


# ============================================================
# REBALANCE
# ============================================================

class RebalanceRequest(BaseModel):
    """Manual rebalance trigger."""
    pin: str = Field(..., min_length=4, max_length=4)


class RebalanceResponse(BaseModel):
    """Rebalance result."""
    success: bool
    message: str
    changes: Optional[List[dict]] = None
    new_weights: Optional[List[dict]] = None
