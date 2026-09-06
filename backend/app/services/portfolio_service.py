"""
Portfolio service.

Handles:
- User holdings
- Current market values
- P&L calculations
- Portfolio summary

Optimized for fast dashboard loading.

IMPORTANT:
Portfolio price lookups use get_current_price_only(),
which only fetches basic current-price data.

It does NOT request 52-week statistics.
"""

from typing import List, Dict

from app.services.yfinance_service import (
    get_current_price_only
)


# ============================================================
# BUILD HOLDINGS
# ============================================================

def get_user_holdings(
    conn,
    user_id: int
) -> List[Dict]:

    """
    Get all holdings for a user.

    Uses the FAST current-price-only Yahoo service.
    """

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                h.id,
                h.quantity,
                h.avg_buy_price,
                s.symbol,
                s.name,
                s.sector
            FROM holdings h
            JOIN stocks s
                ON h.stock_id = s.id
            WHERE
                h.user_id = %s
                AND h.quantity > 0
            ORDER BY s.name
            """,
            (user_id,)
        )

        holdings = cursor.fetchall()

    finally:

        cursor.close()

    result: List[Dict] = []

    # ========================================================
    # PROCESS HOLDINGS
    # ========================================================

    for holding in holdings:

        symbol = (
            holding["symbol"] or ""
        ).strip().upper()

        quantity = int(
            holding["quantity"]
        )

        avg_buy_price = float(
            holding["avg_buy_price"]
        )

        # ----------------------------------------------------
        # FAST current price
        #
        # This does NOT request 52-week data.
        # ----------------------------------------------------

        current_price = get_current_price_only(
            symbol
        )

        # ----------------------------------------------------
        # Yahoo unavailable
        # ----------------------------------------------------

        if current_price is None:

            current_price = avg_buy_price

            price_available = False

        else:

            price_available = True

        # ----------------------------------------------------
        # Investment
        # ----------------------------------------------------

        invested_value = (
            quantity *
            avg_buy_price
        )

        # ----------------------------------------------------
        # Current value
        # ----------------------------------------------------

        current_value = (
            quantity *
            current_price
        )

        # ----------------------------------------------------
        # P&L
        # ----------------------------------------------------

        if price_available:

            pnl = (
                current_value -
                invested_value
            )

            pnl_percent = (
                (pnl / invested_value) * 100
                if invested_value > 0
                else 0.0
            )

        else:

            pnl = 0.0

            pnl_percent = 0.0

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        result.append({

            "stock_symbol": symbol,

            "stock_name": holding["name"],

            "sector": holding["sector"],

            "quantity": quantity,

            "avg_buy_price": round(
                avg_buy_price,
                2
            ),

            "current_price": round(
                current_price,
                2
            ),

            "invested_value": round(
                invested_value,
                2
            ),

            "current_value": round(
                current_value,
                2
            ),

            "pnl": round(
                pnl,
                2
            ),

            "pnl_percent": round(
                pnl_percent,
                2
            ),
        })

    return result


# ============================================================
# SUMMARY FROM EXISTING HOLDINGS
# ============================================================

def _calculate_summary_from_holdings(
    balance: float,
    holdings: List[Dict]
) -> Dict:

    """
    Calculate summary using already-loaded holdings.

    This prevents another database query and another
    round of Yahoo price lookups.
    """

    total_invested = sum(
        float(
            holding["invested_value"]
        )
        for holding in holdings
    )

    portfolio_value = sum(
        float(
            holding["current_value"]
        )
        for holding in holdings
    )

    total_pnl = (
        portfolio_value -
        total_invested
    )

    total_pnl_percent = (
        (total_pnl / total_invested) * 100
        if total_invested > 0
        else 0.0
    )

    return {

        "balance": round(
            balance,
            2
        ),

        "total_invested": round(
            total_invested,
            2
        ),

        "portfolio_value": round(
            portfolio_value,
            2
        ),

        "total_pnl": round(
            total_pnl,
            2
        ),

        "total_pnl_percent": round(
            total_pnl_percent,
            2
        ),

        "holdings_count": len(
            holdings
        ),
    }


# ============================================================
# PORTFOLIO SUMMARY
# ============================================================

def get_portfolio_summary(
    conn,
    user_id: int
) -> Dict:

    """
    Calculate portfolio summary.

    Uses fast current-price lookups.
    """

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT balance
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

    finally:

        cursor.close()

    balance = (
        float(user["balance"])
        if user
        and user["balance"] is not None
        else 0.0
    )

    # --------------------------------------------------------
    # Load holdings once.
    # --------------------------------------------------------

    holdings = get_user_holdings(
        conn,
        user_id
    )

    return _calculate_summary_from_holdings(
        balance,
        holdings
    )


# ============================================================
# FULL PORTFOLIO
# ============================================================

def get_full_portfolio(
    conn,
    user_id: int
) -> Dict:

    """
    Get complete portfolio efficiently.

    Holdings are fetched only ONCE.
    """

    cursor = conn.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT balance
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

    finally:

        cursor.close()

    balance = (
        float(user["balance"])
        if user
        and user["balance"] is not None
        else 0.0
    )

    # --------------------------------------------------------
    # Fetch holdings only once.
    # --------------------------------------------------------

    holdings = get_user_holdings(
        conn,
        user_id
    )

    summary = _calculate_summary_from_holdings(
        balance,
        holdings
    )

    return {

        "summary": summary,

        "holdings": holdings,
    }