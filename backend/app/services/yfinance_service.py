"""
Yahoo Finance service for the Fufu investment application.

Optimized for fast dashboard loading.

Features:
- Separate basic-price cache
- Detailed-price cache
- Historical-data cache
- Separate 52-week statistics cache
- Request throttling
- Retry with exponential backoff
- Stale-cache fallback
- No ticker.info / fast_info calls
- Safe handling of Yahoo Finance failures

IMPORTANT:
- Dashboard/popular stocks use BASIC price data only.
- Portfolio uses BASIC price data only.
- Detailed stock pages can still fetch 52-week statistics.
"""

import time
import threading
from typing import Optional, List, Dict, Any

import yfinance as yf
from yfinance import data as _yfd
import yfinance.utils as _yfu

# Compatibility patch: modernize User-Agent (Yahoo blocks 2014 Chrome UA)
try:
    _yfd.TickerData.user_agent_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
except Exception:
    pass

# Compatibility patch: fix DST issue for pandas 3.x
try:
    _orig_fix_dst = _yfu.fix_Yahoo_dst_issue
    def _safe_fix_dst(df, interval):
        try:
            return _orig_fix_dst(df, interval)
        except Exception:
            return df
    _yfu.fix_Yahoo_dst_issue = _safe_fix_dst
except Exception:
    pass



# ============================================================
# CONFIGURATION
# ============================================================

# Basic/current price remains fresh for 5 minutes.
PRICE_CACHE_TTL = 300

# Historical charts remain cached for 30 minutes.
HISTORY_CACHE_TTL = 1800

# 52-week statistics remain cached for 1 day.
WEEK52_CACHE_TTL = 86400

# Minimum time between Yahoo requests.
#
# 1.0 seconds is required to prevent Yahoo Finance 429 Too Many Requests errors.
REQUEST_DELAY = 1.0

# Number of attempts when Yahoo temporarily fails.
MAX_RETRIES = 3

# Retry delays after failures.
RETRY_DELAYS = [2, 5, 10]


# ============================================================
# CACHE STORAGE
# ============================================================

# BASIC PRICE CACHE
#
# Used by:
# - Dashboard
# - Popular stocks
# - Portfolio
#
# Does NOT contain 52-week data.
#
_BASIC_PRICE_CACHE: Dict[str, Dict[str, Any]] = {}


# DETAILED PRICE CACHE
#
# Used by:
# - Stock detail page
#
# Contains:
# - current price
# - change
# - 52-week high
# - 52-week low
# etc.
#
_PRICE_CACHE: Dict[str, Dict[str, Any]] = {}


# Historical chart cache.
_HISTORY_CACHE: Dict[str, Dict[str, Any]] = {}


# 52-week cache.
_WEEK52_CACHE: Dict[str, Dict[str, Any]] = {}


# ============================================================
# THREAD SAFETY
# ============================================================

_CACHE_LOCK = threading.Lock()

_YAHOO_LOCK = threading.Lock()

_LAST_YAHOO_REQUEST = 0.0


# ============================================================
# SYMBOL NORMALIZATION
# ============================================================

def _normalize_symbol(symbol: str) -> str:
    """Normalize stock symbols."""

    if not symbol:
        return ""

    return symbol.strip().upper()


# ============================================================
# BASIC PRICE CACHE
# ============================================================

def _get_cached_basic_price(
    symbol: str
) -> Optional[Dict]:

    symbol = _normalize_symbol(symbol)

    with _CACHE_LOCK:

        cached = _BASIC_PRICE_CACHE.get(symbol)

        if not cached:
            return None

        age = time.time() - cached["timestamp"]

        if age < PRICE_CACHE_TTL:
            return cached["data"]

        return None


def _get_stale_basic_price(
    symbol: str
) -> Optional[Dict]:

    symbol = _normalize_symbol(symbol)

    with _CACHE_LOCK:

        cached = _BASIC_PRICE_CACHE.get(symbol)

        if cached:
            return cached["data"]

        return None


def _set_cached_basic_price(
    symbol: str,
    data: Dict
) -> None:

    symbol = _normalize_symbol(symbol)

    with _CACHE_LOCK:

        _BASIC_PRICE_CACHE[symbol] = {
            "data": data,
            "timestamp": time.time(),
        }


# ============================================================
# DETAILED PRICE CACHE
# ============================================================

def _get_cached_price(
    symbol: str
) -> Optional[Dict]:

    symbol = _normalize_symbol(symbol)

    with _CACHE_LOCK:

        cached = _PRICE_CACHE.get(symbol)

        if not cached:
            return None

        age = time.time() - cached["timestamp"]

        if age < PRICE_CACHE_TTL:
            return cached["data"]

        return None


def _get_stale_price(
    symbol: str
) -> Optional[Dict]:

    symbol = _normalize_symbol(symbol)

    with _CACHE_LOCK:

        cached = _PRICE_CACHE.get(symbol)

        if cached:
            return cached["data"]

        return None


def _set_cached_price(
    symbol: str,
    data: Dict
) -> None:

    symbol = _normalize_symbol(symbol)

    with _CACHE_LOCK:

        _PRICE_CACHE[symbol] = {
            "data": data,
            "timestamp": time.time(),
        }


# ============================================================
# HISTORICAL CACHE
# ============================================================

def _get_cached_history(
    symbol: str,
    period: str
) -> Optional[List[Dict]]:

    symbol = _normalize_symbol(symbol)

    cache_key = f"{symbol}_{period}"

    with _CACHE_LOCK:

        cached = _HISTORY_CACHE.get(cache_key)

        if not cached:
            return None

        age = time.time() - cached["timestamp"]

        if age < HISTORY_CACHE_TTL:
            return cached["data"]

        return None


def _get_stale_history(
    symbol: str,
    period: str
) -> Optional[List[Dict]]:

    symbol = _normalize_symbol(symbol)

    cache_key = f"{symbol}_{period}"

    with _CACHE_LOCK:

        cached = _HISTORY_CACHE.get(cache_key)

        if cached:
            return cached["data"]

        return None


def _set_cached_history(
    symbol: str,
    period: str,
    data: List[Dict]
) -> None:

    symbol = _normalize_symbol(symbol)

    cache_key = f"{symbol}_{period}"

    with _CACHE_LOCK:

        _HISTORY_CACHE[cache_key] = {
            "data": data,
            "timestamp": time.time(),
        }


# ============================================================
# 52-WEEK CACHE
# ============================================================

def _get_cached_week52(
    symbol: str
) -> Optional[Dict]:

    symbol = _normalize_symbol(symbol)

    with _CACHE_LOCK:

        cached = _WEEK52_CACHE.get(symbol)

        if not cached:
            return None

        age = time.time() - cached["timestamp"]

        if age < WEEK52_CACHE_TTL:
            return cached

        return None


def _set_cached_week52(
    symbol: str,
    high: float,
    low: float
) -> None:

    symbol = _normalize_symbol(symbol)

    with _CACHE_LOCK:

        _WEEK52_CACHE[symbol] = {
            "high": high,
            "low": low,
            "timestamp": time.time(),
        }


# ============================================================
# YAHOO REQUEST THROTTLING
# ============================================================

def _wait_before_yahoo_request() -> None:
    """
    Ensure a minimum delay between Yahoo requests.
    """

    global _LAST_YAHOO_REQUEST

    with _YAHOO_LOCK:

        now = time.time()

        elapsed = now - _LAST_YAHOO_REQUEST

        if elapsed < REQUEST_DELAY:

            time.sleep(
                REQUEST_DELAY - elapsed
            )

        _LAST_YAHOO_REQUEST = time.time()


# ============================================================
# SAFE YAHOO HISTORY REQUEST
# ============================================================

def _fetch_history_from_yahoo(
    symbol: str,
    period: str,
    interval: str
):

    """
    Safely fetch data from Yahoo Finance.

    Uses:
    - throttling
    - retries
    - no ticker.info
    """

    symbol = _normalize_symbol(symbol)

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:

            _wait_before_yahoo_request()

            ticker = yf.Ticker(symbol)

            hist = ticker.history(
                period=period,
                interval=interval,
                auto_adjust=False,
                actions=False
            )

            if hist is None or hist.empty:

                raise ValueError(
                    f"Yahoo returned empty data for {symbol}"
                )

            return hist

        except Exception as exc:

            last_error = exc

            print(
                f"Yahoo request failed for {symbol} "
                f"(attempt {attempt + 1}/{MAX_RETRIES}): "
                f"{exc}"
            )

            if attempt < MAX_RETRIES - 1:

                delay = RETRY_DELAYS[
                    min(
                        attempt,
                        len(RETRY_DELAYS) - 1
                    )
                ]

                time.sleep(delay)

    print(
        f"Yahoo Finance unavailable for {symbol}. "
        f"Last error: {last_error}"
    )

    return None


# ============================================================
# BASIC CURRENT PRICE
# ============================================================

def get_basic_stock_price(
    symbol: str
) -> Optional[Dict]:

    """
    FAST price lookup.

    Used by:
    - Dashboard popular stocks
    - Portfolio
    - Portfolio calculations

    IMPORTANT:
    This only downloads 5 days of data.

    It DOES NOT download 1 year of data.

    This is the main dashboard optimization.
    """

    symbol = _normalize_symbol(symbol)

    if not symbol:
        return None

    # --------------------------------------------------------
    # 1. Fresh cache
    # --------------------------------------------------------

    cached = _get_cached_basic_price(symbol)

    if cached is not None:
        return cached

    # --------------------------------------------------------
    # 2. Fetch only 5 days
    # --------------------------------------------------------

    hist = _fetch_history_from_yahoo(
        symbol=symbol,
        period="5d",
        interval="1d"
    )

    if hist is None:

        stale = _get_stale_basic_price(symbol)

        if stale is not None:

            print(
                f"Using stale basic price for {symbol}"
            )

            return stale

        return None

    # --------------------------------------------------------
    # 3. Process data
    # --------------------------------------------------------

    try:

        hist = hist.dropna(
            subset=["Close"]
        )

        if hist.empty:
            return None

        latest = hist.iloc[-1]

        current_price = float(
            latest["Close"]
        )

        if len(hist) >= 2:

            previous_close = float(
                hist.iloc[-2]["Close"]
            )

        else:

            previous_close = current_price

        change = round(
            current_price - previous_close,
            2
        )

        change_percent = (
            round(
                (change / previous_close) * 100,
                2
            )
            if previous_close
            else 0.0
        )

        day_high = (
            float(latest["High"])
            if "High" in latest
            else current_price
        )

        day_low = (
            float(latest["Low"])
            if "Low" in latest
            else current_price
        )

        open_price = (
            float(latest["Open"])
            if "Open" in latest
            else current_price
        )

        volume = 0

        if "Volume" in latest:

            try:
                volume = int(latest["Volume"])
            except Exception:
                volume = 0

        result = {

            "current_price": round(
                current_price,
                2
            ),

            "previous_close": round(
                previous_close,
                2
            ),

            "change": change,

            "change_percent": change_percent,

            "day_high": round(
                day_high,
                2
            ),

            "day_low": round(
                day_low,
                2
            ),

            "volume": volume,

            # These remain unavailable in the
            # fast endpoint.
            "market_cap": 0.0,

            "pe_ratio": None,

            # These are filled in by get_stock_price()
            # for detailed stock pages.
            "fifty_two_week_high": 0.0,

            "fifty_two_week_low": 0.0,

            "open_price": round(
                open_price,
                2
            ),
        }

        # ----------------------------------------------------
        # 4. Cache basic price
        # ----------------------------------------------------

        _set_cached_basic_price(
            symbol,
            result
        )

        return result

    except Exception as exc:

        print(
            f"Error processing basic price "
            f"for {symbol}: {exc}"
        )

        stale = _get_stale_basic_price(symbol)

        if stale is not None:
            return stale

        return None


# ============================================================
# FAST BATCH BASIC PRICE LOOKUP
# ============================================================

def get_batch_basic_prices(symbols: List[str]) -> Dict[str, Optional[Dict]]:
    """
    Fast parallel price lookup for multiple stocks.
    Checks memory cache first, then fetches missing symbols concurrently via Yahoo v8 chart API.
    """
    import httpx
    from concurrent.futures import ThreadPoolExecutor

    results = {}
    missing = []

    now = time.time()
    with _CACHE_LOCK:
        for sym in symbols:
            norm = _normalize_symbol(sym)
            cached = _BASIC_PRICE_CACHE.get(norm)
            if cached and (now - cached.get("timestamp", 0) < PRICE_CACHE_TTL):
                results[norm] = cached["data"]
            else:
                missing.append(norm)

    if not missing:
        return results

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    def _fetch_single(sym):
        fetch_sym = "TMPV.NS" if sym == "TATAMOTORS.NS" else sym
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{fetch_sym}?interval=1d&range=2d"
            r = httpx.get(url, headers=headers, timeout=3.5)
            if r.status_code == 200:
                chart_data = r.json().get("chart", {}).get("result", [{}])[0]
                meta = chart_data.get("meta", {})
                price = meta.get("regularMarketPrice")
                prev = meta.get("chartPreviousClose")
                if price is not None:
                    pct = round(((price - prev) / prev) * 100, 2) if prev else 0.0
                    change = round(price - prev, 2) if prev else 0.0
                    stock_res = {
                        "current_price": round(float(price), 2),
                        "previous_close": round(float(prev), 2) if prev else round(float(price), 2),
                        "change": change,
                        "change_percent": pct,
                        "day_high": round(float(meta.get("regularMarketDayHigh", price)), 2),
                        "day_low": round(float(meta.get("regularMarketDayLow", price)), 2),
                        "volume": int(meta.get("regularMarketVolume", 0)),
                        "market_cap": 0.0,
                        "pe_ratio": None,
                        "fifty_two_week_high": 0.0,
                        "fifty_two_week_low": 0.0,
                        "open_price": round(float(meta.get("regularMarketOpen", price)), 2),
                    }
                    return sym, stock_res
        except Exception:
            pass

        stale = _get_stale_basic_price(sym)
        return sym, stale

    max_w = min(12, max(1, len(missing)))
    with ThreadPoolExecutor(max_workers=max_w) as executor:
        fetched_items = list(executor.map(_fetch_single, missing))

    with _CACHE_LOCK:
        for sym, data in fetched_items:
            results[sym] = data
            if data:
                _BASIC_PRICE_CACHE[sym] = {
                    "data": data,
                    "timestamp": time.time(),
                }

    return results


# ============================================================
# DETAILED STOCK PRICE
# ============================================================

def get_stock_price(
    symbol: str
) -> Optional[Dict]:

    """
    Full stock price information.

    Used for detailed stock information.

    Difference from get_basic_stock_price():

        get_basic_stock_price()
            -> 5d data only

        get_stock_price()
            -> 5d data
            -> 52-week data when needed
    """

    symbol = _normalize_symbol(symbol)

    if not symbol:
        return None

    # --------------------------------------------------------
    # 1. Detailed cache
    # --------------------------------------------------------

    cached = _get_cached_price(symbol)

    if cached is not None:
        return cached

    # --------------------------------------------------------
    # 2. Get basic price
    #
    # This may already be cached from the Dashboard.
    # --------------------------------------------------------

    basic = get_basic_stock_price(symbol)

    if basic is None:

        stale = _get_stale_price(symbol)

        if stale is not None:
            return stale

        return None

    # --------------------------------------------------------
    # 3. Get 52-week data
    # --------------------------------------------------------

    week52 = _get_cached_week52(symbol)

    if week52:

        week52_high = week52["high"]
        week52_low = week52["low"]

    else:

        long_hist = _fetch_history_from_yahoo(
            symbol=symbol,
            period="1y",
            interval="1d"
        )

        if long_hist is not None:

            try:

                long_hist = long_hist.dropna(
                    subset=["High", "Low"]
                )

                if not long_hist.empty:

                    week52_high = round(
                        float(long_hist["High"].max()),
                        2
                    )

                    week52_low = round(
                        float(long_hist["Low"].min()),
                        2
                    )

                    _set_cached_week52(
                        symbol,
                        week52_high,
                        week52_low
                    )

                else:

                    week52_high = 0.0
                    week52_low = 0.0

            except Exception as exc:

                print(
                    f"Error calculating 52-week data "
                    f"for {symbol}: {exc}"
                )

                week52_high = 0.0
                week52_low = 0.0

        else:

            week52_high = 0.0
            week52_low = 0.0

    # --------------------------------------------------------
    # 4. Combine basic + 52-week data
    # --------------------------------------------------------

    result = {
        **basic,

        "fifty_two_week_high": week52_high,

        "fifty_two_week_low": week52_low,
    }

    # --------------------------------------------------------
    # 5. Cache detailed result
    # --------------------------------------------------------

    _set_cached_price(
        symbol,
        result
    )

    return result


# ============================================================
# HISTORICAL DATA
# ============================================================

def get_stock_history(
    symbol: str,
    period: str = "1mo"
) -> List[Dict]:

    """
    Fetch historical stock data.

    Supported:
        1d
        5d
        1mo
        3mo
        6mo
        1y
        5y
    """

    symbol = _normalize_symbol(symbol)

    if not symbol:
        return []

    # --------------------------------------------------------
    # 1. Cache
    # --------------------------------------------------------

    cached = _get_cached_history(
        symbol,
        period
    )

    if cached is not None:
        return cached

    # --------------------------------------------------------
    # 2. Interval mapping
    # --------------------------------------------------------

    interval_map = {

        "1d": "5m",

        "5d": "15m",

        "1mo": "1d",

        "3mo": "1d",

        "6mo": "1d",

        "1y": "1wk",

        "5y": "1mo",
    }

    interval = interval_map.get(
        period,
        "1d"
    )

    # --------------------------------------------------------
    # 3. Fetch
    # --------------------------------------------------------

    hist = _fetch_history_from_yahoo(
        symbol=symbol,
        period=period,
        interval=interval
    )

    if hist is None:

        stale = _get_stale_history(
            symbol,
            period
        )

        if stale is not None:
            return stale

        return []

    # --------------------------------------------------------
    # 4. Convert to API format
    # --------------------------------------------------------

    try:

        history: List[Dict] = []

        hist = hist.dropna(
            subset=["Close"]
        )

        for date, row in hist.iterrows():

            try:
                volume = int(
                    row["Volume"]
                )
            except Exception:
                volume = 0

            try:

                history.append({

                    "date": (
                        date.strftime(
                            "%Y-%m-%d %H:%M"
                        )
                        if interval in [
                            "5m",
                            "15m"
                        ]
                        else date.strftime(
                            "%Y-%m-%d"
                        )
                    ),

                    "open": round(
                        float(row["Open"]),
                        2
                    ),

                    "high": round(
                        float(row["High"]),
                        2
                    ),

                    "low": round(
                        float(row["Low"]),
                        2
                    ),

                    "close": round(
                        float(row["Close"]),
                        2
                    ),

                    "volume": volume,
                })

            except Exception as exc:

                print(
                    f"Skipping invalid history row "
                    f"for {symbol}: {exc}"
                )

        _set_cached_history(
            symbol,
            period,
            history
        )

        return history

    except Exception as exc:

        print(
            f"Error processing history "
            f"for {symbol}: {exc}"
        )

        stale = _get_stale_history(
            symbol,
            period
        )

        if stale is not None:
            return stale

        return []


# ============================================================
# CURRENT PRICE ONLY
# ============================================================

def get_current_price_only(
    symbol: str
) -> Optional[float]:

    """
    FASTEST current-price lookup.

    Used by portfolio_service.py.

    IMPORTANT:
    This does NOT call get_stock_price().

    Therefore it does NOT fetch 52-week data.
    """

    symbol = _normalize_symbol(symbol)

    if not symbol:
        return None

    # --------------------------------------------------------
    # 1. Basic cache
    # --------------------------------------------------------

    cached = _get_cached_basic_price(symbol)

    if cached is not None:

        price = cached.get(
            "current_price"
        )

        if price is not None:
            return float(price)

    # --------------------------------------------------------
    # 2. Detailed cache
    # --------------------------------------------------------

    cached = _get_cached_price(symbol)

    if cached is not None:

        price = cached.get(
            "current_price"
        )

        if price is not None:
            return float(price)

    # --------------------------------------------------------
    # 3. Fetch BASIC price only
    # --------------------------------------------------------

    result = get_basic_stock_price(symbol)

    if result:

        price = result.get(
            "current_price"
        )

        if price is not None:
            return float(price)

    # --------------------------------------------------------
    # 4. Stale basic cache
    # --------------------------------------------------------

    stale = _get_stale_basic_price(symbol)

    if stale:

        price = stale.get(
            "current_price"
        )

        if price is not None:

            print(
                f"Using stale basic price for {symbol}"
            )

            return float(price)

    # --------------------------------------------------------
    # 5. Stale detailed cache
    # --------------------------------------------------------

    stale = _get_stale_price(symbol)

    if stale:

        price = stale.get(
            "current_price"
        )

        if price is not None:

            print(
                f"Using stale detailed price for {symbol}"
            )

            return float(price)

    return None


# ============================================================
# CACHE CONTROL
# ============================================================

def clear_price_cache() -> None:
    """Clear current-price caches."""

    with _CACHE_LOCK:

        _BASIC_PRICE_CACHE.clear()

        _PRICE_CACHE.clear()


def clear_history_cache() -> None:
    """Clear historical cache."""

    with _CACHE_LOCK:

        _HISTORY_CACHE.clear()


def clear_all_cache() -> None:
    """Clear all Yahoo Finance caches."""

    with _CACHE_LOCK:

        _BASIC_PRICE_CACHE.clear()

        _PRICE_CACHE.clear()

        _HISTORY_CACHE.clear()

        _WEEK52_CACHE.clear()