"""
AI Advisor API Router.

Endpoints for AI-powered trading advice.
Works for both individual stocks and custom indexes.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.database.connection import get_db
from app.utils.security import get_current_user
from app.schemas.index_schemas import AIAdviceRequest
from app.services.ai_advisor_service import (
    get_trade_advice,
    get_advice_history,
)
from app.services.news_service import (
    get_stock_news,
    get_sector_news,
)


router = APIRouter()


# ============================================================
# AI ADVICE
# ============================================================

@router.post("/advice")
async def get_advice(
    data: AIAdviceRequest,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """
    Get AI-powered trading advice before a buy/sell.

    Analyzes market conditions, news, price trends,
    and fundamentals to provide a recommendation.
    """

    result = get_trade_advice(
        conn=conn,
        user_id=current_user["user_id"],
        symbol=data.symbol,
        index_id=data.index_id,
        action=data.action,
        amount=data.amount,
        quantity=data.quantity,
    )

    return result


# ============================================================
# ADVICE HISTORY
# ============================================================

@router.get("/history")
async def advice_history(
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Get past AI advisor recommendations."""

    history = get_advice_history(
        conn=conn,
        user_id=current_user["user_id"],
    )

    return {"history": history}


# ============================================================
# NEWS ENDPOINTS
# ============================================================

@router.get("/news/{symbol}")
async def stock_news(
    symbol: str,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Get recent news for a stock."""

    # Get stock name from DB
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT name FROM stocks WHERE symbol = %s",
            (symbol,),
        )
        stock = cursor.fetchone()
    finally:
        cursor.close()

    company_name = stock["name"] if stock else ""

    news = get_stock_news(symbol, company_name)
    return {"news": news}


@router.get("/sector-news/{sector}")
async def sector_news_endpoint(
    sector: str,
    current_user=Depends(get_current_user),
):
    """Get recent news for a sector."""

    news = get_sector_news(sector)
    return {"news": news}
