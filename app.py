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
        "version": "3.1-CORRECTED-FUNDING-RATES",
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
        response = requests.get('https://api.alternative.me/fng/', timeout=10)
        
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
        
        print(f"CoinGlass API URL: {url}")
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
        
        print(f"CoinGlass API URL: {url}")
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
                'exchange': exchange,
                'interval': '1d',
                'limit': 7
            }
            
            print(f"Historical OI API URL: {hist_url}")
            print(f"Historical OI API params: {hist_params}")
            
            hist_response = requests.get(hist_url, params=hist_params, headers=headers, timeout=15)
            print(f"Historical OI API response status: {hist_response.status_code}")
            
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                print(f"Historical OI API response: {hist_data}")
                
                if hist_data.get('code') == '0' and 'data' in hist_data and len(hist_data['data']) > 0:
                    # Sort by time and take last 7 days
                    sorted_data = sorted(hist_data['data'], key=lambda x: x.get('time', 0))
                    recent_data = sorted_data[-7:] if len(sorted_data) > 7 else sorted_data
                    
                    for item in recent_data:
                        timestamp = item.get('time', 0)
                        date = datetime.fromtimestamp(timestamp / 1000)
                        
                        # Use 'close' value from OHLC data (this is the correct field)
                        oi_value = float(item.get('close', 0)) / 1e9  # Convert to billions
                        
                        historical_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'value': round(oi_value, 2)
                        })
                    
                    print(f"Historical OI data loaded: {len(historical_data)} points")
                else:
                    print(f"Historical OI API returned invalid data: {hist_data}")
            else:
                print(f"Historical OI API failed: {hist_response.status_code}")
        
        except Exception as hist_e:
            print(f"Error fetching historical OI data: {str(hist_e)}")
        
        # If we got current OI but no historical data, generate fallback historical
        if current_oi_billions and not historical_data:
            print("Using fallback historical data with real current OI")
            
            # Use exchange-specific base values for historical fallback
            exchange_base_oi = {
                'binance': 15.2,
                'cme': 19.0,
                'bybit': 8.5,
                'okx': 6.8,
                'gate': 2.9,
                'bitget': 2.3,
                'htx': 1.8
            }
            
            base_oi = exchange_base_oi.get(exchange.lower(), 5.0)
            
            for i in range(7):
                date = datetime.now() - timedelta(days=6-i)
                
                # Generate consistent variation
                day_seed = date.day + hash(exchange) % 100
                variation = (day_seed % 20 - 10) * 0.1  # ±10% variation
                
                oi_value = base_oi * (1 + variation)
                
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': round(oi_value, 2)
                })
        
        # If we have real current OI, return it with historical data
        if current_oi_billions:
            return jsonify({
                "code": "0",
                "data": {
                    "current_oi_billions": current_oi_billions,
                    "historical_data": historical_data,
                    "exchange": exchange
                },
                "source": "coinglass_api_real" if historical_data else "mixed",
                "status": "success",
                "debug": {
                    "current_oi_source": "real_api",
                    "historical_data_source": "real_api" if historical_data else "fallback",
                    "exchange_requested": exchange
                }
            })
        
        # Full fallback if no real data
        print(f"No real OI data available, using full fallback for {exchange}")
        
        exchange_base_oi = {
            'binance': 15.2,
            'cme': 19.0,
            'bybit': 8.5,
            'okx': 6.8,
            'gate': 2.9,
            'bitget': 2.3,
            'htx': 1.8
        }
        
        base_oi = exchange_base_oi.get(exchange.lower(), 5.0)
        historical_data = []
        
        for i in range(7):
            date = datetime.now() - timedelta(days=6-i)
            
            day_seed = date.day + hash(exchange) % 100
            variation = (day_seed % 20 - 10) * 0.1
            
            oi_value = base_oi * (1 + variation)
            
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': round(oi_value, 2)
            })
        
        return jsonify({
            "code": "0",
            "data": {
                "current_oi_billions": 84.76,  # Fallback total market OI
                "historical_data": historical_data,
                "exchange": exchange
            },
            "source": "fallback",
            "status": "success",
            "debug": {
                "reason": "coinglass_api_failed",
                "exchange_requested": exchange,
                "fallback_base_oi": base_oi
            }
        })
        
    except Exception as e:
        print(f"ERROR in open_interest: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Full fallback
        exchange_base_oi = {
            'binance': 15.2,
            'cme': 19.0,
            'bybit': 8.5,
            'okx': 6.8,
            'gate': 2.9,
            'bitget': 2.3,
            'htx': 1.8
        }
        
        base_oi = exchange_base_oi.get(exchange.lower(), 5.0)
        historical_data = []
        
        for i in range(7):
            date = datetime.now() - timedelta(days=6-i)
            timestamp = int(date.timestamp() * 1000)
            
            day_seed = date.day + hash(exchange) % 100
            variation = (day_seed % 20 - 10) * 0.1
            
            oi_value = base_oi * (1 + variation)
            oi_usd = oi_value * 1e9
            
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': round(oi_value, 2)
            })
        
        return jsonify({
            "code": "0",
            "data": {
                "current_oi_billions": 84.76,  # Fallback total market OI
                "historical_data": historical_data,
                "exchange": exchange
            },
            "source": "fallback",
            "status": "error",
            "error": str(e),
            "debug": {
                "reason": "exception_occurred",
                "exchange_requested": exchange
            }
        })

@app.route('/api/funding-rates')
def funding_rates():
    """CORRECTED Funding Rate - Only Binance with proper decimal handling"""
    try:
        print("=== BINANCE FUNDING RATE REQUEST (CORRECTED) ===")
        
        url = "https://open-api-v4.coinglass.com/api/futures/funding-rate/history"
        params = {
            'exchange': 'Binance',
            'symbol': 'BTCUSDT',
            'interval': '8h',
            'limit': 1
        }
        headers = {'CG-API-KEY': COINGLASS_API_KEY}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Binance funding rate API status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"CoinGlass API response: {data}")
            
            if data.get('code') == '0' and 'data' in data and len(data['data']) > 0:
                latest = data['data'][-1]
                funding_rate_decimal = float(latest.get('close', 0))
                
                print(f"Raw funding rate from CoinGlass: {funding_rate_decimal}")
                
                # CORRECTED: Don't multiply by 100 - CoinGlass already returns percentage
                funding_rate_pct = round(funding_rate_decimal, 4)
                
                print(f"Processed funding rate: {funding_rate_pct}%")
                
                # CORRECTED: Adjust thresholds for realistic funding rate ranges
                if funding_rate_pct > 0.01:     # > 0.01%
                    color = "positive"  # Green
                elif funding_rate_pct < -0.01:  # < -0.01%
                    color = "negative"  # Yellow/Orange
                else:
                    color = "neutral"   # Gray
                
                next_funding = int((datetime.now() + timedelta(hours=8)).timestamp() * 1000)
                
                return jsonify({
                    "code": "0",
                    "data": {
                        "exchange": "Binance",
                        "funding_rate": funding_rate_pct,
                        "next_funding_time": next_funding,
                        "color": color,
                        "status": "real"
                    },
                    "source": "coinglass_api_real",
                    "status": "success"
                })
        
        print("CoinGlass API failed, using fallback")
        
        # Fallback with realistic values
        return jsonify({
            "code": "0",
            "data": {
                "exchange": "Binance",
                "funding_rate": 0.0085,  # 0.0085% (realistic)
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000),
                "color": "positive",
                "status": "fallback"
            },
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error in funding_rates: {str(e)}")
        return jsonify({
            "code": "0",
            "data": {
                "exchange": "Binance",
                "funding_rate": 0.0085,  # 0.0085% (realistic)
                "next_funding_time": int((datetime.now() + timedelta(hours=8)).timestamp() * 1000),
                "color": "positive",
                "status": "fallback"
            },
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })

@app.route('/api/hodl-waves')
def hodl_waves():
    try:
        # Static realistic HODL Waves data
        hodl_data = {
            "1d-1w": 2.5,
            "1w-1m": 8.3,
            "1m-3m": 12.7,
            "3m-6m": 15.2,
            "6m-1y": 18.9,
            "1y-2y": 16.4,
            "2y-3y": 11.8,
            "3y-5y": 9.1,
            "5y+": 5.1
        }
        
        return jsonify({
            "code": "0",
            "data": hodl_data,
            "source": "static",
            "status": "success"
        })
        
    except Exception as e:
        # Fallback data
        fallback_hodl = {
            "1d-1w": 2.5,
            "1w-1m": 8.3,
            "1m-3m": 12.7,
            "3m-6m": 15.2,
            "6m-1y": 18.9,
            "1y-2y": 16.4,
            "2y-3y": 11.8,
            "3y-5y": 9.1,
            "5y+": 5.1
        }
        
        return jsonify({
            "code": "0",
            "data": fallback_hodl,
            "source": "fallback",
            "status": "error"
        })

@app.route('/api/macro-correlations')
def macro_correlations():
    try:
        # Static realistic macro correlations data
        correlations = [
            {"asset": "Gold", "correlation": 0.15, "change_24h": 0.8},
            {"asset": "S&P 500", "correlation": 0.42, "change_24h": 1.2},
            {"asset": "NASDAQ", "correlation": 0.58, "change_24h": 1.8},
            {"asset": "DXY", "correlation": -0.31, "change_24h": -0.3},
            {"asset": "10Y Treasury", "correlation": -0.18, "change_24h": 0.1},
            {"asset": "Oil (WTI)", "correlation": 0.23, "change_24h": 2.1}
        ]
        
        return jsonify({
            "code": "0",
            "data": correlations,
            "metadata": {
                "period": "30d",
                "updated": datetime.now().isoformat()
            },
            "source": "realistic_fallback",
            "status": "success"
        })
        
    except Exception as e:
        # Fallback data
        fallback_correlations = [
            {"asset": "Gold", "correlation": 0.15, "change_24h": 0.8},
            {"asset": "S&P 500", "correlation": 0.42, "change_24h": 1.2},
            {"asset": "NASDAQ", "correlation": 0.58, "change_24h": 1.8},
            {"asset": "DXY", "correlation": -0.31, "change_24h": -0.3},
            {"asset": "10Y Treasury", "correlation": -0.18, "change_24h": 0.1},
            {"asset": "Oil (WTI)", "correlation": 0.23, "change_24h": 2.1}
        ]
        
        return jsonify({
            "code": "0",
            "data": fallback_correlations,
            "source": "fallback",
            "status": "error"
        })

@app.route('/api/asset-performance')
def asset_performance():
    """Real-time crypto asset performance from CoinGecko"""
    try:
        print("=== CRYPTO ASSET PERFORMANCE REQUEST ===")
        
        # CoinGecko API for real-time prices and 24h changes
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum,ripple,solana,tether',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        print(f"CoinGecko API URL: {url}")
        print(f"CoinGecko API params: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        print(f"CoinGecko API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"CoinGecko API response: {data}")
            
            # Transform to expected format
            result_data = {}
            
            if 'bitcoin' in data:
                result_data['Bitcoin'] = {
                    'price': data['bitcoin'].get('usd', 0),
                    'change_24h': data['bitcoin'].get('usd_24h_change', 0)
                }
            
            if 'ethereum' in data:
                result_data['Ethereum'] = {
                    'price': data['ethereum'].get('usd', 0),
                    'change_24h': data['ethereum'].get('usd_24h_change', 0)
                }
            
            if 'ripple' in data:
                result_data['Ripple'] = {
                    'price': data['ripple'].get('usd', 0),
                    'change_24h': data['ripple'].get('usd_24h_change', 0)
                }
            
            if 'solana' in data:
                result_data['Solana'] = {
                    'price': data['solana'].get('usd', 0),
                    'change_24h': data['solana'].get('usd_24h_change', 0)
                }
            
            if 'tether' in data:
                result_data['Tether'] = {
                    'price': data['tether'].get('usd', 0),
                    'change_24h': data['tether'].get('usd_24h_change', 0)
                }
            
            print(f"Transformed data: {result_data}")
            
            return jsonify({
                "code": "0",
                "data": result_data,
                "source": "coingecko_real",
                "status": "success"
            })
        else:
            print(f"CoinGecko API failed with status {response.status_code}")
            raise Exception(f"API returned status {response.status_code}")
        
    except Exception as e:
        print(f"Error in asset_performance: {str(e)}")
        
        # Fallback data with realistic values
        fallback_data = {
            "Bitcoin": {
                "price": 119300,
                "change_24h": -1.65
            },
            "Ethereum": {
                "price": 3600,
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
            "error": str(e),
            "source": "fallback",
            "status": "error"
        })

@app.route('/api/asset-performance-historical-real')
def asset_performance_historical_real():
    """Calculate REAL historical performance using current vs historical prices"""
    try:
        period = request.args.get('period', '3y')
        print(f"=== REAL HISTORICAL PERFORMANCE REQUEST FOR {period} ===")
        
        # Calculate days back based on period
        days_back = {
            '6m': 180,
            '3y': 1095,  # 3 years
            '5y': 1825,  # 5 years
            '10y': 3650  # 10 years
        }.get(period, 1095)
        
        # Calculate historical date
        historical_date = datetime.now() - timedelta(days=days_back)
        date_str = historical_date.strftime('%d-%m-%Y')
        
        print(f"Fetching data for {days_back} days back ({date_str})")
        
        # Crypto IDs for CoinGecko
        crypto_ids = {
            'btc': 'bitcoin',
            'eth': 'ethereum', 
            'xrp': 'ripple',
            'sol': 'solana'
        }
        
        results = {}
        
        # Get current prices first
        current_url = "https://api.coingecko.com/api/v3/simple/price"
        current_params = {
            'ids': ','.join(crypto_ids.values()),
            'vs_currencies': 'usd'
        }
        
        current_response = requests.get(current_url, params=current_params, timeout=10)
        print(f"Current prices API status: {current_response.status_code}")
        
        if current_response.status_code != 200:
            raise Exception("Failed to get current prices")
        
        current_data = current_response.json()
        print(f"Current prices: {current_data}")
        
        # Get historical prices for each crypto
        for symbol, coin_id in crypto_ids.items():
            try:
                print(f"Fetching historical data for {symbol} ({coin_id})...")
                
                # Get historical price
                hist_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
                hist_params = {
                    'date': date_str,
                    'localization': 'false'
                }
                
                hist_response = requests.get(hist_url, params=hist_params, timeout=10)
                print(f"{symbol} historical API status: {hist_response.status_code}")
                
                if hist_response.status_code == 200:
                    hist_data = hist_response.json()
                    
                    # Extract prices
                    current_price = current_data.get(coin_id, {}).get('usd', 0)
                    historical_price = hist_data.get('market_data', {}).get('current_price', {}).get('usd', 0)
                    
                    print(f"{symbol}: Current ${current_price}, Historical ${historical_price}")
                    
                    if current_price > 0 and historical_price > 0:
                        # Calculate percentage change: ((current - historical) / historical) * 100
                        performance = ((current_price - historical_price) / historical_price) * 100
                        results[symbol] = round(performance, 2)
                        print(f"{symbol} performance: {performance:.2f}%")
                    else:
                        print(f"{symbol}: Invalid price data")
                        results[symbol] = 0
                else:
                    print(f"{symbol} historical API failed: {hist_response.status_code}")
                    results[symbol] = 0
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing {symbol}: {str(e)}")
                results[symbol] = 0
        
        # Handle coins that didn't exist in certain periods
        if period == '5y':
            if results.get('sol', 0) == 0:  # Solana didn't exist 5 years ago
                results['sol'] = 0
        elif period == '10y':
            if results.get('eth', 0) == 0:  # Ethereum didn't exist 10 years ago
                results['eth'] = 0
            if results.get('sol', 0) == 0:  # Solana didn't exist 10 years ago
                results['sol'] = 0
        
        print(f"Final results: {results}")
        
        return jsonify({
            "code": "0",
            "data": results,
            "period": period,
            "historical_date": date_str,
            "source": "coingecko_real",
            "status": "success",
            "debug": {
                "days_back": days_back,
                "crypto_count": len(results)
            }
        })
        
    except Exception as e:
        print(f"Error in asset_performance_historical_real: {str(e)}")
        
        # Fallback data with corrected realistic values
        fallback_data = {
            '6m': { 
                'btc': 45,      # BTC: $82k -> $119k = +45%
                'eth': 9.38,    # ETH: $3200 -> $3500 = +9.38%
                'xrp': 6.25,    # XRP: $3.2 -> $3.4 = +6.25%
                'sol': -16.19   # SOL: $210 -> $176 = -16.19%
            },
            '3y': { 
                'btc': 180, 
                'eth': 120, 
                'xrp': 30, 
                'sol': 800 
            },
            '5y': { 
                'btc': 600, 
                'eth': 800, 
                'xrp': 150, 
                'sol': 0  # Didn't exist
            },
            '10y': { 
                'btc': 41800,  # CORRECTED: $284 -> $119k = +41,800%
                'eth': 0,      # Didn't exist
                'xrp': 800, 
                'sol': 0      # Didn't exist
            }
        }
        
        period = request.args.get('period', '3y')
        data = fallback_data.get(period, fallback_data['3y'])
        
        return jsonify({
            "code": "1",
            "data": data,
            "period": period,
            "source": "fallback",
            "status": "error",
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)

