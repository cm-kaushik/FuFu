from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    balance: float = 0.00
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_row(row: tuple, columns: list) -> "User":
        """Create a User instance from a database row."""
        data = dict(zip(columns, row))
        return User(**data)
