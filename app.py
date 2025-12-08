from flask import Flask, jsonify, request #request reads query params
import yfinance as yf
from sheets_client import read_watchlist, write_demo_value


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

# Only run the server if this file is executed directly
if __name__ == "__main__":
    app.run(debug=True)
