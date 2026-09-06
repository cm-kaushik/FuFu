from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TradeRequest(BaseModel):
    symbol: str
    quantity: int
    pin: str


class AddFundsRequest(BaseModel):
    amount: float
    pin: str


class TransactionResponse(BaseModel):
    id: int
    type: str
    stock_symbol: Optional[str] = None
    stock_name: Optional[str] = None
    quantity: int
    price_per_share: float
    total_amount: float
    created_at: str


class TradeResponse(BaseModel):
    success: bool
    message: str
    transaction: Optional[TransactionResponse] = None
    new_balance: Optional[float] = None
