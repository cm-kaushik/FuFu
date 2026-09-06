"""
Custom Index Service.

Core business logic for creating, managing, and tracking
user-defined custom indexes on the Indian stock market (NSE/BSE).

Features:
- Create custom indexes with a universe of stocks
- Auto-select Top-N by market cap from the universe
- Calculate composite NAV (Net Asset Value)
- Track index performance over time
- Support multiple weight strategies (EQUAL, MARKET_CAP, CUSTOM, PERFORMANCE)

Rebalancing follows Indian market convention:
- Semi-annual: end of March and end of September
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.services.yfinance_service import (
    get_basic_stock_price,
    get_current_price_only,
    get_stock_history,
)


# ============================================================
# INDIAN STOCK MARKET SECTORS
# ============================================================

INDIAN_STOCK_MARKET_SECTORS = [
    {
        "id": "banking-finance",
        "name": "Banking & Financial Services",
        "icon": "🏦",
        "description": "Private & PSU banks, NBFCs, housing finance & insurance",
        "db_sectors": ["Banking", "Finance", "Financial Services"],
        "leaders": "HDFC Bank, ICICI Bank, SBI, Bajaj Finance",
        "flagship_symbols": [
            "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
            "BAJFINANCE.NS", "BAJAJFINSV.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS",
            "CANBK.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "SHRIRAMFIN.NS", "HDFCLIFE.NS",
            "SBILIFE.NS", "ICICIPRULI.NS",
        ],
    },
    {
        "id": "it-software",
        "name": "Information Technology (IT)",
        "icon": "💻",
        "description": "Global software exporters, cloud, SaaS & enterprise consulting",
        "db_sectors": ["IT", "Technology"],
        "leaders": "TCS, Infosys, Wipro, HCL Tech",
        "flagship_symbols": [
            "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS",
            "LTIM.NS", "COFORGE.NS", "PERSISTENT.NS", "MPHASIS.NS", "LTTS.NS",
            "KPITTECH.NS", "TATAELXSI.NS",
        ],
    },
    {
        "id": "auto-ancillary",
        "name": "Automobile & Auto Ancillary",
        "icon": "🚗",
        "description": "Passenger cars, 2-wheelers, commercial vehicles, EVs & auto components",
        "db_sectors": ["Automobile", "Consumer Cyclical"],
        "leaders": "Tata Motors, Maruti Suzuki, M&M, Bajaj Auto",
        "flagship_symbols": [
            "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS",
            "HEROMOTOCO.NS", "TVSMOTOR.NS", "BHARATFORG.NS", "ASHOKLEY.NS", "BOSCHLTD.NS",
            "MRF.NS", "APOLLOTYRE.NS", "BALKRISIND.NS",
        ],
    },
    {
        "id": "pharma-healthcare",
        "name": "Pharmaceuticals & Healthcare",
        "icon": "💊",
        "description": "Formulations, active pharmaceutical ingredients (APIs) & hospitals",
        "db_sectors": ["Pharma", "Healthcare"],
        "leaders": "Sun Pharma, Dr. Reddy's, Cipla, Apollo Hospitals",
        "flagship_symbols": [
            "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "APOLLOHOSP.NS", "DIVISLAB.NS",
            "LUPIN.NS", "MANKIND.NS", "MAXHEALTH.NS", "ZYDUSLIFE.NS", "TORNTPHARM.NS",
            "AUROPHARMA.NS", "ALKEM.NS", "BIOCON.NS", "FORTIS.NS",
        ],
    },
    {
        "id": "fmcg-consumer",
        "name": "Fast-Moving Consumer Goods (FMCG)",
        "icon": "🛒",
        "description": "Packaged food, personal care, beverages, household staples & retail",
        "db_sectors": ["FMCG", "Consumer Defensive", "Consumer Goods"],
        "leaders": "ITC, Hindustan Unilever, Nestle India, Britannia",
        "flagship_symbols": [
            "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS",
            "DABUR.NS", "MARICO.NS", "GODREJCP.NS", "COLPAL.NS", "VBL.NS",
            "EMAMILTD.NS", "PGHH.NS",
        ],
    },
    {
        "id": "energy-oil-gas",
        "name": "Oil, Gas & Energy",
        "icon": "⚡",
        "description": "Refineries, oil exploration, city gas distribution & petrochem",
        "db_sectors": ["Energy", "Conglomerate"],
        "leaders": "Reliance Industries, ONGC, BPCL, IOC, GAIL",
        "flagship_symbols": [
            "RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS", "GAIL.NS",
            "OIL.NS", "PETRONET.NS", "HINDPETRO.NS", "GUJGASLTD.NS", "IGL.NS",
            "MGL.NS", "MRPL.NS",
        ],
    },
    {
        "id": "metals-mining",
        "name": "Metals, Mining & Steel",
        "icon": "⛏️",
        "description": "Primary steel production, iron ore, aluminum, zinc & mineral mining",
        "db_sectors": ["Steel", "Basic Materials"],
        "leaders": "Tata Steel, JSW Steel, Hindalco, Coal India",
        "flagship_symbols": [
            "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS", "VEDL.NS",
            "JINDALSTEL.NS", "NMDC.NS", "NATIONALUM.NS", "SAIL.NS", "APLAPOLLO.NS",
            "HINDZINC.NS",
        ],
    },
    {
        "id": "infra-industrials",
        "name": "Infrastructure & Industrials",
        "icon": "🏗️",
        "description": "Engineering, capital goods, defense equipment, ports & cement",
        "db_sectors": ["Infrastructure", "Industrials", "Cement"],
        "leaders": "Larsen & Toubro, UltraTech Cement, Adani Ports, BHEL",
        "flagship_symbols": [
            "LT.NS", "ULTRACEMCO.NS", "ADANIPORTS.NS", "GRASIM.NS", "SIEMENS.NS",
            "ABB.NS", "BEL.NS", "HAL.NS", "BHEL.NS", "AMBUJACEM.NS",
            "SHREECEM.NS", "ACC.NS",
        ],
    },
    {
        "id": "power-utilities",
        "name": "Power & Renewable Energy",
        "icon": "🔋",
        "description": "Thermal, hydro, wind & solar power generators, transmission grids",
        "db_sectors": ["Power", "Utilities"],
        "leaders": "NTPC, Power Grid, Tata Power, Adani Green",
        "flagship_symbols": [
            "NTPC.NS", "POWERGRID.NS", "TATAPOWER.NS", "ADANIGREEN.NS", "ADANIPOWER.NS",
            "NHPC.NS", "SJVN.NS", "CESC.NS", "TORNTPOWER.NS", "SUZLON.NS",
            "JSWENERGY.NS", "BHEL.NS",
        ],
    },
    {
        "id": "telecom-media",
        "name": "Telecommunications & Media",
        "icon": "📡",
        "description": "Cellular telecom operators, optical fiber networks & media broadcast",
        "db_sectors": ["Telecom", "Communication Services"],
        "leaders": "Bharti Airtel, Tata Comm, Indus Towers, Zee",
        "flagship_symbols": [
            "BHARTIARTL.NS", "TATACOMM.NS", "INDUSTOWER.NS", "IDEA.NS", "ZEEL.NS",
            "PVRINOX.NS", "NAUKRI.NS", "SUNTV.NS", "SAREGAMA.NS", "NETWORK18.NS",
            "HATHWAY.NS", "NAZARA.NS",
        ],
    },
    {
        "id": "real-estate",
        "name": "Real Estate & Realty",
        "icon": "🏢",
        "description": "Residential & commercial property developers, SEZs & REITs",
        "db_sectors": ["Real Estate"],
        "leaders": "DLF, Godrej Properties, Oberoi Realty, Prestige",
        "flagship_symbols": [
            "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS", "PHOENIXLTD.NS",
            "BRIGADE.NS", "SOBHA.NS", "LODHA.NS", "SUNTECK.NS",
        ],
    },
    {
        "id": "consumer-durables",
        "name": "Consumer Durables & Retail",
        "icon": "🛍️",
        "description": "Electronics, electrical consumer goods, lifestyle retail & paints",
        "db_sectors": ["Consumer Cyclical", "Paints"],
        "leaders": "Titan Company, Trent, Asian Paints, Havells",
        "flagship_symbols": [
            "TITAN.NS", "TRENT.NS", "ASIANPAINT.NS", "HAVELLS.NS", "BERGEPAINT.NS",
            "VOLTAS.NS", "DIXON.NS", "BATAINDIA.NS", "WHIRLPOOL.NS", "CROMPTON.NS",
            "KAJARIACER.NS", "BLUESTARCO.NS", "POLYCAB.NS",
        ],
    },
    {
        "id": "all-sectors",
        "name": "Diversified (All Sectors)",
        "icon": "🌐",
        "description": "Multi-sector universe combining top blue-chip leaders from all industries",
        "db_sectors": [],
        "leaders": "Nifty 50 & broad-market leaders",
        "flagship_symbols": [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS",
            "LT.NS", "BAJFINANCE.NS", "MARUTI.NS", "TATAMOTORS.NS", "SUNPHARMA.NS",
            "AXISBANK.NS", "NTPC.NS", "TITAN.NS", "POWERGRID.NS", "TATASTEEL.NS",
        ],
    },
]

AVAILABLE_SECTORS = [s["name"] for s in INDIAN_STOCK_MARKET_SECTORS]
AVAILABLE_THEMES = []


# ============================================================
# CREATE CUSTOM INDEX
# ============================================================

def create_custom_index(
    conn,
    user_id: int,
    name: str,
    stock_symbols: List[str],
    top_n: int,
    description: str = None,
    sector: str = None,
    theme: str = None,
    weight_strategy: str = "EQUAL",
    custom_weights: List[float] = None,
) -> Dict:
    """
    Create a new custom index.

    Steps:
    1. Validate inputs (top_n <= len(stock_symbols))
    2. Verify all stock symbols exist in DB
    3. Create index record
    4. Add all stocks as universe constituents
    5. Rank stocks by market cap and mark top_n as active
    """

    # Validate top_n
    if top_n > len(stock_symbols):
        return {
            "success": False,
            "message": f"Top {top_n} cannot exceed universe size ({len(stock_symbols)} stocks).",
        }

    if top_n < 1:
        return {
            "success": False,
            "message": "Top N must be at least 1.",
        }

    if len(stock_symbols) < 2:
        return {
            "success": False,
            "message": "Universe must contain at least 2 stocks.",
        }

    # Validate weight strategy
    valid_strategies = ["EQUAL", "MARKET_CAP", "CUSTOM", "PERFORMANCE"]
    if weight_strategy not in valid_strategies:
        return {
            "success": False,
            "message": f"Invalid weight strategy. Choose from: {', '.join(valid_strategies)}",
        }

    # Custom weights validation
    if weight_strategy == "CUSTOM":
        if not custom_weights or len(custom_weights) != top_n:
            return {
                "success": False,
                "message": f"Custom weights must have exactly {top_n} values.",
            }
        if abs(sum(custom_weights) - 100.0) > 0.01:
            return {
                "success": False,
                "message": "Custom weights must sum to 100%.",
            }

    cursor = conn.cursor(dictionary=True)

    try:
        # Verify all symbols exist in stocks table
        placeholders = ", ".join(["%s"] * len(stock_symbols))
        cursor.execute(
            f"SELECT id, symbol, name, sector FROM stocks WHERE symbol IN ({placeholders})",
            tuple(stock_symbols),
        )
        found_stocks = cursor.fetchall()
        found_symbols = {s["symbol"] for s in found_stocks}

        missing = set(stock_symbols) - found_symbols
        if missing:
            return {
                "success": False,
                "message": f"Stocks not found in database: {', '.join(missing)}",
            }

        # Create index record
        cursor.execute(
            """
            INSERT INTO custom_indexes
                (user_id, name, description, sector, theme,
                 universe_size, top_n, weight_strategy, rebalance_frequency)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'SEMI_ANNUAL')
            """,
            (
                user_id, name, description, sector, theme,
                len(stock_symbols), top_n, weight_strategy,
            ),
        )
        index_id = cursor.lastrowid

        # Fast batch price lookup for all found constituents
        from app.services.yfinance_service import get_batch_basic_prices
        found_syms = [s["symbol"] for s in found_stocks]
        batch_prices = get_batch_basic_prices(found_syms)

        order_map = {sym: idx for idx, sym in enumerate(stock_symbols)}
        stock_prices = []
        for stock in found_stocks:
            p_data = batch_prices.get(stock["symbol"])
            stock_prices.append({
                **stock,
                "current_price": p_data["current_price"] if p_data and p_data.get("current_price") is not None else 0.0,
            })

        # Maintain constituents in the user-selected order (Top-N order)
        stock_prices.sort(key=lambda s: order_map.get(s["symbol"], 999))

        # Insert all constituents with rank
        for rank, stock in enumerate(stock_prices, start=1):
            is_active = rank <= top_n

            # Determine custom weight if applicable
            cw = None
            if weight_strategy == "CUSTOM" and is_active:
                weight_idx = rank - 1
                if weight_idx < len(custom_weights):
                    cw = custom_weights[weight_idx]

            cursor.execute(
                """
                INSERT INTO index_constituents
                    (index_id, stock_id, is_active_in_index,
                     rank_position, custom_weight)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (index_id, stock["id"], is_active, rank, cw),
            )

        # Record initial NAV
        cursor.execute(
            """
            INSERT INTO index_value_history
                (index_id, nav, total_value)
            VALUES (%s, 100.0000, 0.00)
            """,
            (index_id,),
        )

        conn.commit()

        return {
            "success": True,
            "message": f"Custom index '{name}' created successfully!",
            "index_id": index_id,
            "universe_size": len(stock_symbols),
            "top_n": top_n,
            "active_stocks": [
                sp["symbol"]
                for sp in stock_prices[:top_n]
            ],
        }

    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Failed to create index: {str(e)}",
        }

    finally:
        cursor.close()


# ============================================================
# GET USER INDEXES
# ============================================================

def get_user_indexes(
    conn,
    user_id: int,
) -> List[Dict]:
    """
    Get all custom indexes for a user with live performance data.
    """

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                ci.id, ci.name, ci.description,
                ci.sector, ci.theme,
                ci.universe_size, ci.top_n,
                ci.weight_strategy, ci.rebalance_frequency,
                ci.is_active, ci.created_at,
                ii.total_invested, ii.current_value,
                ii.units, ii.nav, ii.status as investment_status
            FROM custom_indexes ci
            LEFT JOIN index_investments ii
                ON ii.index_id = ci.id
                AND ii.user_id = ci.user_id
                AND ii.status = 'ACTIVE'
            WHERE ci.user_id = %s AND ci.is_active = TRUE
            ORDER BY ci.created_at DESC
            """,
            (user_id,),
        )
        indexes = cursor.fetchall()

    finally:
        cursor.close()

    results = []

    for idx in indexes:

        # Calculate live NAV if invested
        total_invested = float(idx["total_invested"] or 0)
        current_value = float(idx["current_value"] or 0)

        if total_invested > 0:
            # Recalculate current value from live prices
            current_value = _calculate_live_value(
                conn, idx["id"], user_id
            )

        pnl = current_value - total_invested
        pnl_percent = (
            (pnl / total_invested) * 100
            if total_invested > 0
            else 0.0
        )

        nav = float(idx["nav"] or 100.0)

        # Count active stocks
        cursor2 = conn.cursor(dictionary=True)
        cursor2.execute(
            """
            SELECT COUNT(*) as cnt
            FROM index_constituents
            WHERE index_id = %s AND is_active_in_index = TRUE
            """,
            (idx["id"],),
        )
        active_count = cursor2.fetchone()["cnt"]
        cursor2.close()

        results.append({
            "id": idx["id"],
            "name": idx["name"],
            "description": idx["description"],
            "sector": idx["sector"],
            "theme": idx["theme"],
            "universe_size": idx["universe_size"],
            "top_n": idx["top_n"],
            "weight_strategy": idx["weight_strategy"],
            "rebalance_frequency": idx["rebalance_frequency"],
            "is_active": bool(idx["is_active"]),
            "nav": round(nav, 2),
            "nav_change": 0.0,
            "nav_change_percent": round(nav - 100.0, 2),
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "constituents_count": idx["universe_size"],
            "active_stocks_count": active_count,
            "created_at": str(idx["created_at"]) if idx["created_at"] else None,
        })

    return results


# ============================================================
# GET INDEX DETAIL
# ============================================================

def get_index_detail(
    conn,
    index_id: int,
    user_id: int,
) -> Optional[Dict]:
    """
    Get full index detail with constituents and live prices.
    """

    cursor = conn.cursor(dictionary=True)

    try:
        # Get index info
        cursor.execute(
            """
            SELECT
                ci.*,
                ii.total_invested, ii.current_value,
                ii.units, ii.nav as investment_nav,
                ii.status as investment_status
            FROM custom_indexes ci
            LEFT JOIN index_investments ii
                ON ii.index_id = ci.id
                AND ii.user_id = %s
                AND ii.status = 'ACTIVE'
            WHERE ci.id = %s AND ci.user_id = %s
            """,
            (user_id, index_id, user_id),
        )
        idx = cursor.fetchone()

        if not idx:
            return None

        # Get constituents with stock info
        cursor.execute(
            """
            SELECT
                ic.id, ic.is_active_in_index,
                ic.rank_position, ic.custom_weight,
                s.id as stock_id, s.symbol, s.name, s.sector
            FROM index_constituents ic
            JOIN stocks s ON s.id = ic.stock_id
            WHERE ic.index_id = %s
            ORDER BY ic.rank_position ASC
            """,
            (index_id,),
        )
        constituents_raw = cursor.fetchall()

    finally:
        cursor.close()

    # Fetch live prices for all constituents
    constituents = []
    active_total_price = 0.0
    active_stocks = []

    for c in constituents_raw:
        price_data = get_basic_stock_price(c["symbol"])
        current_price = (
            price_data["current_price"]
            if price_data
            else None
        )
        change_pct = (
            price_data["change_percent"]
            if price_data
            else None
        )

        if c["is_active_in_index"] and current_price:
            active_total_price += current_price
            active_stocks.append(c)

        constituents.append({
            "symbol": c["symbol"],
            "name": c["name"],
            "sector": c["sector"],
            "current_price": round(current_price, 2) if current_price else None,
            "change_percent": round(change_pct, 2) if change_pct else None,
            "market_cap": None,
            "weight_percent": None,
            "is_active_in_index": bool(c["is_active_in_index"]),
            "rank_position": c["rank_position"],
        })

    # Calculate weights for active stocks
    weight_strategy = idx["weight_strategy"]

    for c in constituents:
        if not c["is_active_in_index"]:
            c["weight_percent"] = 0.0
            continue

        if weight_strategy == "EQUAL":
            c["weight_percent"] = round(100.0 / idx["top_n"], 2)

        elif weight_strategy == "MARKET_CAP":
            if active_total_price > 0 and c["current_price"]:
                c["weight_percent"] = round(
                    (c["current_price"] / active_total_price) * 100, 2
                )
            else:
                c["weight_percent"] = round(100.0 / idx["top_n"], 2)

        elif weight_strategy == "CUSTOM":
            # Find custom weight from DB
            for cr in constituents_raw:
                if cr["symbol"] == c["symbol"] and cr["custom_weight"]:
                    c["weight_percent"] = float(cr["custom_weight"])
                    break
            else:
                c["weight_percent"] = round(100.0 / idx["top_n"], 2)

        elif weight_strategy == "PERFORMANCE":
            if active_total_price > 0 and c["current_price"]:
                c["weight_percent"] = round(
                    (c["current_price"] / active_total_price) * 100, 2
                )
            else:
                c["weight_percent"] = round(100.0 / idx["top_n"], 2)

    # Investment calculations
    total_invested = float(idx["total_invested"] or 0)
    current_value = float(idx["current_value"] or 0)

    if total_invested > 0:
        current_value = _calculate_live_value(conn, index_id, user_id)

    pnl = current_value - total_invested
    pnl_percent = (
        (pnl / total_invested) * 100
        if total_invested > 0
        else 0.0
    )

    nav = float(idx["investment_nav"] or 100.0)

    # Get performance history
    perf_cursor = conn.cursor(dictionary=True)
    try:
        perf_cursor.execute(
            """
            SELECT nav, total_value, recorded_at
            FROM index_value_history
            WHERE index_id = %s
            ORDER BY recorded_at ASC
            """,
            (index_id,),
        )
        history = perf_cursor.fetchall()
    finally:
        perf_cursor.close()

    performance_history = [
        {
            "nav": float(h["nav"]),
            "total_value": float(h["total_value"]),
            "date": str(h["recorded_at"]),
        }
        for h in history
    ]

    index_data = {
        "id": idx["id"],
        "name": idx["name"],
        "description": idx["description"],
        "sector": idx["sector"],
        "theme": idx["theme"],
        "universe_size": idx["universe_size"],
        "top_n": idx["top_n"],
        "weight_strategy": idx["weight_strategy"],
        "rebalance_frequency": idx["rebalance_frequency"],
        "is_active": bool(idx["is_active"]),
        "nav": round(nav, 2),
        "nav_change": 0.0,
        "nav_change_percent": round(nav - 100.0, 2),
        "total_invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "pnl": round(pnl, 2),
        "pnl_percent": round(pnl_percent, 2),
        "constituents_count": idx["universe_size"],
        "active_stocks_count": len(active_stocks),
        "created_at": str(idx["created_at"]) if idx["created_at"] else None,
    }

    return {
        "index": index_data,
        "constituents": constituents,
        "performance_history": performance_history,
    }


# ============================================================
# DELETE CUSTOM INDEX
# ============================================================

def delete_custom_index(
    conn,
    index_id: int,
    user_id: int,
) -> Dict:
    """Soft-delete a custom index."""

    cursor = conn.cursor(dictionary=True)

    try:
        # Verify ownership
        cursor.execute(
            "SELECT id FROM custom_indexes WHERE id = %s AND user_id = %s",
            (index_id, user_id),
        )
        if not cursor.fetchone():
            return {
                "success": False,
                "message": "Index not found or not owned by you.",
            }

        # Check for active investments
        cursor.execute(
            """
            SELECT id FROM index_investments
            WHERE index_id = %s AND user_id = %s AND status = 'ACTIVE'
            """,
            (index_id, user_id),
        )
        if cursor.fetchone():
            return {
                "success": False,
                "message": "Cannot delete index with active investments. Redeem first.",
            }

        # Soft delete
        cursor.execute(
            "UPDATE custom_indexes SET is_active = FALSE WHERE id = %s",
            (index_id,),
        )
        conn.commit()

        return {
            "success": True,
            "message": "Index deleted successfully.",
        }

    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Failed to delete index: {str(e)}",
        }

    finally:
        cursor.close()


# ============================================================
# GET STOCKS BY SECTOR (for index builder)
# ============================================================

def get_stocks_by_sector(
    conn,
    sector: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict]:
    """
    Get stocks filtered by sector for the custom index builder UI.
    Supports Indian Stock Market sector categories.
    Returns stocks with live prices, strictly prioritizing flagship market leaders.
    """

    cursor = conn.cursor(dictionary=True)

    db_sectors = []
    flagship_symbols = []

    if sector and sector not in ["Diversified (All Sectors)", "all-sectors", "Diversified", "All Sectors"]:
        # Match from INDIAN_STOCK_MARKET_SECTORS
        for s in INDIAN_STOCK_MARKET_SECTORS:
            if sector.lower() in [s["name"].lower(), s["id"].lower()]:
                db_sectors = s.get("db_sectors", [])
                flagship_symbols = s.get("flagship_symbols", [])
                break
        if not db_sectors and not flagship_symbols:
            db_sectors = [sector]
    else:
        for s in INDIAN_STOCK_MARKET_SECTORS:
            if s["id"] == "all-sectors":
                flagship_symbols = s.get("flagship_symbols", [])
                break

    stocks = []
    seen_symbols = set()

    try:
        if search and search.strip():
            search_pattern = f"%{search.strip().lower()}%"
            if db_sectors:
                format_strings = ",".join(["%s"] * len(db_sectors))
                cursor.execute(
                    f"""
                    SELECT id, symbol, name, sector, exchange
                    FROM stocks
                    WHERE sector IN ({format_strings})
                      AND (LOWER(symbol) LIKE %s OR LOWER(name) LIKE %s)
                    LIMIT 35
                    """,
                    (*db_sectors, search_pattern, search_pattern),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, symbol, name, sector, exchange
                    FROM stocks
                    WHERE LOWER(symbol) LIKE %s OR LOWER(name) LIKE %s
                    LIMIT 35
                    """,
                    (search_pattern, search_pattern),
                )
            matched_stocks = cursor.fetchall()
            flagship_map = {sym: idx for idx, sym in enumerate(flagship_symbols)}
            matched_stocks.sort(
                key=lambda s: (flagship_map.get(s["symbol"], 999), s["name"])
            )
            stocks = matched_stocks
        else:
            # 1. Fetch flagship stocks in exact designated priority order
            if flagship_symbols:
                placeholders = ",".join(["%s"] * len(flagship_symbols))
                cursor.execute(
                    f"""
                    SELECT id, symbol, name, sector, exchange
                    FROM stocks
                    WHERE symbol IN ({placeholders})
                    """,
                    tuple(flagship_symbols),
                )
                flagship_dict = {r["symbol"]: r for r in cursor.fetchall()}
                for sym in flagship_symbols:
                    if sym in flagship_dict and sym not in seen_symbols:
                        stocks.append(flagship_dict[sym])
                        seen_symbols.add(sym)

            # 2. Append secondary matching stocks from DB up to 25 total
            needed = 25 - len(stocks)
            if needed > 0 and db_sectors:
                existing_symbols = list(seen_symbols)
                sec_placeholders = ",".join(["%s"] * len(db_sectors))
                if existing_symbols:
                    ex_placeholders = ",".join(["%s"] * len(existing_symbols))
                    cursor.execute(
                        f"""
                        SELECT id, symbol, name, sector, exchange
                        FROM stocks
                        WHERE sector IN ({sec_placeholders})
                          AND symbol NOT IN ({ex_placeholders})
                        ORDER BY name
                        LIMIT %s
                        """,
                        (*db_sectors, *existing_symbols, needed),
                    )
                else:
                    cursor.execute(
                        f"""
                        SELECT id, symbol, name, sector, exchange
                        FROM stocks
                        WHERE sector IN ({sec_placeholders})
                        ORDER BY name
                        LIMIT %s
                        """,
                        (*db_sectors, needed),
                    )
                for r in cursor.fetchall():
                    if r["symbol"] not in seen_symbols:
                        stocks.append(r)
                        seen_symbols.add(r["symbol"])

    finally:
        cursor.close()

    # Fast batch price lookup for ALL returned stocks concurrently
    from app.services.yfinance_service import get_batch_basic_prices

    all_symbols = [s["symbol"] for s in stocks]
    batch_prices = get_batch_basic_prices(all_symbols) if all_symbols else {}

    results = []
    for stock in stocks:
        sym = stock["symbol"]
        price_data = batch_prices.get(sym)

        results.append({
            "symbol": sym,
            "name": stock["name"],
            "sector": stock["sector"],
            "exchange": stock["exchange"],
            "current_price": (
                price_data["current_price"]
                if price_data and "current_price" in price_data
                else None
            ),
            "change": (
                price_data["change"]
                if price_data and "change" in price_data
                else None
            ),
            "change_percent": (
                price_data["change_percent"]
                if price_data and "change_percent" in price_data
                else None
            ),
        })

    return results


# ============================================================
# GET AVAILABLE SECTORS
# ============================================================

def get_available_sectors(conn) -> List[Dict]:
    """Get all available Indian stock market sectors with stock counts and metadata."""

    cursor = conn.cursor(dictionary=True)
    counts = {}

    try:
        cursor.execute(
            """
            SELECT sector, count(*) as cnt
            FROM stocks
            WHERE sector IS NOT NULL
            GROUP BY sector
            """
        )
        counts = {r["sector"]: r["cnt"] for r in cursor.fetchall()}
    except Exception as e:
        print(f"Error fetching sector counts: {e}")
    finally:
        cursor.close()

    result = []
    for s in INDIAN_STOCK_MARKET_SECTORS:
        if s["db_sectors"]:
            total_stocks = sum(counts.get(sec, 0) for sec in s["db_sectors"])
        else:
            total_stocks = sum(counts.values())

        result.append({
            "id": s["id"],
            "name": s["name"],
            "icon": s["icon"],
            "description": s["description"],
            "leaders": s["leaders"],
            "stock_count": total_stocks,
        })

    return result


# ============================================================
# HELPER: Calculate live portfolio value
# ============================================================

def _calculate_live_value(
    conn,
    index_id: int,
    user_id: int,
) -> float:
    """
    Calculate the live value of an index investment
    by summing up current prices of all holdings.
    """

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT ih.quantity, ih.avg_buy_price, s.symbol
            FROM index_holdings ih
            JOIN index_investments ii ON ii.id = ih.investment_id
            JOIN stocks s ON s.id = ih.stock_id
            WHERE ii.index_id = %s
              AND ii.user_id = %s
              AND ii.status = 'ACTIVE'
            """,
            (index_id, user_id),
        )
        holdings = cursor.fetchall()

    finally:
        cursor.close()

    total_value = 0.0
    for h in holdings:
        price = get_current_price_only(h["symbol"])
        if price:
            total_value += price * h["quantity"]
        else:
            total_value += float(h["avg_buy_price"]) * h["quantity"]

    return total_value
