from typing import Dict, Optional
import mysql.connector
from app.services.yfinance_service import get_current_price_only
from app.utils.security import verify_pin


def buy_stock(conn, user_id: int, symbol: str, quantity: int, pin: str) -> Dict:
    """Execute a stock buy order."""
    # Verify PIN
    if not verify_pin(pin):
        return {"success": False, "message": "Invalid PIN. Please enter the correct PIN."}

    if quantity <= 0:
        return {"success": False, "message": "Quantity must be greater than 0."}

    # Get current price
    current_price = get_current_price_only(symbol)
    if current_price is None:
        return {"success": False, "message": f"Unable to fetch price for {symbol}. Please try again."}

    total_cost = current_price * quantity

    cursor = conn.cursor(dictionary=True)

    try:
        # Check user balance
        cursor.execute("SELECT balance FROM users WHERE id = %s FOR UPDATE", (user_id,))
        user = cursor.fetchone()
        if not user:
            return {"success": False, "message": "User not found."}

        balance = float(user["balance"])
        if balance < total_cost:
            return {
                "success": False,
                "message": f"Insufficient balance. Required: ₹{total_cost:,.2f}, Available: ₹{balance:,.2f}"
            }

        # Get or create stock in DB
        cursor.execute("SELECT id FROM stocks WHERE symbol = %s", (symbol,))
        stock = cursor.fetchone()
        if not stock:
            return {"success": False, "message": f"Stock {symbol} not found in database."}
        stock_id = stock["id"]

        # Deduct balance
        cursor.execute(
            "UPDATE users SET balance = balance - %s WHERE id = %s",
            (total_cost, user_id)
        )

        # Update or create holding
        cursor.execute(
            "SELECT id, quantity, avg_buy_price FROM holdings WHERE user_id = %s AND stock_id = %s",
            (user_id, stock_id)
        )
        existing = cursor.fetchone()

        if existing:
            old_qty = existing["quantity"]
            old_avg = float(existing["avg_buy_price"])
            new_qty = old_qty + quantity
            new_avg = ((old_avg * old_qty) + (current_price * quantity)) / new_qty
            cursor.execute(
                "UPDATE holdings SET quantity = %s, avg_buy_price = %s WHERE id = %s",
                (new_qty, round(new_avg, 2), existing["id"])
            )
        else:
            cursor.execute(
                "INSERT INTO holdings (user_id, stock_id, quantity, avg_buy_price) VALUES (%s, %s, %s, %s)",
                (user_id, stock_id, quantity, current_price)
            )

        # Record transaction
        cursor.execute(
            """INSERT INTO transactions (user_id, stock_id, type, quantity, price_per_share, total_amount)
               VALUES (%s, %s, 'BUY', %s, %s, %s)""",
            (user_id, stock_id, quantity, current_price, total_cost)
        )
        transaction_id = cursor.lastrowid

        conn.commit()

        # Get updated balance
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        new_balance = float(cursor.fetchone()["balance"])

        cursor.close()

        return {
            "success": True,
            "message": f"Successfully bought {quantity} shares of {symbol} at ₹{current_price:,.2f}",
            "transaction": {
                "id": transaction_id,
                "type": "BUY",
                "stock_symbol": symbol,
                "stock_name": symbol,
                "quantity": quantity,
                "price_per_share": current_price,
                "total_amount": round(total_cost, 2),
                "created_at": "",
            },
            "new_balance": round(new_balance, 2),
        }

    except Exception as e:
        conn.rollback()
        cursor.close()
        return {"success": False, "message": f"Trade failed: {str(e)}"}


def sell_stock(conn, user_id: int, symbol: str, quantity: int, pin: str) -> Dict:
    """Execute a stock sell order."""
    # Verify PIN
    if not verify_pin(pin):
        return {"success": False, "message": "Invalid PIN. Please enter the correct PIN."}

    if quantity <= 0:
        return {"success": False, "message": "Quantity must be greater than 0."}

    # Get current price
    current_price = get_current_price_only(symbol)
    if current_price is None:
        return {"success": False, "message": f"Unable to fetch price for {symbol}. Please try again."}

    total_value = current_price * quantity

    cursor = conn.cursor(dictionary=True)

    try:
        # Get stock ID
        cursor.execute("SELECT id FROM stocks WHERE symbol = %s", (symbol,))
        stock = cursor.fetchone()
        if not stock:
            return {"success": False, "message": f"Stock {symbol} not found."}
        stock_id = stock["id"]

        # Check holdings
        cursor.execute(
            "SELECT id, quantity, avg_buy_price FROM holdings WHERE user_id = %s AND stock_id = %s FOR UPDATE",
            (user_id, stock_id)
        )
        holding = cursor.fetchone()

        if not holding or holding["quantity"] < quantity:
            available = holding["quantity"] if holding else 0
            return {
                "success": False,
                "message": f"Insufficient shares. You have {available} shares of {symbol}."
            }

        # Update holding
        new_qty = holding["quantity"] - quantity
        if new_qty == 0:
            cursor.execute("DELETE FROM holdings WHERE id = %s", (holding["id"],))
        else:
            cursor.execute(
                "UPDATE holdings SET quantity = %s WHERE id = %s",
                (new_qty, holding["id"])
            )

        # Add to balance
        cursor.execute(
            "UPDATE users SET balance = balance + %s WHERE id = %s",
            (total_value, user_id)
        )

        # Record transaction
        cursor.execute(
            """INSERT INTO transactions (user_id, stock_id, type, quantity, price_per_share, total_amount)
               VALUES (%s, %s, 'SELL', %s, %s, %s)""",
            (user_id, stock_id, quantity, current_price, total_value)
        )
        transaction_id = cursor.lastrowid

        conn.commit()

        # Get updated balance
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        new_balance = float(cursor.fetchone()["balance"])

        cursor.close()

        return {
            "success": True,
            "message": f"Successfully sold {quantity} shares of {symbol} at ₹{current_price:,.2f}",
            "transaction": {
                "id": transaction_id,
                "type": "SELL",
                "stock_symbol": symbol,
                "stock_name": symbol,
                "quantity": quantity,
                "price_per_share": current_price,
                "total_amount": round(total_value, 2),
                "created_at": "",
            },
            "new_balance": round(new_balance, 2),
        }

    except Exception as e:
        conn.rollback()
        cursor.close()
        return {"success": False, "message": f"Trade failed: {str(e)}"}


def add_funds(conn, user_id: int, amount: float, pin: str) -> Dict:
    """Add virtual funds to user account (requires PIN)."""
    if not verify_pin(pin):
        return {"success": False, "message": "Invalid PIN. Please enter the correct PIN."}

    if amount <= 0:
        return {"success": False, "message": "Amount must be greater than 0."}

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "UPDATE users SET balance = balance + %s WHERE id = %s",
            (amount, user_id)
        )

        # Record as DEPOSIT transaction
        cursor.execute(
            """INSERT INTO transactions (user_id, stock_id, type, quantity, price_per_share, total_amount)
               VALUES (%s, NULL, 'DEPOSIT', 0, 0, %s)""",
            (user_id, amount)
        )

        conn.commit()

        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        new_balance = float(cursor.fetchone()["balance"])

        cursor.close()

        return {
            "success": True,
            "message": f"Successfully added ₹{amount:,.2f} to your account.",
            "new_balance": round(new_balance, 2),
        }

    except Exception as e:
        conn.rollback()
        cursor.close()
        return {"success": False, "message": f"Failed to add funds: {str(e)}"}
