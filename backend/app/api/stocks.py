from fastapi import APIRouter, Depends, HTTPException, Query

from app.database.connection import get_db
from app.services.yfinance_service import (
    get_basic_stock_price,
    get_stock_price,
    get_stock_history,
)
from app.utils.security import get_current_user


router = APIRouter()


# ============================================================
# SEARCH STOCKS
# ============================================================

@router.get("/search")
async def search_stocks(
    q: str = Query(
        "",
        description="Search query"
    ),
    conn=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Search stocks by symbol or name.

    Search results use BASIC price data so that
    searching does not trigger unnecessary 52-week
    Yahoo requests.
    """

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        if q:

            search_term = f"%{q}%"

            cursor.execute(
                """
                SELECT
                    symbol,
                    name,
                    sector,
                    exchange
                FROM stocks
                WHERE symbol LIKE %s
                   OR name LIKE %s
                ORDER BY name
                LIMIT 20
                """,
                (
                    search_term,
                    search_term
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    symbol,
                    name,
                    sector,
                    exchange
                FROM stocks
                ORDER BY name
                LIMIT 20
                """
            )

        stocks = cursor.fetchall()

    finally:

        cursor.close()

    # --------------------------------------------------------
    # Fetch BASIC prices
    # --------------------------------------------------------

    results = []

    for stock in stocks:

        price_data = get_basic_stock_price(
            stock["symbol"]
        )

        results.append({

            "symbol": stock["symbol"],

            "name": stock["name"],

            "sector": stock["sector"],

            "exchange": stock["exchange"],

            "current_price": (
                price_data["current_price"]
                if price_data
                else None
            ),

            "change": (
                price_data["change"]
                if price_data
                else None
            ),

            "change_percent": (
                price_data["change_percent"]
                if price_data
                else None
            ),
        })

    return results


# ============================================================
# POPULAR STOCKS
# ============================================================

@router.get("/popular")
async def get_popular_stocks(
    conn=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get popular stocks with LIVE current prices.

    OPTIMIZATION:
    Uses get_basic_stock_price() instead of
    get_stock_price().

    Therefore each stock needs only the 5-day
    price request.

    52-week data is NOT downloaded here.
    """

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                symbol,
                name,
                sector,
                exchange
            FROM stocks
            ORDER BY id
            LIMIT 12
            """
        )

        stocks = cursor.fetchall()

    finally:

        cursor.close()

    results = []

    for stock in stocks:

        price_data = get_basic_stock_price(
            stock["symbol"]
        )

        results.append({

            "symbol": stock["symbol"],

            "name": stock["name"],

            "sector": stock["sector"],

            "exchange": stock["exchange"],

            "current_price": (
                price_data["current_price"]
                if price_data
                else None
            ),

            "change": (
                price_data["change"]
                if price_data
                else None
            ),

            "change_percent": (
                price_data["change_percent"]
                if price_data
                else None
            ),
        })

    return results


# ============================================================
# ALL STOCKS
# ============================================================

@router.get("/all")
async def get_all_stocks(
    conn=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get all stocks from database with current prices.

    Uses BASIC price data.

    This avoids downloading 52-week data for every
    stock in the database.
    """

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                symbol,
                name,
                sector,
                exchange
            FROM stocks
            ORDER BY name
            """
        )

        stocks = cursor.fetchall()

    finally:

        cursor.close()

    results = []

    for stock in stocks:

        price_data = get_basic_stock_price(
            stock["symbol"]
        )

        results.append({

            "symbol": stock["symbol"],

            "name": stock["name"],

            "sector": stock["sector"],

            "exchange": stock["exchange"],

            "current_price": (
                price_data["current_price"]
                if price_data
                else None
            ),

            "change": (
                price_data["change"]
                if price_data
                else None
            ),

            "change_percent": (
                price_data["change_percent"]
                if price_data
                else None
            ),
        })

    return results


# ============================================================
# STOCK DETAIL
# ============================================================

@router.get("/{symbol}")
async def get_stock_detail(
    symbol: str,
    current_user=Depends(get_current_user),
    conn=Depends(get_db)
):
    """
    Get detailed stock information.

    Unlike Dashboard/Popular, this endpoint DOES
    fetch 52-week statistics when required.
    """

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                symbol,
                name,
                sector,
                exchange
            FROM stocks
            WHERE symbol = %s
            """,
            (symbol,)
        )

        stock = cursor.fetchone()

    finally:

        cursor.close()

    if not stock:

        raise HTTPException(
            status_code=404,
            detail=f"Stock {symbol} not found"
        )

    price_data = get_stock_price(
        symbol
    )

    if not price_data:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to fetch data for {symbol}"
        )

    return {
        **stock,
        **price_data,
    }


# ============================================================
# STOCK HISTORY
# ============================================================

@router.get("/{symbol}/history")
async def get_stock_history_endpoint(
    symbol: str,
    period: str = Query(
        "1mo",
        description=(
            "Time period: "
            "1d, 5d, 1mo, 3mo, 6mo, 1y, 5y"
        )
    ),
    current_user=Depends(get_current_user)
):
    """
    Get historical price data for a stock.

    Historical data remains separately cached.
    """

    history = get_stock_history(
        symbol,
        period
    )

    if not history:

        raise HTTPException(
            status_code=404,
            detail=f"No history found for {symbol}"
        )

    return history