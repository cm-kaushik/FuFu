from fastapi import APIRouter, Depends
from app.database.connection import get_db
from app.utils.security import get_current_user
from app.services.portfolio_service import (
    get_full_portfolio,
    get_portfolio_summary,
    get_user_holdings,
)

router = APIRouter()


@router.get("")
async def get_portfolio(
    current_user=Depends(get_current_user),
    conn=Depends(get_db)
):
    """Get full portfolio with holdings and summary."""

    return get_full_portfolio(
        conn,
        current_user["user_id"]
    )

@router.get("/summary")
async def get_summary(current_user=Depends(get_current_user), conn=Depends(get_db)):
    """Get portfolio summary only."""
    return get_portfolio_summary(conn, current_user["user_id"])
