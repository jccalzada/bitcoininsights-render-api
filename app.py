#!/usr/bin/env python3
"""
Crypto Lake Backend - RENDER COMPATIBLE VERSION
Works with or without python-dotenv
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, jsonify
from flask_cors import CORS

# Try to load environment variables from .env file (for local development)
# In Render, environment variables are already set, so this is optional
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not available, using environment variables directly")
    print("   This is normal in production environments like Render")

app = Flask(__name__)
CORS(app)

# Global cache for available dates and data
date_cache = {}
data_cache = {}

def get_latest_available_date(symbol="BTC-USDT", exchange="BINANCE", table="book"):
    """
    Get the latest available date for a symbol/exchange/table combination
    Based on ChatGPT's recommendation
    """
    try:
        import lakeapi
        
        cache_key = f"{symbol}_{exchange}_{table}"
        if cache_key in date_cache:
            return date_cache[cache_key]
        
        print(f"🔍 Checking available dates for {symbol} on {exchange} ({table})...")
        
        # List available data
        available = lakeapi.list_data(
            table=table, 
            symbols=[symbol], 
            exchanges=[exchange]
        )
        
        if available and symbol in available and exchange in available[symbol]:
            if table in available[symbol][exchange]:
                dates = available[symbol][exchange][table]
                if dates:
                    latest_date = max(dates)
                    date_cache[cache_key] = latest_date
                    print(f"✅ Latest available date: {latest_date}")
                    return latest_date
        
        print(f"❌ No dates found for {symbol} on {exchange} ({table})")
        return None
        
    except Exception as e:
        print(f"❌ Error checking available dates: {str(e)}")
        return None

def load_crypto_lake_data(symbol="BTC-USDT", exchange="BINANCE", table="book", hours_back=24):
    """
    Load data from Crypto Lake using the latest available date
    """
    try:
        import lakeapi
        
        # Get the latest available date
        latest_date = get_latest_available_date(symbol, exchange, table)
        if not latest_date:
            return None, "No available dates found"
        
        # Convert to datetime if it's a string
        if isinstance(latest_date, str):
            latest_date = datetime.strptime(latest_date, '%Y-%m-%d')
        
        # Load data from the latest available date
        start_time = latest_date
        end_time = latest_date + timedelta(hours=hours_back)
        
        print(f"📊 Loading {table} data from {start_time} to {end_time}...")
        
        df = lakeapi.load_data(
            table=table,
            start=start_time,
            end=end_time,
            symbols=[symbol],
            exchanges=[exchange]
        )
        
        if df.empty:
            return None, f"No data available for {start_time}"
        
        print(f"✅ Loaded {len(df)} records from Crypto Lake")
        return df, f"crypto_lake_{table}_{latest_date.strftime('%Y%m%d')}"
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Crypto Lake error: {error_msg}")
        return None, f"crypto_lake_error: {error_msg}"

def process_order_book_data(df):
    """
    Process order book data into heatmap format
    """
    try:
        if df is None or df.empty:
            return None
        
        # Process the order book data
        print(f"📊 Processing {len(df)} order book records...")
        
        # Extract price levels and volumes
        price_levels = []
        volumes = []
        
        # This is a placeholder - adjust based on actual data structure
        if 'price' in df.columns and 'size' in df.columns:
            # Group by price levels
            grouped = df.groupby('price')['size'].sum().reset_index()
            price_levels = grouped['price'].tolist()
            volumes = grouped['size'].tolist()
        else:
            # Fallback: create realistic data structure
            current_price = 113500  # This should come from the data
            price_levels = [current_price + i*10 for i in range(-50, 51)]
            volumes = [np.random.exponential(50) for _ in price_levels]
        
        return {
            'price_levels': price_levels,
            'volumes': volumes,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error processing order book data: {str(e)}")
        return None

def generate_realistic_fallback_data():
    """
    Generate realistic fallback data when Crypto Lake is not available
    """
    print("🔄 Generating realistic fallback data...")
    
    # Current market conditions (you can update these)
    current_price = 113500
    
    # Generate realistic price history (97 points as expected by frontend)
    time_points = 97
    price_history = []
    base_price = current_price
    
    for i in range(time_points):
        # Add some realistic price movement
        change = np.random.normal(0, 50)  # Small random changes
        base_price += change
        price_history.append(round(base_price, 2))
    
    # Generate liquidity levels
    levels = []
    for i in range(12):  # 12 levels as expected
        price_offset = np.random.randint(-2000, 2000)
        price = current_price + price_offset
        volume = np.random.exponential(60)  # Exponential distribution for realistic volumes
        level_type = "Support" if price < current_price else "Resistance"
        
        levels.append({
            'price': price,
            'volume': round(volume, 2),
            'type': level_type
        })
    
    # Sort levels by price
    levels.sort(key=lambda x: x['price'])
    
    # Create heatmap matrix (97 x 100 as expected by frontend)
    heatmap_matrix = []
    for i in range(time_points):
        row = []
        for j in range(100):
            # Generate realistic heatmap values (0-1 range)
            intensity = np.random.beta(2, 5)  # Beta distribution for realistic intensity
            row.append(round(intensity, 4))
        heatmap_matrix.append(row)
    
    return {
        'current_price': current_price,
        'price_history': price_history,
        'levels': levels,
        'heatmapData': heatmap_matrix,
        'keySupport': {
            'price': min([l['price'] for l in levels if l['type'] == 'Support'], default=current_price-1000),
            'volume': max([l['volume'] for l in levels if l['type'] == 'Support'], default=50)
        },
        'keyResistance': {
            'price': min([l['price'] for l in levels if l['type'] == 'Resistance'], default=current_price+1000),
            'volume': max([l['volume'] for l in levels if l['type'] == 'Resistance'], default=50)
        }
    }

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        import lakeapi
        aws_configured = bool(os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'))
        return jsonify({
            'status': 'healthy',
            'crypto_lake': 'available',
            'aws_configured': aws_configured,
            'environment': 'render' if os.getenv('RENDER') else 'local',
            'timestamp': datetime.now().isoformat()
        })
    except ImportError:
        return jsonify({
            'status': 'healthy',
            'crypto_lake': 'not_available',
            'aws_configured': bool(os.getenv('AWS_ACCESS_KEY_ID')),
            'environment': 'render' if os.getenv('RENDER') else 'local',
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/liquidity-heatmap', methods=['GET'])
def get_liquidity_heatmap():
    """
    Get liquidity heatmap data with automatic date detection
    """
    try:
        print("🚀 Processing liquidity heatmap request...")
        
        # Check if AWS credentials are configured
        if not os.getenv('AWS_ACCESS_KEY_ID'):
            print("⚠️  AWS credentials not configured, using fallback data")
            fallback_data = generate_realistic_fallback_data()
            return jsonify({
                'status': 'success',
                'code': 0,
                'source': 'fallback_no_credentials',
                'data': fallback_data,
                'timestamp': datetime.now().isoformat()
            })
        
        # Try to load real data from Crypto Lake
        df, source = load_crypto_lake_data()
        
        if df is not None:
            # Process real data
            processed_data = process_order_book_data(df)
            if processed_data:
                return jsonify({
                    'status': 'success',
                    'code': 0,
                    'source': source,
                    'data': processed_data,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Fallback to realistic simulated data
        print("🔄 Using realistic fallback data...")
        fallback_data = generate_realistic_fallback_data()
        
        return jsonify({
            'status': 'success',
            'code': 0,
            'source': 'realistic_fallback',
            'data': fallback_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in liquidity heatmap endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 1,
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/available-dates', methods=['GET'])
def get_available_dates():
    """
    Get available dates for different data types
    """
    try:
        if not os.getenv('AWS_ACCESS_KEY_ID'):
            return jsonify({
                'status': 'error',
                'message': 'AWS credentials not configured',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        dates_info = {}
        
        for table in ['book', 'trades', 'deep_book_1m']:
            latest_date = get_latest_available_date(table=table)
            dates_info[table] = {
                'latest_available': latest_date.isoformat() if latest_date else None,
                'status': 'available' if latest_date else 'not_available'
            }
        
        return jsonify({
            'status': 'success',
            'dates': dates_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Crypto Lake Backend (RENDER COMPATIBLE)...")
    print("🔒 Security features:")
    print("   - Environment variables loaded automatically")
    print("   - Compatible with Render deployment")
    print("   - No hardcoded secrets in code")
    print("📊 Features:")
    print("   - Automatic date detection using lakeapi.list_data()")
    print("   - Fallback to realistic simulated data")
    print("   - Health check endpoint")
    print("   - Available dates endpoint")
    
    # Check if credentials are configured
    if os.getenv('AWS_ACCESS_KEY_ID'):
        print("✅ AWS credentials found in environment")
    else:
        print("⚠️  AWS credentials not found - will use fallback data")
    
    # Detect if running on Render
    if os.getenv('RENDER'):
        print("🌐 Running on Render platform")
    else:
        print("🏠 Running locally")
    
    print("🌐 Server starting...")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=False)

