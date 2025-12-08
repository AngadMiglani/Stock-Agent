from flask import Flask, jsonify, request #request reads query params
import yfinance as yf
from sheets_client import read_watchlist, write_demo_value, write_watchlist_update
from ai_agent import analyse_stock

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
    except Exception as e:
        return jsonify({"error": f"Error fetching market data: {str(e)}"}), 500

    try:
        analysis = analyse_stock(stock_info, notes)
        return jsonify(
            {
                "ticker": ticker,
                "stock_info": stock_info,
                "analysis": analysis["raw_analysis"],
            }
        )
    except Exception as e:
        return jsonify({"error": f"Error calling Gemini: {str(e)}"}), 500

# Only run the server if this file is executed directly
if __name__ == "__main__":
    app.run(debug=True)
