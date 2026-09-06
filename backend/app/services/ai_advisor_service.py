"""
AI Trading Advisor Service.

Powered by Groq API for fast LLM inference.

Provides intelligent buy/sell advice by analyzing:
- Current stock price and trends
- Recent news and sentiment
- Sector performance
- Technical indicators (price-based)
- Fundamental data (Alpha Vantage)

Works for both:
- Individual stock trades
- Custom index investments

Indian market focused (NSE/BSE).

Example scenario:
"TCS price dropped 5% due to a minor issue.
 AI Advisor says: This is a short-term dip. Long-term fundamentals
 remain strong. Consider holding or buying more."
"""

import os
import json
from typing import Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


# ============================================================
# GET TRADE ADVICE
# ============================================================

def get_trade_advice(
    conn,
    user_id: int,
    symbol: str = None,
    index_id: int = None,
    action: str = "BUY",
    amount: float = None,
    quantity: int = None,
) -> Dict:
    """
    Get AI-powered trading advice before executing a trade.

    Returns a structured recommendation with:
    - sentiment (BULLISH/BEARISH/NEUTRAL/CAUTIOUS)
    - confidence score (0-100)
    - detailed reasoning
    - news summary
    - risk assessment
    - key factors
    """

    from app.services.news_service import get_market_context
    from app.services.yfinance_service import (
        get_basic_stock_price,
        get_stock_history,
    )

    # Determine what we're analyzing
    if symbol:
        # Individual stock
        stock_name = _get_stock_name(conn, symbol)
        sector = _get_stock_sector(conn, symbol)

        # Get price data
        price_data = get_basic_stock_price(symbol)
        history = get_stock_history(symbol, "1mo")

        # Get market context
        context = get_market_context(
            symbol, stock_name, sector
        )

        analysis_target = f"{stock_name} ({symbol})"
        context_type = f"STOCK_{action}"

    elif index_id:
        # Custom index
        index_info = _get_index_info(conn, index_id, user_id)
        if not index_info:
            return _default_response(
                "Unable to find index information."
            )

        analysis_target = index_info["name"]
        context_type = f"INDEX_{action}"
        price_data = None
        history = []
        sector = index_info.get("sector", "")

        # Aggregate context from all active stocks
        context = {"news": [], "sector_news": [], "web_results": []}
        for stock in index_info.get("active_stocks", [])[:3]:
            stock_context = get_market_context(
                stock["symbol"],
                stock["name"],
                sector,
            )
            context["news"].extend(stock_context.get("news", [])[:2])

    else:
        return _default_response(
            "Please provide a stock symbol or index ID."
        )

    # Build the prompt
    prompt = _build_analysis_prompt(
        analysis_target=analysis_target,
        action=action,
        price_data=price_data,
        history=history,
        context=context,
        amount=amount,
        quantity=quantity,
    )

    # Call Groq AI
    ai_response = _call_groq(prompt)

    # Parse the response
    result = _parse_ai_response(ai_response)

    # Log the interaction
    _log_advice(
        conn, user_id, context_type,
        symbol, index_id,
        prompt, ai_response,
        result.get("sentiment", "NEUTRAL"),
        result.get("confidence", 50.0),
        _summarize_news(context.get("news", [])),
    )

    return result


# ============================================================
# BUILD ANALYSIS PROMPT
# ============================================================

def _build_analysis_prompt(
    analysis_target: str,
    action: str,
    price_data: Dict = None,
    history: List = None,
    context: Dict = None,
    amount: float = None,
    quantity: int = None,
) -> str:
    """Build a structured prompt for the AI model."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    prompt = f"""You are an expert Indian stock market analyst and trading advisor.
A user wants to {action} {analysis_target} on the NSE/BSE.
Current date/time: {now}

INSTRUCTIONS:
- Analyze the stock/index based on the data provided below
- Consider both short-term and long-term perspectives
- Factor in Indian market conditions
- Be honest about risks
- Provide clear, actionable advice
- If a stock dropped due to a minor/temporary issue, say so clearly
- If there are fundamental concerns, warn the user

"""

    # Price data
    if price_data:
        prompt += f"""
CURRENT PRICE DATA:
- Current Price: ₹{price_data.get('current_price', 'N/A')}
- Previous Close: ₹{price_data.get('previous_close', 'N/A')}
- Day Change: {price_data.get('change', 'N/A')} ({price_data.get('change_percent', 'N/A')}%)
- Day High: ₹{price_data.get('day_high', 'N/A')}
- Day Low: ₹{price_data.get('day_low', 'N/A')}
- Volume: {price_data.get('volume', 'N/A')}
"""

    # Recent price history
    if history and len(history) > 0:
        recent = history[-5:] if len(history) >= 5 else history
        prompt += "\nRECENT PRICE TREND (last few days):\n"
        for h in recent:
            prompt += f"  {h.get('date', 'N/A')}: Close ₹{h.get('close', 'N/A')}\n"

        # Calculate simple trend
        if len(history) >= 2:
            first = history[0].get("close", 0)
            last = history[-1].get("close", 0)
            if first > 0:
                trend_pct = ((last - first) / first) * 100
                prompt += f"\n1-Month Trend: {trend_pct:+.2f}%\n"

    # News
    news = context.get("news", []) if context else []
    if news:
        prompt += "\nRECENT NEWS:\n"
        for n in news[:5]:
            prompt += f"- {n.get('title', 'N/A')}\n"
            if n.get("description"):
                prompt += f"  Summary: {n['description'][:150]}\n"

    # Fundamentals
    fundamentals = context.get("fundamentals") if context else None
    if fundamentals:
        prompt += f"""
FUNDAMENTALS (Alpha Vantage):
- Market Cap: {fundamentals.get('market_cap', 'N/A')}
- P/E Ratio: {fundamentals.get('pe_ratio', 'N/A')}
- EPS: {fundamentals.get('eps', 'N/A')}
- Dividend Yield: {fundamentals.get('dividend_yield', 'N/A')}
- Analyst Target: ₹{fundamentals.get('analyst_target', 'N/A')}
"""

    # Web context
    web_results = context.get("web_results", []) if context else []
    if web_results:
        prompt += "\nMARKET CONTEXT (Web):\n"
        for w in web_results[:3]:
            prompt += f"- {w.get('title', '')}: {w.get('body', '')[:100]}\n"

    # Trade details
    if amount:
        prompt += f"\nTRADE DETAILS: User wants to invest ₹{amount:,.2f}\n"
    if quantity:
        prompt += f"\nTRADE DETAILS: User wants to {action} {quantity} shares\n"

    prompt += """
RESPOND IN THIS EXACT JSON FORMAT:
{
    "recommendation": "BUY / SELL / HOLD / AVOID",
    "sentiment": "BULLISH / BEARISH / NEUTRAL / CAUTIOUS",
    "confidence": 75,
    "reasoning": "2-3 sentence explanation of your recommendation",
    "market_context": "Current market conditions affecting this stock/index",
    "news_summary": "Key takeaway from recent news",
    "risk_assessment": "What risks the user should be aware of",
    "key_factors": ["factor1", "factor2", "factor3"],
    "price_analysis": {
        "support_level": "nearest support price or N/A",
        "resistance_level": "nearest resistance price or N/A",
        "trend": "uptrend / downtrend / sideways"
    }
}

Respond ONLY with the JSON object, no additional text.
"""

    return prompt


# ============================================================
# CALL GROQ AI
# ============================================================

def _call_groq(prompt: str) -> str:
    """Call Groq API for fast LLM inference with model fallback."""
    raw_key = os.getenv("GROQ_API_KEY", "") or GROQ_API_KEY
    api_key = raw_key.strip("'\" \t\r\n")

    if not api_key:
        return _generate_fallback_response(
            prompt,
            "Please configure your GROQ_API_KEY in .env for detailed AI-powered insights."
        )

    # Candidate models in priority order
    models_to_try = [
        os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        "openai/gpt-oss-20b",
        "groq/compound",
    ]
    seen = set()
    models = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

    import httpx

    last_error = ""
    for model in models:
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert Indian stock market analyst. "
                                    "Respond only in valid JSON format."
                                ),
                            },
                            {
                                "role": "user",
                                "content": prompt,
                            },
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000,
                        "response_format": {"type": "json_object"},
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    if content:
                        return content

                print(f"Groq API error ({model}): {response.status_code} {response.text}")
                last_error = f"Status {response.status_code}"
        except Exception as e:
            print(f"Groq API error ({model}): {e}")
            last_error = str(e)

    return _generate_fallback_response(
        prompt,
        f"AI service temporarily unavailable ({last_error}). Using baseline market analysis."
    )


# ============================================================
# PARSE AI RESPONSE
# ============================================================

def _parse_ai_response(response_text: str) -> Dict:
    """Parse the AI response JSON."""

    try:
        # Try to extract JSON from the response
        text = response_text.strip()

        # Handle markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)

        rec = str(result.get("recommendation", "HOLD")).strip().upper()
        if "BUY" in rec:
            rec = "BUY"
        elif "SELL" in rec:
            rec = "SELL"
        elif "AVOID" in rec:
            rec = "AVOID"
        else:
            rec = "HOLD"

        sentiment = str(result.get("sentiment", "NEUTRAL")).strip().upper()
        if sentiment not in ["BULLISH", "BEARISH", "NEUTRAL", "CAUTIOUS"]:
            if "BULL" in sentiment:
                sentiment = "BULLISH"
            elif "BEAR" in sentiment:
                sentiment = "BEARISH"
            elif "CAUTION" in sentiment:
                sentiment = "CAUTIOUS"
            else:
                sentiment = "NEUTRAL"

        return {
            "recommendation": rec,
            "sentiment": sentiment,
            "confidence": float(result.get("confidence", 50)),
            "reasoning": result.get("reasoning", "Unable to provide detailed analysis."),
            "market_context": result.get("market_context", "No market context available."),
            "news_summary": result.get("news_summary", "No recent news found."),
            "risk_assessment": result.get("risk_assessment", "Standard market risks apply."),
            "key_factors": result.get("key_factors", []),
            "price_analysis": result.get("price_analysis", {}),
        }

    except (json.JSONDecodeError, Exception) as e:
        print(f"AI response parse error: {e}")
        return _default_response(
            "AI analysis completed but response format was unexpected. "
            "Please use your own judgment for this trade."
        )


# ============================================================
# HELPERS
# ============================================================

def _get_stock_name(conn, symbol: str) -> str:
    """Get stock name from DB."""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT name FROM stocks WHERE symbol = %s",
            (symbol,),
        )
        result = cursor.fetchone()
        return result["name"] if result else symbol
    finally:
        cursor.close()


def _get_stock_sector(conn, symbol: str) -> str:
    """Get stock sector from DB."""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT sector FROM stocks WHERE symbol = %s",
            (symbol,),
        )
        result = cursor.fetchone()
        return result["sector"] if result else ""
    finally:
        cursor.close()


def _get_index_info(conn, index_id: int, user_id: int) -> Optional[Dict]:
    """Get index info with active stocks."""
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT ci.id, ci.name, ci.sector, ci.theme, ci.top_n
            FROM custom_indexes ci
            WHERE ci.id = %s AND ci.user_id = %s
            """,
            (index_id, user_id),
        )
        idx = cursor.fetchone()

        if not idx:
            return None

        cursor.execute(
            """
            SELECT s.symbol, s.name, s.sector
            FROM index_constituents ic
            JOIN stocks s ON s.id = ic.stock_id
            WHERE ic.index_id = %s AND ic.is_active_in_index = TRUE
            ORDER BY ic.rank_position ASC
            """,
            (index_id,),
        )
        active_stocks = cursor.fetchall()

        return {
            **idx,
            "active_stocks": active_stocks,
        }

    finally:
        cursor.close()


def _log_advice(
    conn, user_id, context_type,
    symbol, index_id,
    query, response,
    sentiment, confidence,
    news_summary,
):
    """Log AI advice to database."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ai_advisor_log
                (user_id, context_type, stock_symbol, index_id,
                 query, ai_response, sentiment, confidence, news_summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id, context_type, symbol, index_id,
                query[:500] if query else "",
                response[:2000] if response else "",
                sentiment, confidence,
                news_summary[:500] if news_summary else "",
            ),
        )
        conn.commit()
    except Exception as e:
        print(f"Failed to log AI advice: {e}")


def _summarize_news(news: List[Dict]) -> str:
    """Create a brief news summary string."""
    if not news:
        return "No recent news available."
    titles = [n.get("title", "") for n in news[:3]]
    return " | ".join(titles)


def _default_response(message: str) -> Dict:
    """Return a default response when AI is unavailable."""
    return {
        "recommendation": "HOLD",
        "sentiment": "NEUTRAL",
        "confidence": 50.0,
        "reasoning": message,
        "market_context": "Market analysis temporarily unavailable.",
        "news_summary": "News data temporarily unavailable.",
        "risk_assessment": "Standard market risks apply. Please do your own research.",
        "key_factors": [
            "AI analysis temporarily unavailable",
            "Please review market conditions manually",
            "Consider consulting a financial advisor",
        ],
        "price_analysis": {},
    }


def _generate_fallback_response(prompt: str, reason_override: str = None) -> str:
    """
    Generate a basic response when Groq API is not configured or unavailable.
    Extracts key info from the prompt itself.
    """

    # Try to extract basic info from the prompt
    recommendation = "HOLD"
    sentiment = "NEUTRAL"

    if "dropped" in prompt.lower() or "fell" in prompt.lower():
        sentiment = "CAUTIOUS"
        recommendation = "HOLD"
    elif "rising" in prompt.lower() or "up" in prompt.lower():
        sentiment = "BULLISH"
        recommendation = "BUY"

    reasoning = reason_override or (
        "AI model is not configured. This is a basic analysis based on "
        "available data. Please configure your GROQ_API_KEY in .env for "
        "detailed AI-powered insights."
    )

    return json.dumps({
        "recommendation": recommendation,
        "sentiment": sentiment,
        "confidence": 45,
        "reasoning": reasoning,
        "market_context": "Market context analysis requires active AI configuration.",
        "news_summary": "News analysis requires active AI configuration.",
        "risk_assessment": (
            "All investments carry risk. Please do thorough research "
            "before making trading decisions in the Indian stock market."
        ),
        "key_factors": [
            "Review stock fundamentals manually",
            "Consider overall market conditions",
            "Check latest company disclosures and news",
        ],
        "price_analysis": {
            "support_level": "N/A",
            "resistance_level": "N/A",
            "trend": "N/A",
        },
    })


# ============================================================
# GET AI ADVICE HISTORY
# ============================================================

def get_advice_history(
    conn,
    user_id: int,
    limit: int = 20,
) -> List[Dict]:
    """Get past AI advisor interactions for a user."""

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, context_type, stock_symbol, index_id,
                   sentiment, confidence, ai_response,
                   news_summary, created_at
            FROM ai_advisor_log
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        logs = cursor.fetchall()

    finally:
        cursor.close()

    results = []
    for log in logs:
        # Try to parse the stored AI response
        try:
            parsed = json.loads(log["ai_response"]) if log["ai_response"] else {}
        except (json.JSONDecodeError, TypeError):
            parsed = {}

        results.append({
            "id": log["id"],
            "context_type": log["context_type"],
            "stock_symbol": log["stock_symbol"],
            "index_id": log["index_id"],
            "sentiment": log["sentiment"],
            "confidence": float(log["confidence"]) if log["confidence"] else 0,
            "recommendation": parsed.get("recommendation", "N/A"),
            "reasoning": parsed.get("reasoning", ""),
            "created_at": str(log["created_at"]),
        })

    return results
