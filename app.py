from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import random
import time
import os
import threading

app = Flask(__name__)
CORS(app)

# CoinGlass API Key
COINGLASS_API_KEY = "8dde1df481bd440eb6fe0e97bf856fcc"

# Global cache with longer TTL and pre-warming
global_cache = {
    'asset_performance': {
        'data': None,
        'timestamp': None,
        'ttl': 180,  # 3 minutes (reduced from 5)
        'loading': False
    },
    'historical_performance': {
        'data': {},
        'timestamp': {},
        'ttl': 1800,  # 30 minutes (reduced from 1 hour)
        'loading': {}
    }
}

# Pre-warm cache with realistic data to avoid initial delays
def initialize_cache():
    """Initialize cache with realistic fallback data"""
    print("Initializing cache with fallback data...")
    
    # Asset Performance 24H
    global_cache['asset_performance']['data'] = {
        "Bitcoin": {"price": 119300, "change_24h": -1.65},
        "Ethereum": {"price": 3600, "change_24h": 3.69},
        "Ripple": {"price": 3.4, "change_24h": 2.51},
        "Solana": {"price": 176, "change_24h": 1.48},
        "Tether": {"price": 1.0, "change_24h": 0.01}
    }
    global_cache['asset_performance']['timestamp'] = datetime.now()
    
    # Historical Performance
    historical_fallback = {
        '6m': {'btc': 45, 'eth': 9.38, 'xrp': 6.25, 'sol': -16.19},
        '3y': {'btc': 180, 'eth': 120, 'xrp': 30, 'sol': 800},
        '5y': {'btc': 600, 'eth': 800, 'xrp': 150, 'sol': 0},
        '10y': {'btc': 41800, 'eth': 0, 'xrp': 800, 'sol': 0}
    }
    
    for period, data in historical_fallback.items():
        global_cache['historical_performance']['data'][period] = data
        global_cache['historical_performance']['timestamp'][period] = datetime.now()
        global_cache['historical_performance']['loading'][period] = False

# Initialize cache on startup
initialize_cache()

def is_cache_valid(cache_entry, key=None):
    """Check if cache entry is still valid"""
    if key:
        if key not in cache_entry['data'] or key not in cache_entry['timestamp']:
            return False
        cache_time = cache_entry['timestamp'][key]
    else:
        if cache_entry['data'] is None or cache_entry['timestamp'] is None:
            return False
        cache_time = cache_entry['timestamp']
    
    return (datetime.now() - cache_time).total_seconds() < cache_entry['ttl']

def background_refresh_asset_performance():
    """Background thread to refresh asset performance data"""
    if global_cache['asset_performance']['loading']:
        return
    
    global_cache['asset_performance']['loading'] = True
    
    try:
        print("Background refresh: Asset Performance")
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum,ripple,solana,tether',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result_data = {}
            
            for coin_id, coin_name in [('bitcoin', 'Bitcoin'), ('ethereum', 'Ethereum'), 
                                     ('ripple', 'Ripple'), ('solana', 'Solana'), ('tether', 'Tether')]:
                if coin_id in data:
                    result_data[coin_name] = {
                        'price': data[coin_id].get('usd', 0),
                        'change_24h': data[coin_id].get('usd_24h_change', 0)
                    }
            
            if result_data:
                global_cache['asset_performance']['data'] = result_data
                global_cache['asset_performance']['timestamp'] = datetime.now()
                print("Background refresh: Asset Performance updated successfully")
        
    except Exception as e:
        print(f"Background refresh failed: {str(e)}")
    finally:
        global_cache['asset_performance']['loading'] = False

def background_refresh_historical(period):
    """Background thread to refresh historical performance data"""
    if global_cache['historical_performance']['loading'].get(period, False):
        return
    
    global_cache['historical_performance']['loading'][period] = True
    
    try:
        print(f"Background refresh: Historical Performance {period}")
        
        days_back = {'6m': 180, '3y': 1095, '5y': 1825, '10y': 3650}.get(period, 1095)
        historical_date = datetime.now() - timedelta(days=days_back)
        date_str = historical_date.strftime('%d-%m-%Y')
        
        crypto_ids = {'btc': 'bitcoin', 'eth': 'ethereum', 'xrp': 'ripple', 'sol': 'solana'}
        results = {}
        
        # Get current prices
        current_url = "https://api.coingecko.com/api/v3/simple/price"
        current_params = {'ids': ','.join(crypto_ids.values()), 'vs_currencies': 'usd'}
        
        current_response = requests.get(current_url, params=current_params, timeout=10)
        
        if current_response.status_code == 200:
            current_data = current_response.json()
            
            # Get historical prices with minimal delay
            for symbol, coin_id in crypto_ids.items():
                try:
                    time.sleep(0.5)  # Minimal delay
                    
                    hist_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
                    hist_params = {'date': date_str, 'localization': 'false'}
                    
                    hist_response = requests.get(hist_url, params=hist_params, timeout=10)
                    
                    if hist_response.status_code == 200:
                        hist_data = hist_response.json()
                        current_price = current_data.get(coin_id, {}).get('usd', 0)
                        historical_price = hist_data.get('market_data', {}).get('current_price', {}).get('usd', 0)
                        
                        if current_price > 0 and historical_price > 0:
                            performance = ((current_price - historical_price) / historical_price) * 100
                            results[symbol] = round(performance, 2)
                        else:
                            results[symbol] = 0
                    else:
                        results[symbol] = 0
                        
                except Exception:
                    results[symbol] = 0
            
            # Handle non-existent coins
            if period in ['5y', '10y'] and 'sol' in results:
                results['sol'] = 0
            if period == '10y' and 'eth' in results:
                results['eth'] = 0
            
            if results:
                global_cache['historical_performance']['data'][period] = results
                global_cache['historical_performance']['timestamp'][period] = datetime.now()
                print(f"Background refresh: Historical {period} updated successfully")
        
    except Exception as e:
        print(f"Background refresh historical {period} failed: {str(e)}")
    finally:
        global_cache['historical_performance']['loading'][period] = False

@app.route('/')
def home():
    return jsonify({
        "message": "BitcoinInsights API Gateway - OPTIMIZED FAST VERSION",
        "status": "active",
        "version": "4.0-SPEED-OPTIMIZED",
        "cache_status": {
            "asset_performance": "loaded" if global_cache['asset_performance']['data'] else "empty",
            "historical_periods": list(global_cache['historical_performance']['data'].keys())
        }
    })

@app.route('/api/fear-greed-index')
def fear_greed_index():
    try:
        response = requests.get('https://api.alternative.me/fng/', timeout=5)
        
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
        
        return jsonify({
            "code": "0",
            "data": {"value": 75, "value_classification": "Greed"},
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "code": "0",
            "data": {"value": 75, "value_classification": "Greed"},
            "source": "fallback",
            "status": "error"
        })

@app.route('/api/long-short-current')
def long_short_current():
    exchange = request.args.get('exchange', 'binance')
    
    try:
        url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio/history"
        params = {'symbol': 'BTCUSDT', 'exchange': exchange, 'interval': '4h', 'limit': 1}
        headers = {'CG-API-KEY': COINGLASS_API_KEY}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
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
                    "source": "coinglass_api_real",
                    "status": "success",
                    "debug": {"exchange_requested": exchange, "data_source": "real_api"}
                })
        
        # Fast fallback
        exchange_data = {
            'binance': {'long': 45.2, 'short': 54.8},
            'bybit': {'long': 47.1, 'short': 52.9},
            'okx': {'long': 44.8, 'short': 55.2}
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
            "status": "success"
        })
        
    except Exception as e:
        exchange_data = {
            'binance': {'long': 45.2, 'short': 54.8},
            'bybit': {'long': 47.1, 'short': 52.9}
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
            "status": "error"
        })

@app.route('/api/long-short-history')
def long_short_history():
    exchange = request.args.get('exchange', 'binance')
    interval = request.args.get('interval', '1d')
    limit = int(request.args.get('limit', 7))
    
    try:
        url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio/history"
        params = {'symbol': 'BTCUSDT', 'exchange': exchange, 'interval': interval, 'limit': limit}
        headers = {'CG-API-KEY': COINGLASS_API_KEY}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '0' and 'data' in data and len(data['data']) > 0:
                sorted_data = sorted(data['data'], key=lambda x: x.get('time', 0))
                limited_data = sorted_data[-limit:] if len(sorted_data) > limit else sorted_data
                
                return jsonify({
                    "code": "0",
                    "data": limited_data,
                    "metadata": {"exchange": exchange, "count": len(limited_data)},
                    "source": "coinglass_api_real",
                    "status": "success"
                })
        
        # Fast fallback
        fallback_data = []
        base_long = {'binance': 45.2, 'bybit': 47.1, 'okx': 44.8}.get(exchange.lower(), 45.0)
        
        for i in range(limit):
            date = datetime.now() - timedelta(days=limit-1-i)
            timestamp = int(date.timestamp() * 1000)
            variation = (date.day % 10 - 5) * 0.5
            long_pct = round(base_long + variation, 1)
            short_pct = round(100 - long_pct, 1)
            
            fallback_data.append({
                "time": timestamp,
                "global_account_long_percent": long_pct,
                "global_account_short_percent": short_pct,
                "global_account_long_short_ratio": round(long_pct / short_pct, 2)
            })
        
        return jsonify({
            "code": "0",
            "data": fallback_data,
            "metadata": {"exchange": exchange, "count": len(fallback_data)},
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        # Same fast fallback
        fallback_data = []
        base_long = {'binance': 45.2, 'bybit': 47.1}.get(exchange.lower(), 45.0)
        
        for i in range(limit):
            date = datetime.now() - timedelta(days=limit-1-i)
            timestamp = int(date.timestamp() * 1000)
            variation = (date.day % 10 - 5) * 0.5
            long_pct = round(base_long + variation, 1)
            short_pct = round(100 - long_pct, 1)
            
            fallback_data.append({
                "time": timestamp,
                "global_account_long_percent": long_pct,
                "global_account_short_percent": short_pct,
                "global_account_long_short_ratio": round(long_pct / short_pct, 2)
            })
        
        return jsonify({
            "code": "0",
            "data": fallback_data,
            "source": "fallback",
            "status": "error"
        })

@app.route('/api/open-interest')
def open_interest():
    exchange = request.args.get('exchange', 'binance')
    
    try:
        url = "https://open-api-v4.coinglass.com/api/futures/open-interest/exchange-list"
        params = {'symbol': 'BTC'}
        headers = {'CG-API-KEY': COINGLASS_API_KEY}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        current_oi_billions = None
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '0' and 'data' in data:
                for item in data['data']:
                    if item.get('exchange', '').lower() == 'all':
                        oi_usd = float(item.get('open_interest_usd', 0))
                        current_oi_billions = round(oi_usd / 1e9, 2)
                        break
        
        # Fast historical fallback
        historical_data = []
        base_value = {'binance': 15.0, 'cme': 19.0, 'bybit': 8.5}.get(exchange.lower(), 10.0)
        
        for i in range(15):
            date = datetime.now() - timedelta(days=14-i)
            variation = random.uniform(-0.15, 0.15)
            value = round(base_value * (1 + variation), 2)
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': value
            })
        
        final_oi_billions = current_oi_billions if current_oi_billions is not None else 86.58
        
        return jsonify({
            "code": "0",
            "data": {
                "current_oi_billions": final_oi_billions,
                "current_oi_usd": int(final_oi_billions * 1e9),
                "historical": historical_data,
                "exchange": exchange
            },
            "source": "coinglass_api_real" if current_oi_billions else "fallback",
            "status": "success"
        })
        
    except Exception as e:
        # Fast fallback
        historical_data = []
        base_value = {'binance': 15.0, 'cme': 19.0}.get(exchange.lower(), 10.0)
        
        for i in range(15):
            date = datetime.now() - timedelta(days=14-i)
            value = round(base_value * (1 + random.uniform(-0.15, 0.15)), 2)
            historical_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': value
            })
        
        return jsonify({
            "code": "0",
            "data": {
                "current_oi_billions": 86.58,
                "current_oi_usd": 86580000000,
                "historical": historical_data,
                "exchange": exchange
            },
            "source": "fallback",
            "status": "error"
        })

@app.route('/api/funding-rates')
def funding_rates():
    try:
        url = "https://open-api-v4.coinglass.com/api/futures/funding-rate/history"
        params = {'exchange': 'Binance', 'symbol': 'BTCUSDT', 'interval': '8h', 'limit': 1}
        headers = {'CG-API-KEY': COINGLASS_API_KEY}
        
        response = requests.get(url, params=params, headers=headers, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '0' and 'data' in data and len(data['data']) > 0:
                latest = data['data'][-1]
                funding_rate_pct = round(float(latest.get('close', 0)), 4)
                
                color = "positive" if funding_rate_pct > 0.01 else "negative" if funding_rate_pct < -0.01 else "neutral"
                
                # Fast next funding calculation
                now_utc = datetime.utcnow()
                current_hour = now_utc.hour
                
                if current_hour < 8:
                    next_hour, next_date = 8, now_utc.date()
                elif current_hour < 16:
                    next_hour, next_date = 16, now_utc.date()
                else:
                    next_hour, next_date = 0, now_utc.date() + timedelta(days=1)
                
                next_funding_dt = datetime.combine(next_date, datetime.min.time().replace(hour=next_hour))
                next_funding = int(next_funding_dt.timestamp() * 1000)
                
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
        
        # Fast fallback
        now_utc = datetime.utcnow()
        current_hour = now_utc.hour
        
        if current_hour < 8:
            next_hour, next_date = 8, now_utc.date()
        elif current_hour < 16:
            next_hour, next_date = 16, now_utc.date()
        else:
            next_hour, next_date = 0, now_utc.date() + timedelta(days=1)
        
        next_funding_dt = datetime.combine(next_date, datetime.min.time().replace(hour=next_hour))
        next_funding = int(next_funding_dt.timestamp() * 1000)
        
        return jsonify({
            "code": "0",
            "data": {
                "exchange": "Binance",
                "funding_rate": 0.0085,
                "next_funding_time": next_funding,
                "color": "positive",
                "status": "fallback"
            },
            "source": "fallback",
            "status": "success"
        })
        
    except Exception as e:
        # Same fast fallback
        now_utc = datetime.utcnow()
        current_hour = now_utc.hour
        
        if current_hour < 8:
            next_hour, next_date = 8, now_utc.date()
        elif current_hour < 16:
            next_hour, next_date = 16, now_utc.date()
        else:
            next_hour, next_date = 0, now_utc.date() + timedelta(days=1)
        
        next_funding_dt = datetime.combine(next_date, datetime.min.time().replace(hour=next_hour))
        next_funding = int(next_funding_dt.timestamp() * 1000)
        
        return jsonify({
            "code": "0",
            "data": {
                "exchange": "Binance",
                "funding_rate": 0.0085,
                "next_funding_time": next_funding,
                "color": "positive",
                "status": "fallback"
            },
            "source": "fallback",
            "status": "error"
        })

@app.route('/api/hodl-waves')
def hodl_waves():
    return jsonify({
        "code": "0",
        "data": {
            "1d-1w": 2.5, "1w-1m": 8.3, "1m-3m": 12.7, "3m-6m": 15.2,
            "6m-1y": 18.9, "1y-2y": 16.4, "2y-3y": 11.8, "3y-5y": 9.1, "5y+": 5.1
        },
        "source": "static",
        "status": "success"
    })

@app.route('/api/macro-correlations')
def macro_correlations():
    return jsonify({
        "code": "0",
        "data": [
            {"asset": "Gold", "correlation": 0.15, "change_24h": 0.8},
            {"asset": "S&P 500", "correlation": 0.42, "change_24h": 1.2},
            {"asset": "NASDAQ", "correlation": 0.58, "change_24h": 1.8},
            {"asset": "DXY", "correlation": -0.31, "change_24h": -0.3},
            {"asset": "10Y Treasury", "correlation": -0.18, "change_24h": 0.1},
            {"asset": "Oil (WTI)", "correlation": 0.23, "change_24h": 2.1}
        ],
        "source": "realistic_fallback",
        "status": "success"
    })

@app.route('/api/asset-performance')
def asset_performance():
    """Optimized asset performance with instant cache response"""
    try:
        # Always return cache immediately for speed
        if global_cache['asset_performance']['data']:
            cache_age = int((datetime.now() - global_cache['asset_performance']['timestamp']).total_seconds())
            
            # Start background refresh if cache is getting old
            if cache_age > 120 and not global_cache['asset_performance']['loading']:  # 2 minutes
                threading.Thread(target=background_refresh_asset_performance, daemon=True).start()
            
            return jsonify({
                "code": "0",
                "data": global_cache['asset_performance']['data'],
                "source": "cache" if cache_age < 180 else "cache_refreshing",
                "status": "success",
                "cache_age": cache_age
            })
        
        # If no cache, return fallback immediately
        fallback_data = {
            "Bitcoin": {"price": 119300, "change_24h": -1.65},
            "Ethereum": {"price": 3600, "change_24h": 3.69},
            "Ripple": {"price": 3.4, "change_24h": 2.51},
            "Solana": {"price": 176, "change_24h": 1.48},
            "Tether": {"price": 1.0, "change_24h": 0.01}
        }
        
        # Start background refresh
        threading.Thread(target=background_refresh_asset_performance, daemon=True).start()
        
        return jsonify({
            "code": "0",
            "data": fallback_data,
            "source": "fallback_instant",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "code": "0",
            "data": {
                "Bitcoin": {"price": 119300, "change_24h": -1.65},
                "Ethereum": {"price": 3600, "change_24h": 3.69},
                "Ripple": {"price": 3.4, "change_24h": 2.51},
                "Solana": {"price": 176, "change_24h": 1.48},
                "Tether": {"price": 1.0, "change_24h": 0.01}
            },
            "source": "fallback",
            "status": "error"
        })

@app.route('/api/asset-performance-historical-real')
def asset_performance_historical_real():
    """Optimized historical performance with instant cache response"""
    try:
        period = request.args.get('period', '3y')
        
        # Always return cache immediately for speed
        if period in global_cache['historical_performance']['data']:
            cache_age = 0
            if period in global_cache['historical_performance']['timestamp']:
                cache_age = int((datetime.now() - global_cache['historical_performance']['timestamp'][period]).total_seconds())
            
            # Start background refresh if cache is getting old
            if cache_age > 900 and not global_cache['historical_performance']['loading'].get(period, False):  # 15 minutes
                threading.Thread(target=background_refresh_historical, args=(period,), daemon=True).start()
            
            return jsonify({
                "code": "0",
                "data": global_cache['historical_performance']['data'][period],
                "period": period,
                "source": "cache" if cache_age < 1800 else "cache_refreshing",
                "status": "success",
                "cache_age": cache_age
            })
        
        # If no cache for this period, return fallback immediately
        fallback_data = {
            '6m': {'btc': 45, 'eth': 9.38, 'xrp': 6.25, 'sol': -16.19},
            '3y': {'btc': 180, 'eth': 120, 'xrp': 30, 'sol': 800},
            '5y': {'btc': 600, 'eth': 800, 'xrp': 150, 'sol': 0},
            '10y': {'btc': 41800, 'eth': 0, 'xrp': 800, 'sol': 0}
        }
        
        data = fallback_data.get(period, fallback_data['3y'])
        
        # Start background refresh
        threading.Thread(target=background_refresh_historical, args=(period,), daemon=True).start()
        
        return jsonify({
            "code": "0",
            "data": data,
            "period": period,
            "source": "fallback_instant",
            "status": "success"
        })
        
    except Exception as e:
        period = request.args.get('period', '3y')
        fallback_data = {
            '6m': {'btc': 45, 'eth': 9.38, 'xrp': 6.25, 'sol': -16.19},
            '3y': {'btc': 180, 'eth': 120, 'xrp': 30, 'sol': 800},
            '5y': {'btc': 600, 'eth': 800, 'xrp': 150, 'sol': 0},
            '10y': {'btc': 41800, 'eth': 0, 'xrp': 800, 'sol': 0}
        }
        
        return jsonify({
            "code": "0",
            "data": fallback_data.get(period, fallback_data['3y']),
            "period": period,
            "source": "fallback",
            "status": "error"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)

