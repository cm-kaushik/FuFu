"""
Rebalance Service.

Handles automatic and manual rebalancing of custom indexes.

Indian Market Convention:
- Semi-annual rebalance: End of March and End of September
- Matches NIFTY 50 / SENSEX rebalance schedule

Rebalance process:
1. Re-rank all universe stocks by market cap (current price)
2. Select new Top-N
3. Compare with current Top-N
4. Sell stocks that dropped out
5. Buy stocks that entered
6. Adjust weights for remaining stocks
7. Log all changes
"""

from typing import Dict, List, Optional
from datetime import datetime
import math

from app.services.yfinance_service import get_current_price_only


# ============================================================
# CHECK IF REBALANCE IS DUE
# ============================================================

def is_rebalance_due() -> bool:
    """
    Check if current date is in the rebalance window.

    Indian market rebalances at end of March and September.
    We trigger if we're in the last week of March or September.
    """

    now = datetime.now()
    month = now.month
    day = now.day

    # Last week of March (25-31) or September (25-30)
    if month == 3 and day >= 25:
        return True
    if month == 9 and day >= 25:
        return True

    return False


def get_next_rebalance_date() -> str:
    """Get the next rebalance date."""

    now = datetime.now()

    if now.month <= 3:
        return f"March 31, {now.year}"
    elif now.month <= 9:
        return f"September 30, {now.year}"
    else:
        return f"March 31, {now.year + 1}"


# ============================================================
# EXECUTE REBALANCE
# ============================================================

def execute_rebalance(
    conn,
    index_id: int,
    user_id: int,
    rebalance_type: str = "SEMI_ANNUAL",
) -> Dict:
    """
    Execute a rebalance on a custom index.

    Steps:
    1. Get all universe stocks with current prices
    2. Re-rank by price (market cap proxy)
    3. Select new Top-N
    4. Compare with old Top-N
    5. For invested indexes: sell removed stocks, buy added stocks
    6. Adjust weights
    7. Log everything
    """

    cursor = conn.cursor(dictionary=True)

    try:
        # Get index info
        cursor.execute(
            """
            SELECT id, name, top_n, weight_strategy, universe_size
            FROM custom_indexes
            WHERE id = %s AND user_id = %s AND is_active = TRUE
            """,
            (index_id, user_id),
        )
        index_info = cursor.fetchone()

        if not index_info:
            return {
                "success": False,
                "message": "Index not found.",
            }

        top_n = index_info["top_n"]

        # Get all constituents with prices
        cursor.execute(
            """
            SELECT ic.id, ic.stock_id, ic.is_active_in_index,
                   ic.rank_position, ic.custom_weight,
                   s.symbol, s.name
            FROM index_constituents ic
            JOIN stocks s ON s.id = ic.stock_id
            WHERE ic.index_id = %s
            """,
            (index_id,),
        )
        all_constituents = cursor.fetchall()

        # Fetch current prices and rank
        stock_data = []
        for c in all_constituents:
            price = get_current_price_only(c["symbol"])
            stock_data.append({
                **c,
                "current_price": price or 0.0,
                "was_active": bool(c["is_active_in_index"]),
            })

        # Re-rank by price (market cap proxy)
        stock_data.sort(
            key=lambda s: s["current_price"],
            reverse=True,
        )

        # Determine new Top-N
        old_active = {
            s["stock_id"]
            for s in stock_data
            if s["was_active"]
        }
        new_active = set()
        changes = []

        for rank, stock in enumerate(stock_data, start=1):
            is_now_active = rank <= top_n
            was_active = stock["was_active"]

            new_active.add(stock["stock_id"]) if is_now_active else None

            # Update constituent
            cursor.execute(
                """
                UPDATE index_constituents
                SET is_active_in_index = %s,
                    rank_position = %s
                WHERE id = %s
                """,
                (is_now_active, rank, stock["id"]),
            )

            if is_now_active and not was_active:
                changes.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "action": "ADDED",
                    "new_rank": rank,
                    "price": stock["current_price"],
                })
            elif was_active and not is_now_active:
                changes.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "action": "REMOVED",
                    "old_rank": stock["rank_position"],
                    "price": stock["current_price"],
                })
            elif is_now_active and was_active:
                if rank != stock["rank_position"]:
                    changes.append({
                        "symbol": stock["symbol"],
                        "name": stock["name"],
                        "action": "RANK_CHANGED",
                        "old_rank": stock["rank_position"],
                        "new_rank": rank,
                        "price": stock["current_price"],
                    })

        # Handle investment rebalance if user has active investment
        cursor.execute(
            """
            SELECT id, total_invested, current_value, units, nav
            FROM index_investments
            WHERE index_id = %s AND user_id = %s AND status = 'ACTIVE'
            """,
            (index_id, user_id),
        )
        investment = cursor.fetchone()

        investment_changes = []

        if investment:
            investment_id = investment["id"]

            # Sell stocks that were removed from top-N
            removed_stocks = old_active - new_active
            added_stocks = new_active - old_active

            sell_proceeds = 0.0

            for stock_id in removed_stocks:
                cursor.execute(
                    """
                    SELECT ih.id, ih.quantity, ih.avg_buy_price, s.symbol
                    FROM index_holdings ih
                    JOIN stocks s ON s.id = ih.stock_id
                    WHERE ih.investment_id = %s AND ih.stock_id = %s
                    """,
                    (investment_id, stock_id),
                )
                holding = cursor.fetchone()

                if holding and holding["quantity"] > 0:
                    price = get_current_price_only(holding["symbol"])
                    if price is None:
                        price = float(holding["avg_buy_price"])

                    proceeds = price * holding["quantity"]
                    sell_proceeds += proceeds

                    # Record sell transaction
                    cursor.execute(
                        """
                        INSERT INTO transactions
                            (user_id, stock_id, type, quantity,
                             price_per_share, total_amount)
                        VALUES (%s, %s, 'SELL', %s, %s, %s)
                        """,
                        (user_id, stock_id, holding["quantity"], price, proceeds),
                    )

                    # Remove holding
                    cursor.execute(
                        "DELETE FROM index_holdings WHERE id = %s",
                        (holding["id"],),
                    )

                    investment_changes.append({
                        "action": "SELL",
                        "symbol": holding["symbol"],
                        "quantity": holding["quantity"],
                        "price": round(price, 2),
                        "amount": round(proceeds, 2),
                    })

            # Buy new stocks that entered top-N
            if sell_proceeds > 0 and added_stocks:
                per_stock = sell_proceeds / len(added_stocks)

                for stock_id in added_stocks:
                    # Find the stock details
                    stock_info = next(
                        (s for s in stock_data if s["stock_id"] == stock_id),
                        None,
                    )
                    if not stock_info or stock_info["current_price"] <= 0:
                        continue

                    price = stock_info["current_price"]
                    quantity = max(1, math.floor(per_stock / price))
                    cost = quantity * price

                    # Record buy transaction
                    cursor.execute(
                        """
                        INSERT INTO transactions
                            (user_id, stock_id, type, quantity,
                             price_per_share, total_amount)
                        VALUES (%s, %s, 'BUY', %s, %s, %s)
                        """,
                        (user_id, stock_id, quantity, price, cost),
                    )

                    # Add new holding
                    cursor.execute(
                        """
                        INSERT INTO index_holdings
                            (investment_id, stock_id, quantity,
                             allocated_amount, weight_percent, avg_buy_price)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            quantity = quantity + %s,
                            allocated_amount = allocated_amount + %s,
                            avg_buy_price = %s
                        """,
                        (
                            investment_id, stock_id, quantity,
                            cost, 100.0 / top_n, price,
                            quantity, cost, price,
                        ),
                    )

                    investment_changes.append({
                        "action": "BUY",
                        "symbol": stock_info["symbol"],
                        "quantity": quantity,
                        "price": round(price, 2),
                        "amount": round(cost, 2),
                    })

            # Recalculate current value
            cursor.execute(
                """
                SELECT ih.quantity, s.symbol
                FROM index_holdings ih
                JOIN stocks s ON s.id = ih.stock_id
                WHERE ih.investment_id = %s
                """,
                (investment_id,),
            )
            all_holdings = cursor.fetchall()

            new_value = 0.0
            for h in all_holdings:
                p = get_current_price_only(h["symbol"])
                if p:
                    new_value += p * h["quantity"]

            # Update investment value
            units = float(investment["units"])
            new_nav = new_value / units if units > 0 else 100.0

            cursor.execute(
                """
                UPDATE index_investments
                SET current_value = %s, nav = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (new_value, new_nav, investment_id),
            )

            # Record NAV history
            cursor.execute(
                """
                INSERT INTO index_value_history
                    (index_id, nav, total_value)
                VALUES (%s, %s, %s)
                """,
                (index_id, new_nav, new_value),
            )

        # Log rebalance
        for change in changes:
            cursor.execute(
                """
                INSERT INTO rebalance_log
                    (index_id, investment_id, rebalance_type,
                     action, stock_symbol,
                     old_weight, new_weight)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    index_id,
                    investment["id"] if investment else 0,
                    rebalance_type,
                    change["action"],
                    change["symbol"],
                    0.0, 0.0,
                ),
            )

        conn.commit()

        # Build new weights list
        new_weights = []
        for rank, stock in enumerate(stock_data[:top_n], start=1):
            new_weights.append({
                "rank": rank,
                "symbol": stock["symbol"],
                "name": stock["name"],
                "price": round(stock["current_price"], 2),
            })

        return {
            "success": True,
            "message": (
                f"Rebalance completed for '{index_info['name']}'. "
                f"{len(changes)} changes made."
            ),
            "changes": changes,
            "investment_changes": investment_changes,
            "new_weights": new_weights,
        }

    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Rebalance failed: {str(e)}",
        }

    finally:
        cursor.close()


# ============================================================
# GET REBALANCE HISTORY
# ============================================================

def get_rebalance_history(
    conn,
    index_id: int,
    user_id: int,
) -> List[Dict]:
    """Get rebalance history for an index."""

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT rl.*
            FROM rebalance_log rl
            JOIN custom_indexes ci ON ci.id = rl.index_id
            WHERE rl.index_id = %s AND ci.user_id = %s
            ORDER BY rl.executed_at DESC
            LIMIT 50
            """,
            (index_id, user_id),
        )
        logs = cursor.fetchall()

    finally:
        cursor.close()

    return [
        {
            "id": log["id"],
            "action": log["action"],
            "stock_symbol": log["stock_symbol"],
            "rebalance_type": log["rebalance_type"],
            "old_weight": float(log["old_weight"]) if log["old_weight"] else 0,
            "new_weight": float(log["new_weight"]) if log["new_weight"] else 0,
            "executed_at": str(log["executed_at"]),
        }
        for log in logs
    ]
