from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time
import random
import math
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# CoinGlass API configuration
COINGLASS_API_KEY = "8dde1df481bd440eb6fe0e97bf856fcc"
COINGLASS_BASE_URL = "https://open-api-v4.coinglass.com/api"

def make_coinglass_request(endpoint, params=None):
    """Make a request to CoinGlass API"""
    url = f"{COINGLASS_BASE_URL}/{endpoint}"
    headers = {
        'CG-API-KEY': COINGLASS_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🌐 Making CoinGlass request to: {url}")
        print(f"🔑 Using API key: {COINGLASS_API_KEY[:8]}...")
        if params:
            print(f"📋 Parameters: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"📡 CoinGlass response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 CoinGlass response data keys: {list(data.keys())}")
            print(f"📊 Full response: {data}")
            
            if 'code' in data and data.get('code') != '0':
                print(f"❌ CoinGlass API error: {data.get('msg', 'Unknown error')}")
                return None
            
            print("✅ CoinGlass API success")
            return data
        else:
            print(f"❌ CoinGlass HTTP error: {response.status_code}")
            print(f"❌ Response text: {response.text[:500]}...")
            return None
            
    except Exception as e:
        print(f"❌ CoinGlass request failed: {str(e)}")
        return None

def test_ohlc_endpoints():
    """Test different OHLC endpoints to see which ones work"""
    print("🧪 TESTING OHLC ENDPOINTS...")
    
    # Calculate time range (last 24 hours)
    end_time = int(datetime.utcnow().timestamp() * 1000)
    start_time = int((datetime.utcnow() - timedelta(days=1)).timestamp() * 1000)
    
    print(f"⏰ Time range: {start_time} to {end_time}")
    print(f"⏰ Human readable: {datetime.fromtimestamp(start_time/1000)} to {datetime.fromtimestamp(end_time/1000)}")
    
    # Test endpoints
    endpoints_to_test = [
        {
            'name': 'aggregrated-history (double r)',
            'endpoint': 'futures/coin/aggregrated-history',
            'params': {
                'symbol': 'BTC',
                'interval': '4h',
                'start_time': start_time,
                'end_time': end_time
            }
        },
        {
            'name': 'aggregated-history (single r)',
            'endpoint': 'futures/coin/aggregated-history',
            'params': {
                'symbol': 'BTC',
                'interval': '4h',
                'start_time': start_time,
                'end_time': end_time
            }
        },
        {
            'name': 'price/ohlc-history',
            'endpoint': 'price/ohlc-history',
            'params': {
                'symbol': 'BTC',
                'interval': '4h',
                'start_time': start_time,
                'end_time': end_time
            }
        },
        {
            'name': 'futures/price-change-list',
            'endpoint': 'futures/price-change-list',
            'params': {
                'symbol': 'BTC'
            }
        }
    ]
    
    results = {}
    
    for test in endpoints_to_test:
        print(f"\n🔍 TESTING: {test['name']}")
        print(f"📍 Endpoint: {test['endpoint']}")
        
        result = make_coinglass_request(test['endpoint'], test['params'])
        
        if result:
            print(f"✅ SUCCESS: {test['name']}")
            results[test['name']] = {
                'status': 'success',
                'data': result
            }
        else:
            print(f"❌ FAILED: {test['name']}")
            results[test['name']] = {
                'status': 'failed',
                'data': None
            }
    
    return results

@app.route('/api/test-ohlc', methods=['GET'])
def test_ohlc():
    """Test OHLC endpoints"""
    try:
        print("🧪 Starting OHLC endpoint tests...")
        results = test_ohlc_endpoints()
        
        return jsonify({
            'status': 'completed',
            'test_results': results,
            'timestamp': int(time.time() * 1000)
        })
        
    except Exception as e:
        print(f"❌ Error in test_ohlc: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/liquidity-heatmap', methods=['GET'])
def liquidity_heatmap():
    """Get liquidity heatmap data - with OHLC testing"""
    try:
        print("🚀 Starting CoinGlass API calls with OHLC testing...")
        
        # First, test OHLC endpoints
        print("🧪 Testing OHLC endpoints first...")
        ohlc_results = test_ohlc_endpoints()
        
        # Check if any OHLC endpoint worked
        working_ohlc = None
        for name, result in ohlc_results.items():
            if result['status'] == 'success':
                print(f"✅ Found working OHLC endpoint: {name}")
                working_ohlc = result['data']
                break
        
        current_price = 113000  # Realistic fallback
        
        if working_ohlc:
            print("🎯 Using REAL OHLC data for price history!")
            # Process OHLC data into price history
            price_history = []
            
            if 'data' in working_ohlc and isinstance(working_ohlc['data'], list):
                ohlc_data = working_ohlc['data']
                print(f"📊 Got {len(ohlc_data)} OHLC candles")
                
                # Interpolate between OHLC candles to create 144 points
                for i in range(144):
                    # Map 144 points to available OHLC data
                    candle_index = int((i / 144) * len(ohlc_data))
                    candle_index = min(candle_index, len(ohlc_data) - 1)
                    
                    candle = ohlc_data[candle_index]
                    
                    # Use close price from real OHLC data
                    if 'close' in candle:
                        price = float(candle['close'])
                    elif 'c' in candle:
                        price = float(candle['c'])
                    else:
                        price = current_price
                    
                    timestamp = int(time.time() * 1000) - (143 - i) * 10 * 60 * 1000
                    
                    price_history.append({
                        "timestamp": timestamp,
                        "price": round(price, 2),
                        "close": round(price, 2),
                        "index": i
                    })
                
                # Update current price from latest candle
                if ohlc_data:
                    latest_candle = ohlc_data[-1]
                    if 'close' in latest_candle:
                        current_price = float(latest_candle['close'])
                    elif 'c' in latest_candle:
                        current_price = float(latest_candle['c'])
            
        else:
            print("❌ No OHLC endpoints working, using realistic synthetic data")
            # Generate realistic synthetic price history
            price_history = []
            base_time = int(time.time() * 1000)
            
            for i in range(144):
                timestamp = base_time - (143 - i) * 10 * 60 * 1000
                time_factor = i / 144.0
                
                # Realistic movement
                trend = -200 * time_factor
                volatility = 50 * math.sin(time_factor * math.pi * 4)
                noise = random.uniform(-25, 25)
                
                price = current_price + trend + volatility + noise
                price = max(current_price - 500, min(current_price + 300, price))
                
                price_history.append({
                    "timestamp": timestamp,
                    "price": round(price, 2),
                    "close": round(price, 2),
                    "index": i
                })
        
        # Get liquidation data (this we know works)
        liquidation_data = make_coinglass_request('futures/liquidation/history', {
            'exchange': 'Binance',
            'symbol': 'BTCUSDT',
            'interval': '4h',
            'limit': 24
        })
        
        liquidity_levels = []
        if liquidation_data and 'data' in liquidation_data:
            liquidation_entries = liquidation_data.get('data', [])
            
            for i, entry in enumerate(liquidation_entries[:40]):
                if 'long_liquidation_usd' in entry and 'short_liquidation_usd' in entry:
                    long_liq = float(entry['long_liquidation_usd']) / 1000000
                    short_liq = float(entry['short_liquidation_usd']) / 1000000
                    
                    support_price = current_price - (i + 1) * 50
                    liquidity_levels.append({
                        "price": support_price,
                        "liquidity": long_liq,
                        "type": "support"
                    })
                    
                    resistance_price = current_price + (i + 1) * 50
                    liquidity_levels.append({
                        "price": resistance_price,
                        "liquidity": short_liq,
                        "type": "liquidation"
                    })
        
        source = 'coinglass_real_ohlc' if working_ohlc else 'realistic_synthetic'
        
        return jsonify({
            'code': '0',
            'status': 'success',
            'data': {
                'current_price': current_price,
                'priceHistory': price_history,
                'liquidityLevels': liquidity_levels,
                'levels': liquidity_levels,
                'total_bid_liquidity': sum(l['liquidity'] for l in liquidity_levels if l['price'] < current_price),
                'total_ask_liquidity': sum(l['liquidity'] for l in liquidity_levels if l['price'] > current_price),
                'spread': 0.02,
                'last_updated': int(time.time() * 1000),
                'ohlc_test_results': ohlc_results
            },
            'source': source
        })
        
    except Exception as e:
        print(f"❌ Error in liquidity_heatmap: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'neural-liquidity-api-ohlc-test',
        'timestamp': int(time.time() * 1000)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)

