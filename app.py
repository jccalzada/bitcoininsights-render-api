from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import random
import time
import os

app = Flask(__name__)
CORS(app)

# CoinGlass API Key
COINGLASS_API_KEY = "8dde1df481bd440eb6fe0e97bf856fcc"

@app.route('/')
def home():
    return jsonify({
        "message": "BitcoinInsights API Gateway - CRYPTO ASSETS VERSION",
        "status": "active",
        "version": "3.0-REAL-HISTORICAL-PERFORMANCE",
        "endpoints": [
            "/api/fear-greed-index",
            "/api/long-short-current",
            "/api/long-short-history",
            "/api/open-interest",
            "/api/funding-rates",
            "/api/hodl-waves",
            "/api/macro-correlations",
            "/api/asset-performance",
            "/api/asset-performance-historical-real"
        ]
    })

@app.route('/api/fear-greed-index')
def fear_greed_index():
    try:
        # Alternative Fear & Greed Index API
        response = requests.get('https://api.alternative.me/fng/', timeout=10 )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                return jsonify({
                    "code": "0",
                    "data": {
                        "value": int(latest['value']),
                        "value_classification": latest['value_classification']
                    },
                    "source": "alternative_me",
                    "status": "success"
                })
        
        # Fallback data
        return jsonify({
            "code": "0",
            "data": {
                "value": 75,
                "value_classification": "Greed"
            },
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "code": "0",
            "data": {
                "value": 75,
                "value_classification": "Greed"
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
        
        # Try the /history endpoint with current interval for current data
        url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio/history"
        params = {
            'symbol': 'BTCUSDT',
            'exchange': exchange,
            'interval': '4h',
            'limit': 1  # Just get the latest data point
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        print(f"CoinGlass API URL: {url}" )
        print(f"CoinGlass API params: {params}")
        print(f"API Key (last 4): ...{COINGLASS_API_KEY[-4:]}")
        
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
                    "source": "coinglass_api_real",
                    "status": "success",
                    "debug": {
                        "exchange_requested": exchange,
                        "timestamp": latest.get('time', 0),
                        "data_source": "real_api"
                    }
                }
                
                print(f"Returning REAL data for {exchange}: {result}")
                return jsonify(result)
            else:
                print(f"CoinGlass API returned invalid data structure: {data}")
        else:
            print(f"CoinGlass API failed with status {response.status_code}: {response.text[:200]}")
        
        print(f"CoinGlass API failed for {exchange}, using consistent fallback")
        
        # Consistent fallback data per exchange
        exchange_data = {
            'binance': {'long': 45.2, 'short': 54.8},
            'bybit': {'long': 47.1, 'short': 52.9},
            'okx': {'long': 44.8, 'short': 55.2},
            'gate': {'long': 46.3, 'short': 53.7},
            'bitget': {'long': 45.9, 'short': 54.1},
            'cme': {'long': 43.5, 'short': 56.5},
            'htx': {'long': 46.8, 'short': 53.2}
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
            "status": "success",
            "debug": {
                "reason": "coinglass_api_failed",
                "exchange_requested": exchange,
                "data_source": "fallback"
            }
        }
        
        print(f"Returning FALLBACK data for {exchange}: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"ERROR in long_short_current for {exchange}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Consistent fallback data per exchange
        exchange_data = {
            'binance': {'long': 45.2, 'short': 54.8},
            'bybit': {'long': 47.1, 'short': 52.9},
            'okx': {'long': 44.8, 'short': 55.2},
            'gate': {'long': 46.3, 'short': 53.7},
            'bitget': {'long': 45.9, 'short': 54.1},
            'cme': {'long': 43.5, 'short': 56.5},
            'htx': {'long': 46.8, 'short': 53.2}
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
            "error": str(e),
            "debug": {
                "reason": "exception_occurred",
                "exchange_requested": exchange,
                "data_source": "fallback"
            }
        })
@app.route('/api/long-short-history')
def long_short_history():
    exchange = request.args.get('exchange', 'binance')
    interval = request.args.get('interval', '1d')
    limit = int(request.args.get('limit', 7))
    
    try:
        print(f"=== LONG/SHORT HISTORY REQUEST ===")
        print(f"Exchange: {exchange}")
        print(f"Interval: {interval}")
        print(f"Limit: {limit}")
        
        # CORRECTED: Use the /history endpoint that actually works!
        url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio/history"
        params = {
            'symbol': 'BTCUSDT',
            'exchange': exchange,
            'interval': interval,
            'limit': limit
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        print(f"CoinGlass API URL: {url}" )
        print(f"CoinGlass API params: {params}")
        print(f"API Key (last 4): ...{COINGLASS_API_KEY[-4:]}")
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"CoinGlass API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"CoinGlass API response: {data}")
            
            if data.get('code') == '0' and 'data' in data and len(data['data']) > 0:
                # Sort data by time (oldest first) and take requested limit
                sorted_data = sorted(data['data'], key=lambda x: x.get('time', 0))
                limited_data = sorted_data[-limit:] if len(sorted_data) > limit else sorted_data
                
                print(f"Returning {len(limited_data)} REAL data points for {exchange}")
                
                return jsonify({
                    "code": "0",
                    "data": limited_data,
                    "metadata": {
                        "exchange": exchange,
                        "interval": interval,
                        "limit": limit,
                        "count": len(limited_data)
                    },
                    "source": "coinglass_api_real",
                    "status": "success",
                    "debug": {
                        "api_response_code": data.get('code'),
                        "original_data_count": len(data['data']),
                        "filtered_data_count": len(limited_data),
                        "data_source": "real_api"
                    }
                })
            else:
                print(f"CoinGlass API returned invalid data structure: {data}")
        else:
            print(f"CoinGlass API failed with status {response.status_code}: {response.text[:200]}")
        
        print(f"CoinGlass API failed, using FALLBACK for {exchange}")
        
        # Fallback data - consistent per exchange
        fallback_data = []
        
        # Use exchange-specific base values for consistency
        exchange_base_long = {
            'binance': 45.2,
            'bybit': 47.1,
            'okx': 44.8,
            'gate': 46.3,
            'bitget': 45.9,
            'cme': 43.5,
            'htx': 46.8
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
            "status": "success",
            "debug": {
                "reason": "coinglass_api_failed",
                "fallback_base_long": base_long,
                "data_source": "fallback"
            }
        })
        
    except Exception as e:
        print(f"ERROR in long_short_history: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback data - consistent per exchange
        fallback_data = []
        
        exchange_base_long = {
            'binance': 45.2,
            'bybit': 47.1,
            'okx': 44.8,
            'gate': 46.3,
            'bitget': 45.9,
            'cme': 43.5,
            'htx': 46.8
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
            "error": str(e),
            "debug": {
                "reason": "exception_occurred",
                "data_source": "fallback"
            }
        })


@app.route('/api/open-interest')
def open_interest():
    exchange = request.args.get('exchange', 'binance')
    
    try:
        print(f"=== OPEN INTEREST REQUEST FOR {exchange} ===")
        
        # Get current total market OI (always show total market value)
        url = "https://open-api-v4.coinglass.com/api/futures/open-interest/exchange-list"
        params = {
            'symbol': 'BTC'
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        print(f"CoinGlass API URL: {url}")
        print(f"CoinGlass API params: {params}")
        print(f"API Key (last 4): ...{COINGLASS_API_KEY[-4:]}")
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"CoinGlass API response status: {response.status_code}")
        
        current_oi_billions = None
        
        if response.status_code == 200:
            data = response.json()
            print(f"CoinGlass API response: {data}")
            
            if data.get('code') == '0' and 'data' in data:
                # Find the 'All' entry which contains total market OI
                for item in data['data']:
                    if item.get('exchange', '').lower() == 'all':
                        oi_usd = float(item.get('open_interest_usd', 0))
                        current_oi_billions = round(oi_usd / 1e9, 2)
                        print(f"Total Market OI from REAL data: ${current_oi_billions}B")
                        break
                
                if current_oi_billions is None:
                    # If no 'All' entry, calculate from sum (excluding 'All')
                    total_oi_usd = 0
                    for item in data['data']:
                        if item.get('exchange', '').lower() != 'all':
                            oi_usd = float(item.get('open_interest_usd', 0))
                            total_oi_usd += oi_usd
                    current_oi_billions = round(total_oi_usd / 1e9, 2)
                    print(f"Total Market OI calculated: ${current_oi_billions}B")
            else:
                print(f"CoinGlass API returned invalid data structure: {data}")
        else:
            print(f"CoinGlass API failed with status {response.status_code}: {response.text[:200]}")
        
        # Get historical data for the SPECIFIC exchange (not total market)
        historical_data = []
        try:
            hist_url = "https://open-api-v4.coinglass.com/api/futures/open-interest/history"
            hist_params = {
                'symbol': 'BTCUSDT',
                'exchange': exchange,  # Use the specific exchange for historical data
                'interval': '1d',
                'limit': 15
            }
            
            print(f"Fetching historical OI for {exchange}...")
            hist_response = requests.get(hist_url, params=hist_params, headers=headers, timeout=15)
            print(f"Historical API response status: {hist_response.status_code}")
            
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                print(f"Historical API response: {hist_data}")
                
                if hist_data.get('code') == '0' and 'data' in hist_data:
                    for item in hist_data['data']:
                        timestamp = item.get('time', 0)
                        if timestamp:
                            date = datetime.fromtimestamp(timestamp / 1000)
                            oi_value = float(item.get('close', 0)) / 1e9  # Convert to billions
                            
                            historical_data.append({
                                'date': date.strftime('%Y-%m-%d'),
                                'value': round(oi_value, 2)
                            })
                    
                    # Sort by date (oldest first)
                    historical_data.sort(key=lambda x: x['date'])
                    print(f"Processed {len(historical_data)} REAL historical data points for {exchange}")
                else:
                    print(f"Historical API returned invalid data: {hist_data}")
            else:
                print(f"Historical API failed with status {hist_response.status_code}: {hist_response.text[:200]}")
        
        except Exception as hist_error:
            print(f"Error fetching historical data: {str(hist_error)}")
        
        # If no historical data, generate fallback for the specific exchange
        if not historical_data:
            print(f"Generating FALLBACK historical data for {exchange}")
            
            exchange_base_values = {
                'binance': 15.0, 'cme': 19.0, 'bybit': 8.5, 'gate': 8.7, 'bitget': 6.0,
                'okx': 4.8, 'htx': 4.6, 'hyperliquid': 4.4, 'mexc': 3.1, 'deribit': 2.6
            }
            
            base_value = exchange_base_values.get(exchange.lower(), 10.0)
            
            for i in range(15):
                date = datetime.now() - timedelta(days=14-i)
                variation = random.uniform(-0.15, 0.15)
                value = round(base_value * (1 + variation), 2)
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': value
                })
        
        # Use real total market OI if available, otherwise fallback
        final_oi_billions = current_oi_billions if current_oi_billions is not None else 86.58
        data_source = "coinglass_api_real" if current_oi_billions is not None else "fallback"
        
        result = {
            "code": "0",
            "data": {
                "current_oi_billions": final_oi_billions,  # Always total market
                "current_oi_usd": int(final_oi_billions * 1e9),
                "historical": historical_data,  # Specific exchange historical data
                "exchange": exchange
            },
            "source": data_source,
            "status": "success",
            "debug": {
                "current_oi_source": "real" if current_oi_billions is not None else "fallback",
                "historical_data_points": len(historical_data),
                "historical_exchange": exchange,
                "data_source": "real_api" if current_oi_billions is not None else "fallback",
                "note": f"Current OI is total market, historical is for {exchange}"
            }
        }
        
        print(f"=== FINAL RESPONSE FOR {exchange} ===")
        print(f"Current OI (Total Market): ${final_oi_billions}B (source: {data_source})")
        print(f"Historical points for {exchange}: {len(historical_data)}")
        
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
                "current_oi_billions": 86.58,  # Total market fallback
                "current_oi_usd": 86580000000,
                "historical": historical_data,  # Exchange-specific historical
                "exchange": exchange
            },
            "source": "fallback",
            "status": "error",
            "error": str(e),
            "debug": {
                "reason": "exception_occurred",
                "data_source": "fallback"
            }
        })

@app.route('/api/funding-rates')
def funding_rates():
    try:
        print("=== FUNDING RATES REQUEST ===")
        
        # Try to get real funding rates from CoinGlass
        url = "https://open-api-v4.coinglass.com/api/futures/funding-rate/exchange-list"
        params = {
            'symbol': 'BTCUSDT'
        }
        headers = {
            'CG-API-KEY': COINGLASS_API_KEY
        }
        
        print(f"CoinGlass Funding API URL: {url}" )
        print(f"CoinGlass Funding API params: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"CoinGlass Funding API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"CoinGlass Funding API response: {len(data.get('data', []))} items")
            
            if data.get('code') == '0' and 'data' in data and len(data['data']) > 0:
                # FILTER only major exchanges
                major_exchanges = ['Binance', 'Bybit', 'OKX', 'Gate.io', 'Bitget', 'HTX', 'CME']
                funding_data = []
                
                for item in data['data']:
                    exchange_name = item.get('exchange', 'Unknown')
                    
                    # Only include major exchanges
                    if exchange_name in major_exchanges:
                        funding_rate = float(item.get('funding_rate', 0))
                        next_funding = item.get('next_funding_time', 0)
                        
                        funding_data.append({
                            "exchange": exchange_name,
                            "funding_rate": funding_rate,
                            "next_funding_time": next_funding
                        })
                
                print(f"Returning FILTERED funding rates data: {len(funding_data)} exchanges")
                
                # If we got some real data, return it
                if len(funding_data) > 0:
                    return jsonify({
                        "code": "0",
                        "data": funding_data,
                        "source": "coinglass_api_real_filtered",
                        "status": "success"
                    })
                else:
                    print("No major exchanges found in API response")
            else:
                print(f"CoinGlass Funding API returned invalid data: {data}")
        else:
            print(f"CoinGlass Funding API failed: {response.status_code}")
        
        print("CoinGlass Funding API failed, using fallback data")
        
        # Fallback data only when API fails
        funding_data = [
            {
                "exchange": "Binance",
                "funding_rate": 0.0085,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            },
            {
                "exchange": "Bybit",
                "funding_rate": 0.0092,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            },
            {
                "exchange": "OKX",
                "funding_rate": 0.0078,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            },
            {
                "exchange": "Gate.io",
                "funding_rate": 0.0088,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            },
            {
                "exchange": "Bitget",
                "funding_rate": 0.0091,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            },
            {
                "exchange": "HTX",
                "funding_rate": 0.0083,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            }
        ]
        
        return jsonify({
            "code": "0",
            "data": funding_data,
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        print(f"ERROR in funding_rates: {str(e)}")
        
        # Fallback data on error
        fallback_rates = [
            {
                "exchange": "Binance",
                "funding_rate": 0.0085,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            },
            {
                "exchange": "Bybit",
                "funding_rate": 0.0092,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            },
            {
                "exchange": "OKX",
                "funding_rate": 0.0078,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            }
        ]
        
        return jsonify({
            "code": "0",
            "data": fallback_rates,
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })
        
        return jsonify({
            "code": "0",
            "data": funding_data,
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        print(f"ERROR in funding_rates: {str(e)}")
        
        # Fallback data on error
        fallback_rates = [
            {
                "exchange": "Binance",
                "funding_rate": 0.0085,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            },
            {
                "exchange": "Bybit",
                "funding_rate": 0.0092,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            },
            {
                "exchange": "OKX",
                "funding_rate": 0.0078,
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
            }
        ]
        
        return jsonify({
            "code": "0",
            "data": fallback_rates,
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })

@app.route('/api/hodl-waves')
def hodl_waves():
    try:
        # Static realistic HODL Waves data
        hodl_data = {
            "1d-1w": 2.1,
            "1w-1m": 3.8,
            "1m-3m": 7.2,
            "3m-6m": 11.5,
            "6m-1y": 14.3,
            "1y-2y": 18.7,
            "2y-3y": 12.4,
            "3y-5y": 15.2,
            "5y-7y": 8.9,
            "7y-10y": 4.1,
            "10y+": 1.8
        }
        
        return jsonify({
            "code": "0",
            "data": hodl_data,
            "metadata": {
                "description": "Bitcoin HODL Waves - Distribution of Bitcoin supply by age",
                "unit": "percentage",
                "total_percentage": sum(hodl_data.values())
            },
            "source": "realistic_static",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "code": "1",
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/macro-correlations')
def macro_correlations():
    try:
        # Static realistic macro correlations data
        correlations_data = [
            {
                "asset": "S&P 500",
                "correlation": 0.42,
                "change_24h": 0.8,
                "trend": "positive"
            },
            {
                "asset": "Gold",
                "correlation": -0.15,
                "change_24h": -0.3,
                "trend": "negative"
            },
            {
                "asset": "DXY (Dollar Index)",
                "correlation": -0.68,
                "change_24h": 0.2,
                "trend": "negative"
            },
            {
                "asset": "10Y Treasury",
                "correlation": -0.23,
                "change_24h": 0.1,
                "trend": "negative"
            },
            {
                "asset": "VIX",
                "correlation": -0.35,
                "change_24h": -2.1,
                "trend": "negative"
            },
            {
                "asset": "Oil (WTI)",
                "correlation": 0.28,
                "change_24h": 1.4,
                "trend": "positive"
            }
        ]
        
        return jsonify({
            "code": "0",
            "data": correlations_data,
            "metadata": {
                "description": "Bitcoin correlations with traditional financial assets",
                "timeframe": "30-day rolling correlation",
                "last_updated": datetime.now().isoformat()
            },
            "source": "realistic_fallback",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "code": "1",
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/asset-performance')
def asset_performance():
    """REAL Crypto Asset Performance endpoint using CoinGecko API"""
    try:
        print("=== CRYPTO ASSET PERFORMANCE REQUEST ===")
        
        # Get crypto data from CoinGecko
        crypto_url = "https://api.coingecko.com/api/v3/simple/price"
        crypto_params = {
            'ids': 'bitcoin,ethereum,ripple,solana,tether',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(crypto_url, params=crypto_params, timeout=10 )
        print(f"CoinGecko API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            assets_data = {}
            
            # Bitcoin
            if 'bitcoin' in data:
                assets_data['Bitcoin'] = {
                    'price': data['bitcoin']['usd'],
                    'change_24h': data['bitcoin'].get('usd_24h_change', 0)
                }
            
            # Ethereum
            if 'ethereum' in data:
                assets_data['Ethereum'] = {
                    'price': data['ethereum']['usd'],
                    'change_24h': data['ethereum'].get('usd_24h_change', 0)
                }
            
            # Ripple (XRP)
            if 'ripple' in data:
                assets_data['Ripple'] = {
                    'price': data['ripple']['usd'],
                    'change_24h': data['ripple'].get('usd_24h_change', 0)
                }
            
            # Solana
            if 'solana' in data:
                assets_data['Solana'] = {
                    'price': data['solana']['usd'],
                    'change_24h': data['solana'].get('usd_24h_change', 0)
                }
            
            # Tether (for reference)
            if 'tether' in data:
                assets_data['Tether'] = {
                    'price': data['tether']['usd'],
                    'change_24h': data['tether'].get('usd_24h_change', 0)
                }
            
            print(f"CoinGecko REAL data retrieved: {assets_data}")
            
            return jsonify({
                "code": "0",
                "data": assets_data,
                "metadata": {
                    "source": "coingecko_api",
                    "timestamp": datetime.now().isoformat(),
                    "assets_count": len(assets_data)
                },
                "source": "coingecko_real",
                "status": "success"
            })
        else:
            print(f"CoinGecko API failed with status {response.status_code}")
            raise Exception(f"CoinGecko API returned status {response.status_code}")
        
    except Exception as e:
        print(f"Error in asset_performance: {str(e)}")
        
        # Fallback data with realistic values
        fallback_data = {
            "Bitcoin": {
                "price": 119000,
                "change_24h": -1.65
            },
            "Ethereum": {
                "price": 3500,
                "change_24h": 3.69
            },
            "Ripple": {
                "price": 3.4,
                "change_24h": 2.51
            },
            "Solana": {
                "price": 176,
                "change_24h": 1.48
            },
            "Tether": {
                "price": 1.0,
                "change_24h": 0.01
            }
        }
        
        return jsonify({
            "code": "0",
            "data": fallback_data,
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })
@app.route('/api/asset-performance-historical-real')
def asset_performance_historical_real():
    """Calculate REAL historical performance by comparing current price vs historical price"""
    try:
        period = request.args.get('period', '6m')
        print(f"=== HISTORICAL PERFORMANCE CALCULATION REQUEST - PERIOD: {period} ===")
        
        # Calculate target date based on period
        now = datetime.now()
        if period == '6m':
            target_date = now - timedelta(days=180)
        elif period == '3y':
            target_date = now - timedelta(days=1095)  # 3 years
        elif period == '5y':
            target_date = now - timedelta(days=1825)  # 5 years
        elif period == '10y':
            target_date = now - timedelta(days=3650)  # 10 years
        else:
            target_date = now - timedelta(days=180)  # default to 6m
        
        # Format date for CoinGecko API (DD-MM-YYYY)
        formatted_date = target_date.strftime('%d-%m-%Y')
        print(f"Target date: {formatted_date}")
        
        # Coin IDs for CoinGecko API
        coins = {
            'Bitcoin': 'bitcoin',
            'Ethereum': 'ethereum', 
            'Ripple': 'ripple',
            'Solana': 'solana'
        }
        
        results = {}
        
        for coin_name, coin_id in coins.items():
            try:
                print(f"\nProcessing {coin_name} ({coin_id})...")
                
                # Get current price
                current_url = "https://api.coingecko.com/api/v3/simple/price"
                current_params = {
                    'ids': coin_id,
                    'vs_currencies': 'usd'
                }
                
                current_response = requests.get(current_url, params=current_params, timeout=10 )
                print(f"Current price API status: {current_response.status_code}")
                
                if current_response.status_code == 200:
                    current_data = current_response.json()
                    current_price = current_data[coin_id]['usd']
                    print(f"Current price: ${current_price:,.2f}")
                else:
                    print(f"Failed to get current price for {coin_name}")
                    continue
                
                # Get historical price
                historical_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
                historical_params = {
                    'date': formatted_date,
                    'localization': 'false'
                }
                
                historical_response = requests.get(historical_url, params=historical_params, timeout=10 )
                print(f"Historical price API status: {historical_response.status_code}")
                
                if historical_response.status_code == 200:
                    historical_data = historical_response.json()
                    
                    # Check if market_data exists and has current_price
                    if 'market_data' in historical_data and 'current_price' in historical_data['market_data']:
                        historical_price = historical_data['market_data']['current_price']['usd']
                        print(f"Historical price ({formatted_date}): ${historical_price:,.2f}")
                        
                        # Calculate percentage change
                        if historical_price > 0:
                            percentage_change = ((current_price - historical_price) / historical_price) * 100
                            print(f"Performance: {percentage_change:+.2f}%")
                            
                            results[coin_name] = {
                                'performance': round(percentage_change, 2),
                                'current_price': current_price,
                                'historical_price': historical_price,
                                'historical_date': formatted_date,
                                'existed': True
                            }
                        else:
                            print(f"Invalid historical price for {coin_name}")
                            results[coin_name] = {
                                'performance': 0,
                                'current_price': current_price,
                                'historical_price': 0,
                                'historical_date': formatted_date,
                                'existed': False
                            }
                    else:
                        print(f"No market data available for {coin_name} on {formatted_date}")
                        # For coins that didn't exist, set performance to 0
                        results[coin_name] = {
                            'performance': 0,
                            'current_price': current_price,
                            'historical_price': 0,
                            'historical_date': formatted_date,
                            'existed': False
                        }
                else:
                    print(f"Failed to get historical price for {coin_name}: {historical_response.status_code}")
                    results[coin_name] = {
                        'performance': 0,
                        'current_price': current_price,
                        'historical_price': 0,
                        'historical_date': formatted_date,
                        'existed': False
                    }
                
                # Add delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing {coin_name}: {str(e)}")
                results[coin_name] = {
                    'performance': 0,
                    'current_price': 0,
                    'historical_price': 0,
                    'historical_date': formatted_date,
                    'existed': False
                }
        
        print(f"\nFinal results: {results}")
        
        return jsonify({
            "code": "0",
            "data": results,
            "debug": {
                "period": period,
                "target_date": formatted_date,
                "calculation_method": "real_price_comparison",
                "coins_processed": len(results)
            },
            "period": period,
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error in asset_performance_historical_real: {str(e)}")
        return jsonify({
            "code": "1",
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)
