from flask import Flask, jsonify, request #request reads query params
import yfinance as yf

from sheets_client import read_watchlist, write_demo_value, write_watchlist_update
from ai_agent import analyse_stock
from datetime import datetime, timezone
from datetime import datetime, timezone
from sheets_client import read_portfolio, write_portfolio_update
from ai_agent import analyse_portfolio_risk
from news_client import fetch_news


def build_stock_info_for_analysis(ticker: str) -> dict:
    """
    Uses yfinance to build a small stock_info dict for the AI.
    """
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.info

    price = info.get("currentPrice")
    if price is None:
        hist = ticker_obj.history(period="1d")
        if not hist.empty:
            price = float(hist["Close"][-1])

    previous_close = info.get("previousClose")
    pe_ratio = info.get("trailingPE")
    currency = info.get("currency")
    short_name = info.get("shortName") or info.get("longName")
    sector = info.get("sector")

    stock_info = {
        "ticker": ticker,
        "name": short_name,
        "sector": sector,
        "currency": currency,
        "current_price": price,
        "previous_close": previous_close,
        "pe_ratio": pe_ratio,
    }

    return stock_info


# Create the Flask app
app = Flask(__name__)

# Health check route
@app.route("/")
def health():
    # Return a simple JSON response
    return jsonify({"status": "ok"})

#stock fetch route
@app.route("/get_stock")
def get_stock():
    """
    Example:
    /get_stock?ticker=AAPL
    /get_stock?ticker=TCS.NS
    """
    ticker = request.args.get("ticker")

    if not ticker:
        return jsonify({"error":"Missing ticker query parameter"}), 400
    
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info

        price = info.get("currentPrice")
        if price is None:
            hist = ticker_obj.history(period="1d")
            if not hist.empty:
                price = float(hist["Close"][-1])

        data = {
            "ticker": ticker,
            "short_name": info.get("shortName"),
            "long_name": info.get("longName"),
            "currency": info.get("currency"),
            "current_price": price,
            "previous_close": info.get("previousClose"),
        }
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({"error" : str(e)}), 500
    
@app.route("/read_watchlist")
def read_watchlist_route():
    rows = read_watchlist()
    return jsonify({"rows" : rows})

@app.route("/write_demo")
def write_demo_route():
    result = write_demo_value("Hello")
    return jsonify({"status": "ok", "updatedRange": result.get("updatedRange")})

@app.route("/analyse")
def analyse_route():
    ticker = request.args.get("ticker")
    notes = request.args.get("notes", "")

    if not ticker:
        return jsonify({"error": "Missing 'ticker' query parameter"}), 400

    try:
        stock_info = build_stock_info_for_analysis(ticker)
        name = stock_info.get("name") or ticker
        base_ticker = ticker.split(".")[0]  

        query = f'"{name}" OR "{base_ticker}" OR "{ticker}" when:90d'
        recent_news = fetch_news(query, max_items=10)

    except Exception as e:
        return jsonify({"error": f"Error fetching market data: {str(e)}"}), 500

    try:
        analysis = analyse_stock(stock_info, notes, recent_news=recent_news)
        return jsonify(
            {
                "ticker": ticker,
                "stock_info": stock_info,
                "recent_news": len(recent_news),
                "analysis": analysis["raw_analysis"],
            }
        )
    except Exception as e:
        return jsonify({"error": f"Error calling Gemini: {str(e)}"}), 500
    
# Refresh WatchList

@app.route("/refresh_watchlist")
def refresh_watchlist():
    rows = read_watchlist()
    updated = []
    row_index = 2

    for row in rows:
        ticker = row[0].strip() if len(row) > 0 and row[0] else ""
        notes = row[2] if len(row) > 2 else ""
        
        if not ticker:
            row_index += 1
            continue
        
        try:
            stock_info = build_stock_info_for_analysis(ticker)

            current_price = stock_info.get("current_price")
            previous_close = stock_info.get("previous_close")

            day_change_pct = None
            if current_price is not None and previous_close:
                try:
                    day_change_pct = ((current_price - previous_close) / previous_close) * 100.0
                except ZeroDivisionError:
                    day_change_pct = None
            
            ai = analyse_stock(stock_info, notes)
            ai_summary = ai.get("raw_analysis", "")

            now_naive_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            now_str = now_naive_utc.isoformat()

            write_watchlist_update(
                row_index=row_index,
                current_price=current_price,
                previous_close=previous_close,
                day_change_pct=day_change_pct,
                ai_summary=ai_summary,
                timestamp=now_str,
            )

            updated.append({"row": row_index, "ticker": ticker, "status": "ok"})

        except Exception as e:
            updated.append({"row": row_index, "ticker": ticker, "status": "error", "error": str(e)})

        row_index += 1

    return jsonify({"updated": updated})

@app.route("/refresh_portfolio")
def refresh_portfolio():
    rows = read_portfolio()
    updated = []
    row_index = 2

    for row in rows:
        ticker = row[0].strip() if len(row) > 0 and row[0] else ""
        notes = row[2] if len(row) > 2 else ""

        if not ticker:
            row_index += 1
            continue

        try: 
            stock_info = build_stock_info_for_analysis(ticker)

            query = f'{stock_info.get("name", ticker)} {ticker}'
            recent_news = fetch_news(query, max_items=10)

            risk = analyse_portfolio_risk(stock_info, notes, recent_news=recent_news)

            now_str = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

            write_portfolio_update(
                row_index = row_index,
                risk_summary = risk.get("risk_summary", ""),
                risk_flag = risk.get("risk_flag", "MEDIUM"),
                timestamp = now_str
            )

            updated.append({"row": row_index, "ticker": ticker, "status" : "ok"})
        except Exception as e:
            updated.append({"row": row_index, "ticker": ticker, "status" : "error", "error" : str(e)})

        row_index += 1

    return jsonify({"updated": updated})



# Only run the server if this file is executed directly
if __name__ == "__main__":
    app.run(debug=True)
