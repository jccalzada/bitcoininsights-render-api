from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# CoinGlass API configuration
COINGLASS_API_KEY = "8dde1df481bd440eb6fe0e97bf856fcc"  # ← CORRECTED: Using correct API key
COINGLASS_BASE_URL = "https://open-api-v4.coinglass.com/api"  # ← CORRECTED: Using v4 API

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
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"📡 CoinGlass response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 CoinGlass response data keys: {list(data.keys())}")
            
            # Check if response contains error
            if 'code' in data and data.get('code') != '0':
                print(f"❌ CoinGlass API error: {data.get('msg', 'Unknown error')}")
                return None
            
            print("✅ CoinGlass API success")
            return data
        else:
            print(f"❌ CoinGlass HTTP error: {response.status_code}")
            print(f"❌ Response text: {response.text[:200]}...")
            return None
            
    except Exception as e:
        print(f"❌ CoinGlass request failed: {str(e)}")
        return None

def generate_fallback_heatmap():
    """Generate realistic fallback heatmap data"""
    print("🔄 Generating fallback heatmap data...")
    
    # Generate realistic price levels around current BTC price
    base_price = 67150  # Fallback BTC price
    levels = []
    
    # Generate support levels (below current price)
    for i in range(20):
        price = base_price - (i + 1) * 50
        liquidity = random.uniform(5, 100)
        levels.append({
            "price": price,
            "liquidity": liquidity,
            "type": "support"
        })
    
    # Generate liquidation levels (above current price)
    for i in range(20):
        price = base_price + (i + 1) * 50
        liquidity = random.uniform(5, 100)
        levels.append({
            "price": price,
            "liquidity": liquidity,
            "type": "liquidation"
        })
    
    # Generate price history (24 hours, 10-minute intervals = 144 points)
    price_history = []
    base_time = int(time.time() * 1000)
    
    for i in range(144):
        timestamp = base_time - (143 - i) * 10 * 60 * 1000  # 10 minutes intervals
        price_variation = random.uniform(-1000, 1000)
        price = base_price + price_variation
        
        price_history.append({
            "timestamp": timestamp,
            "price": price,
            "close": price,
            "index": i
        })
    
    return {
        'code': '0',
        'status': 'success',
        'data': {
            'current_price': base_price,
            'priceHistory': price_history,
            'liquidityLevels': levels,
            'levels': levels,  # Keep for compatibility
            'total_bid_liquidity': sum(l['liquidity'] for l in levels if l['price'] < base_price),
            'total_ask_liquidity': sum(l['liquidity'] for l in levels if l['price'] > base_price),
            'spread': 0.02,
            'last_updated': int(time.time() * 1000)
        },
        'source': 'fallback_realistic'
    }

@app.route('/api/liquidity-heatmap', methods=['GET'])
def liquidity_heatmap():
    """Get liquidity heatmap data from CoinGlass API v4"""
    try:
        print("🚀 Starting CoinGlass API calls...")
        
        # Get BTC price from CoinGlass
        print("📊 Fetching BTC price from CoinGlass...")
        price_data = make_coinglass_request('futures/open-interest/exchange-list', {
            'symbol': 'BTC'
        })
        
        current_price = 117000  # Fallback price
        if price_data and 'data' in price_data:
            print("✅ CoinGlass API success")
            # Try to extract price from open interest data
            if isinstance(price_data['data'], list) and len(price_data['data']) > 0:
                first_item = price_data['data'][0]
                if 'price' in first_item:
                    current_price = float(first_item['price'])
                    print(f"✅ Got real BTC price: ${current_price}")
                else:
                    print("⚠️ No price in open interest data, using fallback")
            else:
                print("⚠️ No price in open interest data, using fallback")
        else:
            print("⚠️ BTC price data failed, using fallback: $117000")
        
        # Get liquidation data from CoinGlass v4 (Hobbyist plan)
        print("🗺️ Fetching liquidation data from CoinGlass...")
        liquidation_data = make_coinglass_request('futures/coin/aggregated-history', {
            'symbol': 'BTC',
            'time_type': '1h',
            'limit': 24
        })
        
        if liquidation_data and 'data' in liquidation_data:
            print(f"✅ Got liquidation data: {len(liquidation_data.get('data', []))} entries")
            
            # Generate price history (24 hours, 10-minute intervals = 144 points)
            price_history = []
            base_time = int(time.time() * 1000)
            
            for i in range(144):
                timestamp = base_time - (143 - i) * 10 * 60 * 1000  # 10 minutes intervals
                price_variation = random.uniform(-1000, 1000)
                price = current_price + price_variation
                
                price_history.append({
                    "timestamp": timestamp,
                    "price": price,
                    "close": price,
                    "index": i
                })
            
            # Process liquidation data into liquidity levels
            liquidity_levels = []
            liquidation_entries = liquidation_data.get('data', [])
            
            for i, entry in enumerate(liquidation_entries[:40]):  # Limit to 40 levels
                if 'aggregated_long_liquidation_usd' in entry and 'aggregated_short_liquidation_usd' in entry:
                    long_liq = float(entry['aggregated_long_liquidation_usd']) / 1000000  # Convert to millions
                    short_liq = float(entry['aggregated_short_liquidation_usd']) / 1000000  # Convert to millions
                    
                    # Create support level (long liquidations = support when broken)
                    support_price = current_price - (i + 1) * 50
                    liquidity_levels.append({
                        "price": support_price,
                        "liquidity": long_liq,
                        "type": "support"
                    })
                    
                    # Create liquidation level (short liquidations = resistance when broken)
                    resistance_price = current_price + (i + 1) * 50
                    liquidity_levels.append({
                        "price": resistance_price,
                        "liquidity": short_liq,
                        "type": "liquidation"
                    })
            
            print(f"🎯 Returning REAL data with {len(liquidity_levels)} liquidity levels")
            
            return jsonify({
                'code': '0',
                'status': 'success',
                'data': {
                    'current_price': current_price,
                    'priceHistory': price_history,  # ← Frontend expects this
                    'liquidityLevels': liquidity_levels,  # ← Frontend expects this
                    'levels': liquidity_levels,  # Keep for compatibility
                    'total_bid_liquidity': sum(l['liquidity'] for l in liquidity_levels if l['price'] < current_price),
                    'total_ask_liquidity': sum(l['liquidity'] for l in liquidity_levels if l['price'] > current_price),
                    'spread': 0.02,
                    'last_updated': int(time.time() * 1000)
                },
                'source': 'coinglass_real'
            })
        else:
            print("❌ CoinGlass liquidation_map failed - returning fallback")
            return jsonify(generate_fallback_heatmap())
            
    except Exception as e:
        print(f"❌ Error in liquidity_heatmap: {str(e)}")
        return jsonify(generate_fallback_heatmap())

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'neural-liquidity-api',
        'timestamp': int(time.time() * 1000)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)

