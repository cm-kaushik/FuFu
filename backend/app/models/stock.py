from dataclasses import dataclass
from typing import Optional


@dataclass
class Stock:
    id: int
    symbol: str
    name: str
    sector: Optional[str] = None
    exchange: str = "NSE"

    @staticmethod
    def from_row(row: tuple, columns: list) -> "Stock":
        data = dict(zip(columns, row))
        return Stock(**data)
