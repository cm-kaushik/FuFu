from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Transaction:
    id: int
    user_id: int
    stock_id: Optional[int]
    type: str  # BUY, SELL, DEPOSIT
    quantity: int = 0
    price_per_share: float = 0.00
    total_amount: float = 0.00
    created_at: Optional[datetime] = None

    @staticmethod
    def from_row(row: tuple, columns: list) -> "Transaction":
        data = dict(zip(columns, row))
        return Transaction(**data)
