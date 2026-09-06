from fastapi import APIRouter, Depends, HTTPException, Query
from app.database.connection import get_db
from app.utils.security import get_current_user
from app.services.trading_service import buy_stock, sell_stock, add_funds
from app.schemas.transaction import TradeRequest, AddFundsRequest

router = APIRouter()


@router.post("/buy")
async def buy(trade: TradeRequest, current_user=Depends(get_current_user), conn=Depends(get_db)):
    """Buy stocks (requires PIN 2468)."""
    result = buy_stock(conn, current_user["user_id"], trade.symbol, trade.quantity, trade.pin)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/sell")
async def sell(trade: TradeRequest, current_user=Depends(get_current_user), conn=Depends(get_db)):
    """Sell stocks (requires PIN 2468)."""
    result = sell_stock(conn, current_user["user_id"], trade.symbol, trade.quantity, trade.pin)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/add-funds")
async def add_funds_route(data: AddFundsRequest, current_user=Depends(get_current_user), conn=Depends(get_db)):
    """Add virtual funds (requires PIN 2468)."""
    result = add_funds(conn, current_user["user_id"], data.amount, data.pin)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/history")
async def get_transactions(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    type_filter: str = Query(None, alias="type"),
    current_user=Depends(get_current_user),
    conn=Depends(get_db)
):
    """Get transaction history."""
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT t.id, t.type, t.quantity, t.price_per_share, t.total_amount, t.created_at,
               s.symbol as stock_symbol, s.name as stock_name
        FROM transactions t
        LEFT JOIN stocks s ON t.stock_id = s.id
        WHERE t.user_id = %s
    """
    params = [current_user["user_id"]]

    if type_filter:
        query += " AND t.type = %s"
        params.append(type_filter.upper())

    query += " ORDER BY t.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, tuple(params))
    transactions = cursor.fetchall()

    # Get total count
    count_query = "SELECT COUNT(*) as total FROM transactions WHERE user_id = %s"
    count_params = [current_user["user_id"]]
    if type_filter:
        count_query += " AND type = %s"
        count_params.append(type_filter.upper())

    cursor.execute(count_query, tuple(count_params))
    total = cursor.fetchone()["total"]

    cursor.close()

    result = []
    for t in transactions:
        result.append({
            "id": t["id"],
            "type": t["type"],
            "stock_symbol": t["stock_symbol"],
            "stock_name": t["stock_name"],
            "quantity": t["quantity"],
            "price_per_share": float(t["price_per_share"]),
            "total_amount": float(t["total_amount"]),
            "created_at": str(t["created_at"]),
        })

    return {"transactions": result, "total": total}
