"""
Crypto Lake Hybrid Heatmap System - MEMORY OPTIMIZED VERSION
Tactical (24-48h) + Strategic (7-30d) views with institutional analysis
"""

import os
import json
import time
import random
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
import gc  # Garbage collection for memory management

def convert_to_json_serializable(obj):
    """Convert NumPy types to JSON serializable Python types"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not available, using environment variables directly")

app = Flask(__name__)
CORS(app)

# Global cache for data - OPTIMIZED
data_cache = {}
last_cache_update = None
CACHE_DURATION = 300  # 5 minutes cache

# CoinGlass API configuration
COINGLASS_API_KEY = "8dde1df481bd440eb6fe0e97bf856fcc"
COINGLASS_BASE_URL = "https://open-api-v4.coinglass.com/api"

def clear_memory():
    """Force garbage collection to free memory"""
    gc.collect()

def get_real_btc_price():
    """Get real Bitcoin price from CoinGlass API"""
    try:
        headers = {
            'coinglassSecret': COINGLASS_API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{COINGLASS_BASE_URL}/futures/openInterest/chart",
            headers=headers,
            params={
                'symbol': 'BTC',
                'interval': '1h',
                'limit': 1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                price = float(data['data'][0]['price'])
                print(f"💰 Real BTC price from CoinGlass: ${price:.2f}")
                return price
        
        print("⚠️ CoinGlass API failed, using fallback price")
        return None
        
    except Exception as e:
        print(f"❌ Error fetching real price: {str(e)}")
        return None

def generate_optimized_fallback_data(view_type="tactical"):
    """Generate memory-optimized fallback data"""
    try:
        print(f"🎯 Generating OPTIMIZED {view_type} fallback data...")
        
        # Get real current price
        real_price = get_real_btc_price()
        current_price = real_price if real_price else 115000
        print(f"💰 Current price: ${current_price:.2f} ({'REAL' if real_price else 'FALLBACK'})")
        
        # MEMORY OPTIMIZATION: Reduce matrix sizes
        if view_type == "tactical":
            # Tactical: Reduced from 691x288 to 345x144 (75% reduction)
            time_points = pd.date_range(end=datetime.now(), periods=144, freq='10min')  # 10min instead of 5min
            price_levels = np.linspace(current_price * 0.95, current_price * 1.05, 345)  # 345 instead of 691
            
            # Moderate filters for better visibility
            filter_threshold_critical = 95    # Top 5%
            filter_threshold_significant = 85 # Top 15%
            filter_threshold_medium = 70      # Top 30%
            filter_threshold_low = 50         # Top 50%
            
            print("⚡ TACTICAL MODE (24h) - OPTIMIZED FILTERS:")
            print(f"🔴 CRITICAL (Top 5%): {filter_threshold_critical}")
            print(f"🟡 SIGNIFICANT (Top 15%): {filter_threshold_significant}")
            print(f"🟢 MEDIUM (Top 30%): {filter_threshold_medium}")
            print(f"🔵 LOW (Top 50%): {filter_threshold_low}")
            
        else:
            # Strategic: Reduced from 346x336 to 173x168 (75% reduction)
            time_points = pd.date_range(end=datetime.now(), periods=168, freq='1h')  # 1h instead of 30min
            price_levels = np.linspace(current_price * 0.85, current_price * 1.15, 173)  # 173 instead of 346
            
            # Aggressive filters for macro view
            filter_threshold_critical = 98    # Top 2%
            filter_threshold_significant = 90 # Top 10%
            filter_threshold_medium = 80      # Top 20%
            filter_threshold_low = 70         # Top 30%
            
            print("🏛️ STRATEGIC MODE (7 days) - OPTIMIZED FILTERS:")
            print(f"🔴 INSTITUTIONAL (Top 2%): {filter_threshold_critical}")
            print(f"🟡 WHALE (Top 10%): {filter_threshold_significant}")
            print(f"🟢 SMART MONEY (Top 20%): {filter_threshold_medium}")
            print(f"🔵 CONTEXT (Top 30%): {filter_threshold_low}")
        
        # MEMORY OPTIMIZATION: Generate matrix in chunks
        institutional_matrix = []
        chunk_size = 50  # Process 50 price levels at a time
        
        total_zones = 0
        level_counts = {'critical': 0, 'significant': 0, 'medium': 0, 'low': 0}
        
        for chunk_start in range(0, len(price_levels), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(price_levels))
            chunk_price_levels = price_levels[chunk_start:chunk_end]
            
            for price_level in chunk_price_levels:
                time_series = []
                
                for j, timestamp in enumerate(time_points):
                    # Simplified intensity calculation
                    distance_factor = abs(price_level - current_price) / current_price
                    base_intensity = max(25, 200 * (1 - distance_factor * 2))
                    
                    # Reduced complexity for memory optimization
                    time_factor = 1 + 0.3 * np.sin(j * 0.1)
                    noise_factor = random.uniform(0.8, 1.2)
                    
                    intensity = base_intensity * time_factor * noise_factor
                    intensity_percentile = (intensity - 25) / (200 - 25) * 100
                    
                    # Apply optimized filters
                    if intensity_percentile >= filter_threshold_critical:
                        final_intensity = intensity
                        level_counts['critical'] += 1
                    elif intensity_percentile >= filter_threshold_significant:
                        final_intensity = intensity
                        level_counts['significant'] += 1
                    elif intensity_percentile >= filter_threshold_medium:
                        final_intensity = intensity
                        level_counts['medium'] += 1
                    elif intensity_percentile >= filter_threshold_low:
                        final_intensity = intensity * 0.6  # Reduced intensity for low level
                        level_counts['low'] += 1
                    else:
                        final_intensity = 0
                    
                    time_series.append(max(0, final_intensity))
                    total_zones += 1
                
                institutional_matrix.append(time_series)
            
            # Force garbage collection after each chunk
            clear_memory()
        
        print(f"🗂️ Created {total_zones} optimized liquidity zones")
        print(f"🔴 Critical zones: {level_counts['critical']}")
        print(f"🟡 Significant zones: {level_counts['significant']}")
        print(f"🟢 Medium zones: {level_counts['medium']}")
        print(f"🔵 Low zones: {level_counts['low']}")
        
        result = {
            'current_price': current_price,
            'institutional_matrix': institutional_matrix,
            'price_levels': price_levels.tolist(),
            'time_points': [int(ts.timestamp() * 1000) for ts in time_points],
            'levels': len(price_levels),
            'data_points': len(time_points),
            'source': 'optimized_simulation'
        }
        
        # Clear temporary variables
        del institutional_matrix, price_levels, time_points
        clear_memory()
        
        return result
        
    except Exception as e:
        print(f"❌ Error generating optimized fallback data: {str(e)}")
        clear_memory()
        return None

# Historical price data for Bitcoin price line
def get_historical_price_from_cryptolake_trades(hours=48):
    """Get historical Bitcoin price data from CryptoLake trades table"""
    try:
        print(f"💰 Attempting to get {hours}h of historical price data from CryptoLake...")
        
        # This would use the actual CryptoLake API
        # For now, return None to trigger fallback
        return None
        
    except Exception as e:
        print(f"❌ Error fetching historical price from CryptoLake: {str(e)}")
        return None

def generate_realistic_bitcoin_price_history(hours=48, current_price=115000):
    """Generate realistic Bitcoin price history as fallback"""
    try:
        print(f"💰 Generating realistic Bitcoin price history for {hours}h...")
        
        # Generate timestamps (every 5 minutes)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        timestamps = pd.date_range(start=start_time, end=end_time, freq='5min')
        
        # Generate realistic price movement
        prices = []
        current = current_price
        
        for i, ts in enumerate(timestamps):
            # Add realistic volatility and trends
            trend = 0.001 * np.sin(i * 0.01)  # Long-term trend
            volatility = random.gauss(0, 0.005)  # Random volatility
            mean_reversion = -0.0001 * (current - current_price) / current_price  # Mean reversion
            
            change = trend + volatility + mean_reversion
            current = current * (1 + change)
            
            # Keep within reasonable bounds
            current = max(current_price * 0.9, min(current_price * 1.1, current))
            prices.append(current)
        
        return {
            'timestamps': [int(ts.timestamp() * 1000) for ts in timestamps],
            'prices': prices
        }
        
    except Exception as e:
        print(f"❌ Error generating realistic price history: {str(e)}")
        return None

# Bitcoin price endpoint
@app.route('/api/bitcoin-price', methods=['GET'])
def get_bitcoin_price_history():
    """Get historical Bitcoin price data for the heatmap price line"""
    try:
        hours = int(request.args.get('hours', 48))
        print(f"💰 Bitcoin price request for {hours} hours")
        
        # Try to get real data from CryptoLake
        real_data = get_historical_price_from_cryptolake_trades(hours)
        
        if real_data:
            print("✅ Using real CryptoLake price data")
            return jsonify({
                'success': True,
                'data': real_data,
                'source': 'cryptolake_trades'
            })
        else:
            # Use realistic fallback
            print("⚠️ CryptoLake unavailable, using realistic fallback")
            current_price = get_real_btc_price() or 115000
            fallback_data = generate_realistic_bitcoin_price_history(hours, current_price)
            
            if fallback_data:
                return jsonify({
                    'success': True,
                    'data': fallback_data,
                    'source': 'realistic_simulation'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate price data'
                }), 500
                
    except Exception as e:
        print(f"❌ Error in bitcoin price endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Main heatmap endpoint - OPTIMIZED
@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    """Get liquidity heatmap data with tactical/strategic views - MEMORY OPTIMIZED"""
    try:
        view_type = request.args.get('view', 'tactical')
        days_back = int(request.args.get('days', 2 if view_type == 'tactical' else 7))  # Reduced default days
        
        print(f"📊 OPTIMIZED Heatmap request: {view_type} view, {days_back} days")
        
          # Check cache first
        current_time = time.time()
        cache_key = f"{view_type}_{days}"
        
        # Declare global variables first
        global last_cache_update
        
        if (cache_key in data_cache and 
            last_cache_update and 
            current_time - last_cache_update < CACHE_DURATION):
            print("✅ Using cached data")
            return jsonify(data_cache[cache_key])
        
        # Generate optimized fallback data
        data = generate_optimized_fallback_data(view_type)
        
        if data:
            print("✅ Using optimized fallback data")
            
            # Cache the result
            data_cache[cache_key] = {
                'success': True,
                'data': convert_to_json_serializable(data),
                'view': view_type,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update cache timestamp
            last_cache_update = current_time
            
            # Clear memory after caching
            clear_memory()
            
            return jsonify(data_cache[cache_key])
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate heatmap data'
            }), 500
            
    except Exception as e:
        print(f"❌ Error in heatmap endpoint: {str(e)}")
        clear_memory()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'memory_optimized': True
    })

if __name__ == '__main__':
    print("🚀 Starting MEMORY OPTIMIZED Crypto Lake Heatmap API...")
    print("📊 Tactical view: 24h with 345x144 matrix (75% memory reduction)")
    print("🏛️ Strategic view: 7 days with 173x168 matrix (75% memory reduction)")
    print("🧹 Memory management: Garbage collection enabled")
    print("💾 Caching: 5-minute cache duration")
    
    # Force initial garbage collection
    clear_memory()
    
    app.run(host='0.0.0.0', port=5000, debug=False)  # Debug=False for production

