from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)

# CoinGlass API Key
COINGLASS_API_KEY = "8dde1df481bd440eb6fe0e97bf856fcc"

@app.route('/')
def home():
    return jsonify({
        "message": "BitcoinInsights API Gateway is working on Render!",
        "status": "success",
        "endpoints": [
            "/api/test",
            "/api/long-short-current",
            "/api/long-short-history"
        ]
    })

@app.route('/api/test')
def test():
    return jsonify({
        "message": "CoinGlass API Gateway is working on Render!",
        "status": "success",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/long-short-current')
def long_short_current():
    exchange = request.args.get('exchange', 'binance')
    
    try:
        # CoinGlass API call
        url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio/history"
        params = {
            'symbol': 'BTC',
            'exchange': exchange,
            'interval': '1d',
            'limit': 1
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == "0" and data.get('data'):
                latest = data['data'][0]
                result = {
                    "code": "0",
                    "data": {
                        "global_account_long_percent": latest['longAccount'] * 100,
                        "global_account_short_percent": latest['shortAccount'] * 100,
                        "global_account_long_short_ratio": latest['longShortRatio']
                    },
                    "source": "coinglass_api",
                    "status": "success"
                }
            else:
                raise Exception("Invalid API response")
        else:
            raise Exception(f"API error: {response.status_code}")
            
    except Exception as e:
        # Fallback data
        fallback_data = {
            'binance': {'long': 36.57, 'short': 63.43},
            'bybit': {'long': 34.2, 'short': 65.8},
            'okx': {'long': 38.1, 'short': 61.9},
            'bitget': {'long': 35.8, 'short': 64.2}
        }
        
        data = fallback_data.get(exchange, fallback_data['binance'])
        result = {
            "code": "0",
            "data": {
                "global_account_long_percent": data['long'],
                "global_account_short_percent": data['short'],
                "global_account_long_short_ratio": data['long'] / data['short']
            },
            "source": "fallback",
            "status": "success"
        }
    
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
