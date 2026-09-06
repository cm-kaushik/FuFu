from dataclasses import dataclass
from typing import Optional


@dataclass
class Holding:
    id: int
    user_id: int
    stock_id: int
    quantity: int = 0
    avg_buy_price: float = 0.00

    @staticmethod
    def from_row(row: tuple, columns: list) -> "Holding":
        data = dict(zip(columns, row))
        return Holding(**data)
