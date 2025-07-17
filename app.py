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
        print(f"=== LONG/SHORT CURRENT REQUEST FOR {exchange} ===")
        
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
        
        print(f"CoinGlass API URL: {url}")
        print(f"CoinGlass API params: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"CoinGlass API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"CoinGlass API response: {data}")
            
            if data.get('code') == '0' and 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                
                result = {
                    "code": "0",
                    "data": {
                        "global_account_long_percent": latest.get('global_account_long_percent', 0),
                        "global_account_short_percent": latest.get('global_account_short_percent', 0),
                        "global_account_long_short_ratio": latest.get('global_account_long_short_ratio', 0)
                    },
                    "source": "coinglass_api",
                    "status": "success"
                }
                
                print(f"Returning real data for {exchange}: {result}")
                return jsonify(result)
        
        print(f"CoinGlass API failed for {exchange}, using consistent fallback")
        
        # Consistent fallback data per exchange
        exchange_data = {
            'binance': {'long': 45.2, 'short': 54.8},
            'bybit': {'long': 47.1, 'short': 52.9},
            'okx': {'long': 44.8, 'short': 55.2},
            'gate': {'long': 46.3, 'short': 53.7},
            'bitget': {'long': 45.9, 'short': 54.1}
        }
        
        data = exchange_data.get(exchange.lower(), {'long': 45.0, 'short': 55.0})
        
        result = {
            "code": "0",
            "data": {
                "global_account_long_percent": data['long'],
                "global_account_short_percent": data['short'],
                "global_account_long_short_ratio": round(data['long'] / data['short'], 2)
            },
            "source": "fallback",
            "status": "success"
        }
        
        print(f"Returning fallback data for {exchange}: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"ERROR in long_short_current for {exchange}: {str(e)}")
        
        # Consistent fallback data per exchange
        exchange_data = {
            'binance': {'long': 45.2, 'short': 54.8},
            'bybit': {'long': 47.1, 'short': 52.9},
            'okx': {'long': 44.8, 'short': 55.2},
            'gate': {'long': 46.3, 'short': 53.7},
            'bitget': {'long': 45.9, 'short': 54.1}
        }
        
        data = exchange_data.get(exchange.lower(), {'long': 45.0, 'short': 55.0})
        
        return jsonify({
            "code": "0",
            "data": {
                "global_account_long_percent": data['long'],
                "global_account_short_percent": data['short'],
                "global_account_long_short_ratio": round(data['long'] / data['short'], 2)
            },
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })

@app.route('/api/long-short-history')
def long_short_history():
    exchange = request.args.get('exchange', 'binance')
    interval = request.args.get('interval', '1d')  # Default to daily
    limit = int(request.args.get('limit', 7))  # Default to 7 days
    
    try:
        print(f"=== LONG/SHORT HISTORY REQUEST ===")
        print(f"Exchange: {exchange}")
        print(f"Interval: {interval}")
        print(f"Limit: {limit}")
        
        # CoinGlass Long/Short Ratio History API call
        url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio"
        params = {
            'symbol': 'BTCUSDT',
            'exchange': exchange,
            'interval': interval,
            'limit': limit
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        print(f"CoinGlass API URL: {url}")
        print(f"CoinGlass API params: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"CoinGlass API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"CoinGlass API response: {data}")
            
            if data.get('code') == '0' and 'data' in data and len(data['data']) > 0:
                # Sort data by time (oldest first) and take requested limit
                sorted_data = sorted(data['data'], key=lambda x: x.get('time', 0))
                limited_data = sorted_data[-limit:] if len(sorted_data) > limit else sorted_data
                
                print(f"Returning {len(limited_data)} data points for {exchange}")
                
                return jsonify({
                    "code": "0",
                    "data": limited_data,
                    "metadata": {
                        "exchange": exchange,
                        "interval": interval,
                        "limit": limit,
                        "count": len(limited_data)
                    },
                    "source": "coinglass_api",
                    "status": "success"
                })
        
        print(f"CoinGlass API failed, using fallback for {exchange}")
        
        # Fallback data - consistent per exchange
        fallback_data = []
        
        # Use exchange-specific base values for consistency
        exchange_base_long = {
            'binance': 45.2,
            'bybit': 47.1,
            'okx': 44.8,
            'gate': 46.3,
            'bitget': 45.9
        }
        
        base_long = exchange_base_long.get(exchange.lower(), 45.0)
        
        for i in range(limit):
            # Generate consistent dates (last N days)
            date = datetime.now() - timedelta(days=limit-1-i)
            timestamp = int(date.timestamp() * 1000)
            
            # Generate consistent variation based on day and exchange
            day_seed = date.day + hash(exchange) % 100
            variation = (day_seed % 10 - 5) * 0.5  # ±2.5% variation
            
            long_pct = round(base_long + variation, 1)
            short_pct = round(100 - long_pct, 1)
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
                "interval": interval,
                "limit": limit,
                "count": len(fallback_data)
            },
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        print(f"ERROR in long_short_history: {str(e)}")
        
        # Fallback data - consistent per exchange
        fallback_data = []
        
        exchange_base_long = {
            'binance': 45.2,
            'bybit': 47.1,
            'okx': 44.8,
            'gate': 46.3,
            'bitget': 45.9
        }
        
        base_long = exchange_base_long.get(exchange.lower(), 45.0)
        
        for i in range(limit):
            date = datetime.now() - timedelta(days=limit-1-i)
            timestamp = int(date.timestamp() * 1000)
            
            day_seed = date.day + hash(exchange) % 100
            variation = (day_seed % 10 - 5) * 0.5
            
            long_pct = round(base_long + variation, 1)
            short_pct = round(100 - long_pct, 1)
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
                "interval": interval,
                "limit": limit,
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
        print(f"=== OPEN INTEREST REQUEST FOR EXCHANGE: {exchange} ===")
        
        # PASO 1: Obtener datos actuales (siempre total del mercado)
        url_current = "https://open-api-v4.coinglass.com/api/futures/open-interest/exchange-list"
        params_current = {'symbol': 'BTC'}
        headers = {'CG-API-KEY': COINGLASS_API_KEY}
        
        print(f"Fetching current data from: {url_current}")
        response_current = requests.get(url_current, params=params_current, headers=headers, timeout=15)
        print(f"Current API response status: {response_current.status_code}")
        
        # Procesar datos actuales
        current_oi_billions = 87.22  # Default
        current_oi_usd = 87220000000  # Default
        exchanges_data = []
        
        if response_current.status_code == 200:
            data_current = response_current.json()
            print(f"Current API response: {data_current}")
            
            if data_current.get('code') == '0' and 'data' in data_current:
                total_oi = sum(float(item.get('open_interest_usd', 0)) for item in data_current['data'])
                current_oi_billions = round(total_oi / 1e9, 2)
                current_oi_usd = total_oi
                exchanges_data = data_current['data']
                print(f"Calculated total OI: ${current_oi_billions}B")
        
        # PASO 2: Obtener datos históricos específicos por exchange
        historical_data = []
        
        if exchange.lower() != 'total':
            print(f"Fetching historical data for exchange: {exchange}")
            
            # Mapear nombres de exchanges para CoinGlass
            exchange_mapping = {
                'binance': 'Binance',
                'cme': 'CME',
                'bybit': 'Bybit', 
                'gate': 'Gate',
                'bitget': 'Bitget',
                'okx': 'OKX',
                'htx': 'HTX',
                'hyperliquid': 'Hyperliquid',
                'mexc': 'MEXC',
                'deribit': 'Deribit'
            }
            
            coinglass_exchange = exchange_mapping.get(exchange.lower(), exchange.capitalize())
            print(f"Using CoinGlass exchange name: {coinglass_exchange}")
            
            url_history = "https://open-api-v4.coinglass.com/api/futures/open-interest/history"
            params_history = {
                'symbol': 'BTCUSDT',
                'exchange': coinglass_exchange,
                'interval': '1d',
                'limit': 15
            }
            
            print(f"Historical API URL: {url_history}")
            print(f"Historical API params: {params_history}")
            
            response_history = requests.get(url_history, params=params_history, headers=headers, timeout=15)
            print(f"Historical API response status: {response_history.status_code}")
            
            if response_history.status_code == 200:
                data_history = response_history.json()
                print(f"Historical API response: {data_history}")
                
                if data_history.get('code') == '0' and 'data' in data_history and len(data_history['data']) > 0:
                    print(f"Processing {len(data_history['data'])} historical data points")
                    
                    for item in data_history['data']:
                        # Convert timestamp to date
                        timestamp = item.get('time', 0)
                        if timestamp > 0:
                            date_obj = datetime.fromtimestamp(timestamp / 1000)
                            date_str = date_obj.strftime('%Y-%m-%d')
                            
                            # Convert USD to billions - usar 'close' del OHLC
                            close_value = float(item.get('close', 0))
                            value_billions = round(close_value / 1e9, 2)
                            
                            historical_data.append({
                                'date': date_str,
                                'value': value_billions
                            })
                            
                            print(f"Date: {date_str}, Close: ${close_value:,.0f}, Billions: {value_billions}B")
                    
                    print(f"Successfully processed {len(historical_data)} historical data points for {exchange}")
                else:
                    print(f"No valid historical data in response for {exchange}")
                    print(f"Response structure: {data_history}")
            else:
                print(f"Historical API call failed for {exchange}: {response_history.status_code}")
                if response_history.text:
                    print(f"Error response: {response_history.text}")
        
        # PASO 3: Si no hay datos históricos reales, usar fallback realista
        if not historical_data and exchange.lower() != 'total':
            print(f"No real historical data available, generating realistic fallback for {exchange}")
            
            # Base values por exchange (basados en datos reales observados)
            exchange_base_values = {
                'binance': 15.0,    # ~$15B
                'cme': 19.0,        # ~$19B  
                'bybit': 8.5,       # ~$8.5B
                'gate': 8.7,        # ~$8.7B
                'bitget': 6.0,      # ~$6B
                'okx': 4.8,         # ~$4.8B
                'htx': 4.6,         # ~$4.6B
                'hyperliquid': 4.4, # ~$4.4B
                'mexc': 3.1,        # ~$3.1B
                'deribit': 2.6      # ~$2.6B
            }
            
            base_value = exchange_base_values.get(exchange.lower(), 10.0)
            print(f"Using base value ${base_value}B for {exchange}")
            
            for i in range(15):
                date = datetime.now() - timedelta(days=14-i)  # Oldest to newest
                # Generate realistic variation (±15%)
                variation = random.uniform(-0.15, 0.15)
                value = round(base_value * (1 + variation), 2)
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': value
                })
            
            print(f"Generated {len(historical_data)} fallback data points for {exchange}")
        
        # PASO 4: Preparar respuesta final
        result = {
            "code": "0",
            "data": {
                "current_oi_billions": current_oi_billions,
                "current_oi_usd": current_oi_usd,
                "historical": historical_data,
                "exchange": exchange,
                "exchanges": exchanges_data[:10]  # Top 10 exchanges
            },
            "source": "coinglass_api",
            "status": "success"
        }
        
        print(f"=== FINAL RESPONSE FOR {exchange} ===")
        print(f"Current OI: ${current_oi_billions}B")
        print(f"Historical points: {len(historical_data)}")
        print(f"Exchange: {exchange}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"ERROR in open_interest endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback completo en caso de error
        exchange_base_values = {
            'binance': 15.0, 'cme': 19.0, 'bybit': 8.5, 'gate': 8.7, 'bitget': 6.0,
            'okx': 4.8, 'htx': 4.6, 'hyperliquid': 4.4, 'mexc': 3.1, 'deribit': 2.6
        }
        
        base_value = exchange_base_values.get(exchange.lower(), 10.0)
        historical_data = []
        
        if exchange.lower() != 'total':
            for i in range(15):
                date = datetime.now() - timedelta(days=14-i)
                variation = random.uniform(-0.15, 0.15)
                value = round(base_value * (1 + variation), 2)
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': value
                })
        
        return jsonify({
            "code": "0",
            "data": {
                "current_oi_billions": 87.22,
                "current_oi_usd": 87220000000,
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

