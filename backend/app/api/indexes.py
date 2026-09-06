"""
Custom Index API Router.

Endpoints for creating, managing, and investing in custom indexes.
All endpoints require authentication (JWT).
Indian market focused (NSE/BSE).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.database.connection import get_db
from app.utils.security import get_current_user
from app.schemas.index_schemas import (
    IndexCreate,
    IndexUpdate,
    InvestRequest,
    RedeemRequest,
    RebalanceRequest,
)
from app.services.index_service import (
    create_custom_index,
    get_user_indexes,
    get_index_detail,
    delete_custom_index,
    get_stocks_by_sector,
    get_available_sectors,
    AVAILABLE_THEMES,
)
from app.services.index_investment_service import (
    invest_in_index,
    redeem_from_index,
)
from app.services.rebalance_service import (
    execute_rebalance,
    get_rebalance_history,
    get_next_rebalance_date,
    is_rebalance_due,
)


router = APIRouter()


# ============================================================
# INDEX CRUD
# ============================================================

@router.post("")
async def create_index(
    data: IndexCreate,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Create a new custom index."""

    result = create_custom_index(
        conn=conn,
        user_id=current_user["user_id"],
        name=data.name,
        stock_symbols=data.stock_symbols,
        top_n=data.top_n,
        description=data.description,
        sector=data.sector,
        theme=data.theme,
        weight_strategy=data.weight_strategy,
        custom_weights=data.custom_weights,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    return result


@router.get("")
async def list_indexes(
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Get all custom indexes for the current user."""

    indexes = get_user_indexes(
        conn=conn,
        user_id=current_user["user_id"],
    )

    return {
        "indexes": indexes,
        "next_rebalance": get_next_rebalance_date(),
        "rebalance_due": is_rebalance_due(),
    }


@router.get("/themes")
async def list_themes(
    current_user=Depends(get_current_user),
):
    """Get available themes for index creation."""
    return {"themes": AVAILABLE_THEMES}


@router.get("/sectors")
async def list_sectors(
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Get available sectors from the stock database."""
    sectors = get_available_sectors(conn)
    return {"sectors": sectors}


@router.get("/stocks-by-sector")
async def stocks_by_sector(
    sector: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Get stocks filtered by sector for the index builder."""
    stocks = get_stocks_by_sector(conn, sector, search)
    return {"stocks": stocks}


@router.get("/{index_id}")
async def get_index(
    index_id: int,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Get detailed information about a custom index."""

    detail = get_index_detail(
        conn=conn,
        index_id=index_id,
        user_id=current_user["user_id"],
    )

    if not detail:
        raise HTTPException(
            status_code=404,
            detail="Index not found.",
        )

    return detail


@router.delete("/{index_id}")
async def delete_index(
    index_id: int,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Delete (deactivate) a custom index."""

    result = delete_custom_index(
        conn=conn,
        index_id=index_id,
        user_id=current_user["user_id"],
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    return result


# ============================================================
# INVESTMENT
# ============================================================

@router.post("/{index_id}/invest")
async def invest(
    index_id: int,
    data: InvestRequest,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Invest in a custom index."""

    result = invest_in_index(
        conn=conn,
        user_id=current_user["user_id"],
        index_id=index_id,
        amount=data.amount,
        pin=data.pin,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    return result


@router.post("/{index_id}/redeem")
async def redeem(
    index_id: int,
    data: RedeemRequest,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Redeem (sell) from a custom index."""

    result = redeem_from_index(
        conn=conn,
        user_id=current_user["user_id"],
        index_id=index_id,
        amount=data.amount,
        redeem_all=data.redeem_all,
        pin=data.pin,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    return result


# ============================================================
# REBALANCE
# ============================================================

@router.post("/{index_id}/rebalance")
async def rebalance(
    index_id: int,
    data: RebalanceRequest,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Manually trigger a rebalance on a custom index."""

    from app.utils.security import verify_pin
    if not verify_pin(data.pin):
        raise HTTPException(
            status_code=400,
            detail="Invalid PIN.",
        )

    result = execute_rebalance(
        conn=conn,
        index_id=index_id,
        user_id=current_user["user_id"],
        rebalance_type="MANUAL",
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"],
        )

    return result


@router.get("/{index_id}/rebalance-history")
async def rebalance_history(
    index_id: int,
    current_user=Depends(get_current_user),
    conn=Depends(get_db),
):
    """Get rebalance history for an index."""

    history = get_rebalance_history(
        conn=conn,
        index_id=index_id,
        user_id=current_user["user_id"],
    )

    return {"history": history}
