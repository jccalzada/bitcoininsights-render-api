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

@app.route('/api/long-short-history')
def long_short_history():
    exchange = request.args.get('exchange', 'binance')
    interval = request.args.get('interval', '1d')
    timeframe = request.args.get('timeframe', '30d')
    
    # Calculate limit based on timeframe
    if timeframe == '7d':
        if interval == '4h':
            limit = 42  # 7 days * 6 intervals per day
        else:
            limit = 7
    else:  # 30d
        if interval == '4h':
            limit = 180  # 30 days * 6 intervals per day
        elif interval == '1w':
            limit = 4   # 4 weeks
        else:
            limit = 30  # 30 days
    
    try:
        # CoinGlass API call
        url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio/history"
        params = {
            'symbol': 'BTC',
            'exchange': exchange,
            'interval': interval,
            'limit': limit
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == "0" and data.get('data'):
                # Transform data
                historical_data = []
                for item in data['data']:
                    historical_data.append({
                        'timestamp': item['timestamp'],
                        'long_percent': item['longAccount'] * 100,
                        'short_percent': item['shortAccount'] * 100,
                        'long_short_ratio': item['longShortRatio']
                    })
                
                result = {
                    "code": "0",
                    "data": historical_data,
                    "metadata": {
                        "exchange": exchange,
                        "interval": interval,
                        "timeframe": timeframe,
                        "count": len(historical_data)
                    },
                    "source": "coinglass_api",
                    "status": "success"
                }
            else:
                raise Exception("Invalid API response")
        else:
            raise Exception(f"API error: {response.status_code}")
            
    except Exception as e:
        # Generate fallback historical data
        historical_data = []
        base_long = 36.57 if exchange == 'binance' else 34.2
        
        now = datetime.now()
        for i in range(limit):
            if interval == '4h':
                timestamp = now - timedelta(hours=4*i)
            elif interval == '1w':
                timestamp = now - timedelta(weeks=i)
            else:  # 1d
                timestamp = now - timedelta(days=i)
            
            # Add realistic variation
            variation = (i % 7 - 3) * 2  # Creates wave pattern
            long_pct = max(25, min(75, base_long + variation))
            short_pct = 100 - long_pct
            
            historical_data.append({
                'timestamp': int(timestamp.timestamp() * 1000),
                'long_percent': round(long_pct, 2),
                'short_percent': round(short_pct, 2),
                'long_short_ratio': round(long_pct / short_pct, 3)
            })
        
        # Reverse to get chronological order
        historical_data.reverse()
        
        result = {
            "code": "0",
            "data": historical_data,
            "metadata": {
                "exchange": exchange,
                "interval": interval,
                "timeframe": timeframe,
                "count": len(historical_data)
            },
            "source": "fallback",
            "status": "success"
        }
    
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
