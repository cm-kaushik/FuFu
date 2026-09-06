"""
News & Market Data Aggregation Service.

Data Sources:
- NewsAPI: Financial news for stocks and sectors
- DuckDuckGo: Web search for additional market context
- Alpha Vantage: Fundamental data and market overview

All focused on Indian stock market (NSE/BSE).
"""

import os
import time
import httpx
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# Rate limiting
_LAST_REQUEST_TIME = 0.0
_MIN_DELAY = 0.5


def _rate_limit():
    """Simple rate limiter."""
    global _LAST_REQUEST_TIME
    now = time.time()
    elapsed = now - _LAST_REQUEST_TIME
    if elapsed < _MIN_DELAY:
        time.sleep(_MIN_DELAY - elapsed)
    _LAST_REQUEST_TIME = time.time()


# ============================================================
# NEWSAPI
# ============================================================

def get_stock_news(
    symbol: str,
    company_name: str = "",
    limit: int = 5,
) -> List[Dict]:
    """
    Fetch news articles for a stock from NewsAPI.
    Focuses on Indian market news.
    """

    if not NEWS_API_KEY:
        return _get_fallback_news(symbol, company_name)

    try:
        _rate_limit()

        # Clean symbol for search
        clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
        query = f"{clean_symbol} OR {company_name}" if company_name else clean_symbol
        query += " India stock market NSE"

        with httpx.Client(timeout=10) as client:
            response = client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": limit,
                    "apiKey": NEWS_API_KEY,
                },
            )

            if response.status_code != 200:
                return _get_fallback_news(symbol, company_name)

            data = response.json()
            articles = data.get("articles", [])

            return [
                {
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "source": a.get("source", {}).get("name", "Unknown"),
                    "url": a.get("url", ""),
                    "published_at": a.get("publishedAt", ""),
                    "image": a.get("urlToImage", ""),
                }
                for a in articles
                if a.get("title")
            ]

    except Exception as e:
        print(f"NewsAPI error: {e}")
        return _get_fallback_news(symbol, company_name)


def get_sector_news(
    sector: str,
    limit: int = 5,
) -> List[Dict]:
    """Fetch news for a sector from NewsAPI."""

    if not NEWS_API_KEY:
        return []

    try:
        _rate_limit()

        query = f"{sector} India stock market sector"

        with httpx.Client(timeout=10) as client:
            response = client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": limit,
                    "apiKey": NEWS_API_KEY,
                },
            )

            if response.status_code != 200:
                return []

            data = response.json()
            articles = data.get("articles", [])

            return [
                {
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "source": a.get("source", {}).get("name", "Unknown"),
                    "url": a.get("url", ""),
                    "published_at": a.get("publishedAt", ""),
                }
                for a in articles
                if a.get("title")
            ]

    except Exception as e:
        print(f"Sector news error: {e}")
        return []


# ============================================================
# DUCKDUCKGO SEARCH
# ============================================================

def search_duckduckgo(
    query: str,
    max_results: int = 5,
) -> List[Dict]:
    """
    Search DuckDuckGo for market context.
    Uses the duckduckgo-search library.
    """

    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(
                f"{query} India stock market NSE",
                max_results=max_results,
            ):
                results.append({
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "url": r.get("href", ""),
                })

        return results

    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        return []


# ============================================================
# ALPHA VANTAGE
# ============================================================

def get_alpha_vantage_overview(
    symbol: str,
) -> Optional[Dict]:
    """
    Get company overview from Alpha Vantage.
    Includes market cap, PE ratio, sector, etc.
    """

    if not ALPHA_VANTAGE_KEY:
        return None

    try:
        _rate_limit()

        # Alpha Vantage uses symbols without .NS suffix
        clean_symbol = symbol.replace(".NS", "").replace(".BO", "")

        with httpx.Client(timeout=10) as client:
            response = client.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "OVERVIEW",
                    "symbol": f"{clean_symbol}.BSE",
                    "apikey": ALPHA_VANTAGE_KEY,
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()

            if "Symbol" not in data:
                return None

            return {
                "symbol": data.get("Symbol", ""),
                "name": data.get("Name", ""),
                "description": data.get("Description", ""),
                "sector": data.get("Sector", ""),
                "industry": data.get("Industry", ""),
                "market_cap": data.get("MarketCapitalization", "0"),
                "pe_ratio": data.get("PERatio", "N/A"),
                "eps": data.get("EPS", "N/A"),
                "dividend_yield": data.get("DividendYield", "0"),
                "52_week_high": data.get("52WeekHigh", "0"),
                "52_week_low": data.get("52WeekLow", "0"),
                "analyst_target": data.get("AnalystTargetPrice", "N/A"),
            }

    except Exception as e:
        print(f"Alpha Vantage error: {e}")
        return None


def get_alpha_vantage_quote(
    symbol: str,
) -> Optional[Dict]:
    """Get real-time quote from Alpha Vantage."""

    if not ALPHA_VANTAGE_KEY:
        return None

    try:
        _rate_limit()

        clean_symbol = symbol.replace(".NS", "").replace(".BO", "")

        with httpx.Client(timeout=10) as client:
            response = client.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": f"{clean_symbol}.BSE",
                    "apikey": ALPHA_VANTAGE_KEY,
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()
            quote = data.get("Global Quote", {})

            if not quote:
                return None

            return {
                "price": quote.get("05. price", "0"),
                "change": quote.get("09. change", "0"),
                "change_percent": quote.get("10. change percent", "0%"),
                "volume": quote.get("06. volume", "0"),
                "previous_close": quote.get("08. previous close", "0"),
            }

    except Exception as e:
        print(f"Alpha Vantage quote error: {e}")
        return None


# ============================================================
# MARKET CONTEXT AGGREGATOR
# ============================================================

def get_market_context(
    symbol: str,
    company_name: str = "",
    sector: str = "",
) -> Dict:
    """
    Aggregate market context from all sources.
    Used by the AI advisor to make informed recommendations.
    """

    context = {
        "news": [],
        "sector_news": [],
        "web_results": [],
        "fundamentals": None,
        "market_quote": None,
    }

    # Get stock news
    context["news"] = get_stock_news(
        symbol, company_name, limit=5
    )

    # Get sector news
    if sector:
        context["sector_news"] = get_sector_news(
            sector, limit=3
        )

    # DuckDuckGo search for context
    search_query = f"{company_name or symbol} stock analysis"
    context["web_results"] = search_duckduckgo(
        search_query, max_results=3
    )

    # Alpha Vantage fundamentals
    context["fundamentals"] = get_alpha_vantage_overview(symbol)

    # Alpha Vantage quote
    context["market_quote"] = get_alpha_vantage_quote(symbol)

    return context


# ============================================================
# FALLBACK NEWS
# ============================================================

def _get_fallback_news(
    symbol: str,
    company_name: str = "",
) -> List[Dict]:
    """
    Fallback when NewsAPI is not available.
    Uses DuckDuckGo to search for recent news.
    """

    query = f"{company_name or symbol} latest news stock"
    results = search_duckduckgo(query, max_results=5)

    return [
        {
            "title": r["title"],
            "description": r["body"],
            "source": "Web Search",
            "url": r["url"],
            "published_at": "",
            "image": "",
        }
        for r in results
    ]
