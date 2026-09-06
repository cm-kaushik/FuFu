"""
Index Investment Service.

Handles investing in and redeeming from custom indexes.

When a user invests in an index:
1. Funds are distributed across the top-N stocks based on the weight strategy
2. Individual stock quantities are calculated and purchased
3. A mutual-fund-like unit system tracks the investment (NAV)

When a user redeems:
1. Holdings are sold proportionally
2. Proceeds are returned to user balance

Indian Market specific:
- All prices are in INR (₹)
- Stocks are NSE/BSE listed
- Rebalancing follows March/September schedule
"""

from typing import Dict, List, Optional
import math

from app.services.yfinance_service import get_current_price_only
from app.utils.security import verify_pin


# ============================================================
# INVEST IN INDEX
# ============================================================

def invest_in_index(
    conn,
    user_id: int,
    index_id: int,
    amount: float,
    pin: str,
) -> Dict:
    """
    Invest a given amount into a custom index.

    Steps:
    1. Verify PIN
    2. Check user balance
    3. Get active constituents (top-N stocks)
    4. Calculate weight-based allocation per stock
    5. Purchase shares of each stock
    6. Create/update index_investments and index_holdings
    7. Deduct from user balance
    """

    if not verify_pin(pin):
        return {
            "success": False,
            "message": "Invalid PIN. Please enter the correct PIN.",
        }

    if amount <= 0:
        return {
            "success": False,
            "message": "Investment amount must be greater than ₹0.",
        }

    cursor = conn.cursor(dictionary=True)

    try:
        # Check user balance
        cursor.execute(
            "SELECT balance FROM users WHERE id = %s FOR UPDATE",
            (user_id,),
        )
        user = cursor.fetchone()
        if not user:
            return {"success": False, "message": "User not found."}

        balance = float(user["balance"])
        if balance < amount:
            return {
                "success": False,
                "message": (
                    f"Insufficient balance. "
                    f"Required: ₹{amount:,.2f}, "
                    f"Available: ₹{balance:,.2f}"
                ),
            }

        # Get index info
        cursor.execute(
            """
            SELECT id, name, top_n, weight_strategy, is_active
            FROM custom_indexes
            WHERE id = %s AND user_id = %s
            """,
            (index_id, user_id),
        )
        index_info = cursor.fetchone()

        if not index_info:
            return {
                "success": False,
                "message": "Custom index not found.",
            }

        if not index_info["is_active"]:
            return {
                "success": False,
                "message": "This index is no longer active.",
            }

        # Get active constituents (top-N)
        cursor.execute(
            """
            SELECT ic.stock_id, ic.rank_position, ic.custom_weight,
                   s.symbol, s.name
            FROM index_constituents ic
            JOIN stocks s ON s.id = ic.stock_id
            WHERE ic.index_id = %s AND ic.is_active_in_index = TRUE
            ORDER BY ic.rank_position ASC
            """,
            (index_id,),
        )
        active_stocks = cursor.fetchall()

        if not active_stocks:
            return {
                "success": False,
                "message": "No active stocks in this index.",
            }

        # Calculate allocations based on weight strategy
        allocations = _calculate_allocations(
            active_stocks,
            amount,
            index_info["weight_strategy"],
        )

        if not allocations:
            return {
                "success": False,
                "message": "Unable to calculate stock allocations. Please try again.",
            }

        # Check if all allocations have valid prices
        total_cost = sum(a["total_cost"] for a in allocations)
        if total_cost > amount:
            # Adjust — can happen due to rounding of whole shares
            amount = total_cost

        if balance < total_cost:
            return {
                "success": False,
                "message": (
                    f"Insufficient balance after allocation. "
                    f"Required: ₹{total_cost:,.2f}, "
                    f"Available: ₹{balance:,.2f}"
                ),
            }

        # Deduct from user balance
        cursor.execute(
            "UPDATE users SET balance = balance - %s WHERE id = %s",
            (total_cost, user_id),
        )

        # Create or update index_investment
        cursor.execute(
            """
            SELECT id, total_invested, units, nav
            FROM index_investments
            WHERE user_id = %s AND index_id = %s AND status = 'ACTIVE'
            """,
            (user_id, index_id),
        )
        existing = cursor.fetchone()

        nav = 100.0  # Starting NAV

        if existing:
            investment_id = existing["id"]
            old_invested = float(existing["total_invested"])
            old_units = float(existing["units"])
            current_nav = float(existing["nav"])

            # Buy new units at current NAV
            new_units = total_cost / current_nav
            total_units = old_units + new_units
            new_invested = old_invested + total_cost

            cursor.execute(
                """
                UPDATE index_investments
                SET total_invested = %s,
                    current_value = %s,
                    units = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (new_invested, new_invested, total_units, investment_id),
            )
            nav = current_nav

        else:
            # First investment — NAV starts at 100
            units = total_cost / nav

            cursor.execute(
                """
                INSERT INTO index_investments
                    (user_id, index_id, total_invested, current_value,
                     units, nav, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
                """,
                (user_id, index_id, total_cost, total_cost, units, nav),
            )
            investment_id = cursor.lastrowid

        # Create/update individual stock holdings
        allocation_details = []

        for alloc in allocations:
            # Check existing holding
            cursor.execute(
                """
                SELECT id, quantity, avg_buy_price
                FROM index_holdings
                WHERE investment_id = %s AND stock_id = %s
                """,
                (investment_id, alloc["stock_id"]),
            )
            existing_holding = cursor.fetchone()

            if existing_holding:
                old_qty = existing_holding["quantity"]
                old_avg = float(existing_holding["avg_buy_price"])
                new_qty = old_qty + alloc["quantity"]
                new_avg = (
                    (old_avg * old_qty + alloc["price"] * alloc["quantity"])
                    / new_qty
                )

                cursor.execute(
                    """
                    UPDATE index_holdings
                    SET quantity = %s,
                        allocated_amount = allocated_amount + %s,
                        weight_percent = %s,
                        avg_buy_price = %s
                    WHERE id = %s
                    """,
                    (
                        new_qty, alloc["total_cost"],
                        alloc["weight"], new_avg,
                        existing_holding["id"],
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO index_holdings
                        (investment_id, stock_id, quantity,
                         allocated_amount, weight_percent, avg_buy_price)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        investment_id, alloc["stock_id"],
                        alloc["quantity"], alloc["total_cost"],
                        alloc["weight"], alloc["price"],
                    ),
                )

            # Record as transaction
            cursor.execute(
                """
                INSERT INTO transactions
                    (user_id, stock_id, type, quantity,
                     price_per_share, total_amount)
                VALUES (%s, %s, 'BUY', %s, %s, %s)
                """,
                (
                    user_id, alloc["stock_id"],
                    alloc["quantity"], alloc["price"],
                    alloc["total_cost"],
                ),
            )

            allocation_details.append({
                "symbol": alloc["symbol"],
                "name": alloc["name"],
                "quantity": alloc["quantity"],
                "price": round(alloc["price"], 2),
                "weight": round(alloc["weight"], 2),
                "total_cost": round(alloc["total_cost"], 2),
            })

        # Record NAV history
        cursor.execute(
            """
            INSERT INTO index_value_history
                (index_id, nav, total_value)
            VALUES (%s, %s, %s)
            """,
            (index_id, nav, total_cost),
        )

        conn.commit()

        # Get updated balance
        cursor.execute(
            "SELECT balance FROM users WHERE id = %s",
            (user_id,),
        )
        new_balance = float(cursor.fetchone()["balance"])

        return {
            "success": True,
            "message": (
                f"Successfully invested ₹{total_cost:,.2f} in "
                f"'{index_info['name']}'"
            ),
            "investment": {
                "index_id": index_id,
                "index_name": index_info["name"],
                "total_invested": round(total_cost, 2),
                "nav": round(nav, 2),
                "stocks_purchased": len(allocation_details),
            },
            "new_balance": round(new_balance, 2),
            "allocations": allocation_details,
        }

    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Investment failed: {str(e)}",
        }

    finally:
        cursor.close()


# ============================================================
# REDEEM FROM INDEX
# ============================================================

def redeem_from_index(
    conn,
    user_id: int,
    index_id: int,
    amount: float = None,
    redeem_all: bool = False,
    pin: str = "",
) -> Dict:
    """
    Redeem (sell) holdings from a custom index.

    If redeem_all=True, sells everything.
    Otherwise, sells proportionally to match the requested amount.
    """

    if not verify_pin(pin):
        return {
            "success": False,
            "message": "Invalid PIN. Please enter the correct PIN.",
        }

    cursor = conn.cursor(dictionary=True)

    try:
        # Get investment
        cursor.execute(
            """
            SELECT ii.id, ii.total_invested, ii.current_value,
                   ii.units, ii.nav, ci.name
            FROM index_investments ii
            JOIN custom_indexes ci ON ci.id = ii.index_id
            WHERE ii.user_id = %s
              AND ii.index_id = %s
              AND ii.status = 'ACTIVE'
            """,
            (user_id, index_id),
        )
        investment = cursor.fetchone()

        if not investment:
            return {
                "success": False,
                "message": "No active investment found in this index.",
            }

        investment_id = investment["id"]

        # Get current holdings
        cursor.execute(
            """
            SELECT ih.id, ih.stock_id, ih.quantity,
                   ih.avg_buy_price, s.symbol, s.name
            FROM index_holdings ih
            JOIN stocks s ON s.id = ih.stock_id
            WHERE ih.investment_id = %s AND ih.quantity > 0
            """,
            (investment_id,),
        )
        holdings = cursor.fetchall()

        if not holdings:
            return {
                "success": False,
                "message": "No holdings to redeem.",
            }

        # Calculate current total value
        total_current_value = 0.0
        holding_values = []

        for h in holdings:
            price = get_current_price_only(h["symbol"])
            if price is None:
                price = float(h["avg_buy_price"])

            value = price * h["quantity"]
            total_current_value += value
            holding_values.append({
                **h,
                "current_price": price,
                "current_value": value,
            })

        if redeem_all:
            redeem_fraction = 1.0
        else:
            if amount is None or amount <= 0:
                return {
                    "success": False,
                    "message": "Please specify an amount to redeem.",
                }
            if amount > total_current_value:
                return {
                    "success": False,
                    "message": (
                        f"Redeem amount (₹{amount:,.2f}) exceeds "
                        f"current value (₹{total_current_value:,.2f})."
                    ),
                }
            redeem_fraction = amount / total_current_value

        total_proceeds = 0.0
        sell_details = []

        for hv in holding_values:
            sell_qty = (
                hv["quantity"]
                if redeem_all
                else max(1, int(hv["quantity"] * redeem_fraction))
            )

            # Don't sell more than we have
            sell_qty = min(sell_qty, hv["quantity"])
            sell_value = sell_qty * hv["current_price"]
            total_proceeds += sell_value

            remaining_qty = hv["quantity"] - sell_qty

            if remaining_qty == 0:
                cursor.execute(
                    "DELETE FROM index_holdings WHERE id = %s",
                    (hv["id"],),
                )
            else:
                cursor.execute(
                    """
                    UPDATE index_holdings
                    SET quantity = %s,
                        allocated_amount = allocated_amount - %s
                    WHERE id = %s
                    """,
                    (remaining_qty, sell_value, hv["id"]),
                )

            # Record transaction
            cursor.execute(
                """
                INSERT INTO transactions
                    (user_id, stock_id, type, quantity,
                     price_per_share, total_amount)
                VALUES (%s, %s, 'SELL', %s, %s, %s)
                """,
                (
                    user_id, hv["stock_id"],
                    sell_qty, hv["current_price"],
                    sell_value,
                ),
            )

            sell_details.append({
                "symbol": hv["symbol"],
                "name": hv["name"],
                "quantity_sold": sell_qty,
                "price": round(hv["current_price"], 2),
                "proceeds": round(sell_value, 2),
            })

        # Add proceeds to user balance
        cursor.execute(
            "UPDATE users SET balance = balance + %s WHERE id = %s",
            (total_proceeds, user_id),
        )

        # Update or close investment
        if redeem_all:
            cursor.execute(
                """
                UPDATE index_investments
                SET status = 'REDEEMED',
                    current_value = 0,
                    units = 0,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (investment_id,),
            )
        else:
            remaining_value = total_current_value - total_proceeds
            old_invested = float(investment["total_invested"])
            remaining_invested = old_invested * (1 - redeem_fraction)

            cursor.execute(
                """
                UPDATE index_investments
                SET total_invested = %s,
                    current_value = %s,
                    units = units * %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    remaining_invested, remaining_value,
                    1 - redeem_fraction, investment_id,
                ),
            )

        conn.commit()

        # Get updated balance
        cursor.execute(
            "SELECT balance FROM users WHERE id = %s",
            (user_id,),
        )
        new_balance = float(cursor.fetchone()["balance"])

        return {
            "success": True,
            "message": (
                f"Successfully redeemed ₹{total_proceeds:,.2f} from "
                f"'{investment['name']}'"
            ),
            "investment": {
                "total_redeemed": round(total_proceeds, 2),
                "stocks_sold": len(sell_details),
            },
            "new_balance": round(new_balance, 2),
            "allocations": sell_details,
        }

    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Redemption failed: {str(e)}",
        }

    finally:
        cursor.close()


# ============================================================
# HELPER: Calculate weight-based allocations
# ============================================================

def _calculate_allocations(
    active_stocks: List[Dict],
    total_amount: float,
    weight_strategy: str,
) -> List[Dict]:
    """
    Calculate how much to invest in each stock
    based on the weight strategy.

    Returns a list of allocation dicts with:
    - stock_id, symbol, name
    - weight (percentage)
    - allocated_amount
    - price (current)
    - quantity (whole shares)
    - total_cost (quantity * price)
    """

    n = len(active_stocks)
    if n == 0:
        return []

    # Get current prices
    stock_prices = []
    for s in active_stocks:
        price = get_current_price_only(s["symbol"])
        if price is None or price <= 0:
            continue
        stock_prices.append({
            "stock_id": s["stock_id"],
            "symbol": s["symbol"],
            "name": s["name"],
            "price": price,
            "custom_weight": float(s["custom_weight"]) if s["custom_weight"] else None,
        })

    if not stock_prices:
        return []

    n = len(stock_prices)
    total_price_sum = sum(sp["price"] for sp in stock_prices)

    # Assign weights
    for sp in stock_prices:
        if weight_strategy == "EQUAL":
            sp["weight"] = 100.0 / n

        elif weight_strategy == "MARKET_CAP":
            sp["weight"] = (sp["price"] / total_price_sum) * 100

        elif weight_strategy == "CUSTOM":
            sp["weight"] = sp["custom_weight"] or (100.0 / n)

        elif weight_strategy == "PERFORMANCE":
            sp["weight"] = (sp["price"] / total_price_sum) * 100

        else:
            sp["weight"] = 100.0 / n

    # Calculate allocated amounts and quantities
    allocations = []
    total_cost = 0.0

    for sp in stock_prices:
        allocated = total_amount * (sp["weight"] / 100.0)
        quantity = max(1, math.floor(allocated / sp["price"]))
        cost = quantity * sp["price"]
        total_cost += cost

        allocations.append({
            "stock_id": sp["stock_id"],
            "symbol": sp["symbol"],
            "name": sp["name"],
            "weight": sp["weight"],
            "allocated_amount": round(allocated, 2),
            "price": sp["price"],
            "quantity": quantity,
            "total_cost": round(cost, 2),
        })

    return allocations
