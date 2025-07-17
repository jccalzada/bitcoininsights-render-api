from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__)
CORS(app)

# CoinGlass API Key
COINGLASS_API_KEY = "8dde1df481bd440eb6fe0e97bf856fcc"

@app.route('/')
def home():
    return jsonify({
        "message": "BitcoinInsights API Gateway",
        "status": "active",
        "endpoints": [
            "/api/fear-greed-index",
            "/api/long-short-current",
            "/api/long-short-history",
            "/api/open-interest"
        ]
    })

@app.route('/api/fear-greed-index')
def fear_greed_index():
    try:
        # Alternative Fear & Greed Index API
        response = requests.get('https://api.alternative.me/fng/', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                fng_data = data['data'][0]
                return jsonify({
                    "code": "0",
                    "data": {
                        "value": int(fng_data['value']),
                        "value_classification": fng_data['value_classification'],
                        "timestamp": fng_data['timestamp']
                    },
                    "source": "alternative_me",
                    "status": "success"
                })
        
        # Fallback data
        return jsonify({
            "code": "0",
            "data": {
                "value": 42,
                "value_classification": "Fear",
                "timestamp": str(int(datetime.now().timestamp()))
            },
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "code": "0",
            "data": {
                "value": 42,
                "value_classification": "Fear",
                "timestamp": str(int(datetime.now().timestamp()))
            },
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })

@app.route('/api/long-short-current')
def long_short_current():
    exchange = request.args.get('exchange', 'binance')
    
    try:
        # CoinGlass Long/Short Ratio API call
        url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio"
        params = {
            'symbol': 'BTCUSDT',
            'exchange': exchange,
            'interval': '4h'
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '0' and 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                return jsonify({
                    "code": "0",
                    "data": {
                        "global_account_long_percent": latest.get('global_account_long_percent', 0),
                        "global_account_short_percent": latest.get('global_account_short_percent', 0),
                        "global_account_long_short_ratio": latest.get('global_account_long_short_ratio', 0)
                    },
                    "source": "coinglass_api",
                    "status": "success"
                })
        
        # Fallback data
        return jsonify({
            "code": "0",
            "data": {
                "global_account_long_percent": 45.2,
                "global_account_short_percent": 54.8,
                "global_account_long_short_ratio": 0.82
            },
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "code": "0",
            "data": {
                "global_account_long_percent": 45.2,
                "global_account_short_percent": 54.8,
                "global_account_long_short_ratio": 0.82
            },
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })

@app.route('/api/long-short-history')
def long_short_history():
    exchange = request.args.get('exchange', 'binance')
    
    try:
        # CoinGlass Long/Short Ratio History API call
        url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio"
        params = {
            'symbol': 'BTCUSDT',
            'exchange': exchange,
            'interval': '4h',
            'limit': 90  # 15 days * 6 (4h intervals per day)
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '0' and 'data' in data:
                return jsonify({
                    "code": "0",
                    "data": data['data'],
                    "metadata": {
                        "exchange": exchange,
                        "interval": "4h",
                        "limit": 90,
                        "count": len(data['data'])
                    },
                    "source": "coinglass_api",
                    "status": "success"
                })
        
        # Fallback data
        fallback_data = []
        for i in range(90):
            timestamp = int((datetime.now() - timedelta(hours=4*i)).timestamp() * 1000)
            long_pct = round(random.uniform(42, 48), 2)
            short_pct = round(100 - long_pct, 2)
            ratio = round(long_pct / short_pct, 2)
            
            fallback_data.append({
                "time": timestamp,
                "global_account_long_percent": long_pct,
                "global_account_short_percent": short_pct,
                "global_account_long_short_ratio": ratio
            })
        
        return jsonify({
            "code": "0",
            "data": fallback_data,
            "metadata": {
                "exchange": exchange,
                "interval": "4h",
                "limit": 90,
                "count": len(fallback_data)
            },
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        # Fallback data
        fallback_data = []
        for i in range(90):
            timestamp = int((datetime.now() - timedelta(hours=4*i)).timestamp() * 1000)
            long_pct = round(random.uniform(42, 48), 2)
            short_pct = round(100 - long_pct, 2)
            ratio = round(long_pct / short_pct, 2)
            
            fallback_data.append({
                "time": timestamp,
                "global_account_long_percent": long_pct,
                "global_account_short_percent": short_pct,
                "global_account_long_short_ratio": ratio
            })
        
        return jsonify({
            "code": "0",
            "data": fallback_data,
            "metadata": {
                "exchange": exchange,
                "interval": "4h",
                "limit": 90,
                "count": len(fallback_data)
            },
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })

@app.route('/api/open-interest')
def open_interest():
    exchange = request.args.get('exchange', 'binance')
    
    try:
        # CoinGlass Open Interest API call - DATOS ACTUALES (siempre total)
        url_current = "https://open-api-v4.coinglass.com/api/futures/open-interest/exchange-list"
        params_current = {
            'symbol': 'BTC'
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        response_current = requests.get(url_current, params=params_current, headers=headers, timeout=15)
        
        # Datos actuales (total del mercado)
        current_oi_billions = 87.22  # Default
        exchanges_data = []
        
        if response_current.status_code == 200:
            data_current = response_current.json()
            if data_current.get('code') == '0' and 'data' in data_current:
                total_oi = sum(float(item.get('openInterest', 0)) for item in data_current['data'])
                current_oi_billions = round(total_oi / 1e9, 2)
                exchanges_data = data_current['data']
        
        # Datos históricos por exchange específico (solo si no es 'total')
        historical_data = []
        if exchange.lower() != 'total':
            url_history = "https://open-api-v4.coinglass.com/api/futures/open-interest/history"
            params_history = {
                'symbol': 'BTCUSDT',
                'exchange': exchange.capitalize(),
                'interval': '1d',
                'limit': 15
            }
            
            response_history = requests.get(url_history, params=params_history, headers=headers, timeout=15)
            
            if response_history.status_code == 200:
                data_history = response_history.json()
                if data_history.get('code') == '0' and 'data' in data_history:
                    for item in data_history['data']:
                        historical_data.append({
                            'date': datetime.fromtimestamp(item.get('time', 0) / 1000).strftime('%Y-%m-%d'),
                            'value': round(float(item.get('close', 0)) / 1e9, 2)  # Convert to billions
                        })
        
        # Si no hay datos históricos, generar fallback realista
        if not historical_data and exchange.lower() != 'total':
            base_value = current_oi_billions * 0.15  # Aproximadamente 15% del total para un exchange
            for i in range(15):
                date = datetime.now() - timedelta(days=i)
                variation = random.uniform(-0.2, 0.2)
                value = round(base_value * (1 + variation), 2)
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': value
                })
            historical_data.reverse()
        
        return jsonify({
            "code": "0",
            "data": {
                "current_oi_billions": current_oi_billions,
                "historical": historical_data,
                "exchange": exchange,
                "exchanges": exchanges_data[:10]  # Top 10 exchanges
            },
            "source": "coinglass_api",
            "status": "success"
        })
        
    except Exception as e:
        # Fallback completo
        base_value = 87.22 * 0.15 if exchange.lower() != 'total' else 87.22
        historical_data = []
        
        if exchange.lower() != 'total':
            for i in range(15):
                date = datetime.now() - timedelta(days=i)
                variation = random.uniform(-0.2, 0.2)
                value = round(base_value * (1 + variation), 2)
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': value
                })
            historical_data.reverse()
        
        return jsonify({
            "code": "0",
            "data": {
                "current_oi_billions": 87.22,
                "historical": historical_data,
                "exchange": exchange,
                "exchanges": []
            },
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

