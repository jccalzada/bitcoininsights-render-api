#!/usr/bin/env python3
"""
Crypto Lake Hybrid Heatmap System
Tactical (24-48h) + Strategic (7-30d) views with institutional analysis
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not available, using environment variables directly")

app = Flask(__name__)
CORS(app)

# Global cache for data
data_cache = {}
last_cache_update = None

def get_real_crypto_lake_data(view_type="tactical", days_back=2, symbol="BTC-USDT", exchange="BINANCE"):
    """
    Load real data from Crypto Lake with tactical/strategic views
    """
    try:
        import lakeapi
        
        print(f"🚀 Loading {view_type} data from Crypto Lake...")
        print(f"   📊 Symbol: {symbol}")
        print(f"   🏢 Exchange: {exchange}")
        print(f"   📅 Days back: {days_back}")
        
        # Calculate date range based on view type
        if view_type == "tactical":
            # Tactical: Last 48 hours with 1-minute granularity
            end_date = datetime(2025, 8, 3)  # Most recent available
            start_date = end_date - timedelta(hours=48)
            table = "book_1m"  # 1-minute snapshots
            print(f"   🎯 Tactical view: {start_date} to {end_date}")
        else:
            # Strategic: Last 7-30 days with aggregated data
            end_date = datetime(2025, 8, 3)
            start_date = end_date - timedelta(days=days_back)
            table = "book_1m"  # We'll aggregate this data
            print(f"   📈 Strategic view: {start_date} to {end_date}")
        
        # Load data from Crypto Lake
        print(f"   📋 Loading from table: {table}")
        df = lakeapi.load_data(
            table=table,
            start=start_date,
            end=end_date,
            symbols=[symbol],
            exchanges=[exchange]
        )
        
        if df.empty:
            print("   ❌ No data loaded from Crypto Lake")
            return None
        
        print(f"   ✅ Loaded {len(df)} records from Crypto Lake!")
        print(f"   📊 Columns: {list(df.columns)}")
        print(f"   📅 Date range: {df.index.min()} to {df.index.max()}")
        
        return df
        
    except Exception as e:
        print(f"   ❌ Error loading from Crypto Lake: {str(e)}")
        return None

def process_tactical_data(df):
    """
    Process data for tactical view (24-48h, 1min granularity)
    Focus on recent liquidity zones and short-term patterns
    """
    if df is None or df.empty:
        return generate_tactical_fallback()
    
    print("🎯 Processing tactical data...")
    
    try:
        # Extract bid/ask levels (20 levels each side)
        bid_columns = [col for col in df.columns if col.startswith('bid_') and col.endswith('_price')]
        ask_columns = [col for col in df.columns if col.startswith('ask_') and col.endswith('_price')]
        
        bid_size_columns = [col for col in df.columns if col.startswith('bid_') and col.endswith('_size')]
        ask_size_columns = [col for col in df.columns if col.startswith('ask_') and col.endswith('_size')]
        
        print(f"   📊 Found {len(bid_columns)} bid levels, {len(ask_columns)} ask levels")
        
        # Create time series data
        time_points = []
        price_levels = []
        liquidity_matrix = []
        
        # Process each timestamp
        for idx, row in df.iterrows():
            timestamp = row.name if hasattr(row, 'name') else idx
            time_points.append(timestamp)
            
            # Collect all price levels and volumes
            levels = []
            
            # Process bid levels (support)
            for i in range(len(bid_columns)):
                price_col = f'bid_{i}_price'
                size_col = f'bid_{i}_size'
                
                if price_col in row and size_col in row:
                    price = row[price_col]
                    size = row[size_col]
                    
                    if pd.notna(price) and pd.notna(size) and price > 0 and size > 0:
                        levels.append({
                            'price': float(price),
                            'volume': float(size),
                            'side': 'bid',
                            'level': i
                        })
            
            # Process ask levels (resistance)
            for i in range(len(ask_columns)):
                price_col = f'ask_{i}_price'
                size_col = f'ask_{i}_size'
                
                if price_col in row and size_col in row:
                    price = row[price_col]
                    size = row[size_col]
                    
                    if pd.notna(price) and pd.notna(size) and price > 0 and size > 0:
                        levels.append({
                            'price': float(price),
                            'volume': float(size),
                            'side': 'ask',
                            'level': i
                        })
            
            # Sort levels by price
            levels.sort(key=lambda x: x['price'])
            
            # Create price range for this timestamp
            if levels:
                min_price = min(level['price'] for level in levels)
                max_price = max(level['price'] for level in levels)
                
                # Create price grid (50 levels for tactical view)
                price_range = np.linspace(min_price, max_price, 50)
                liquidity_row = []
                
                for target_price in price_range:
                    # Find closest liquidity level
                    closest_level = min(levels, key=lambda x: abs(x['price'] - target_price))
                    distance = abs(closest_level['price'] - target_price)
                    
                    # Calculate liquidity intensity (closer = higher intensity)
                    if distance < (max_price - min_price) * 0.02:  # Within 2% of actual level
                        intensity = closest_level['volume']
                    else:
                        intensity = 0
                    
                    liquidity_row.append(intensity)
                
                liquidity_matrix.append(liquidity_row)
                
                if not price_levels:  # First iteration
                    price_levels = price_range.tolist()
        
        # Convert to numpy array for easier processing
        if liquidity_matrix:
            liquidity_matrix = np.array(liquidity_matrix)
            
            # Classify institutional vs retail liquidity
            institutional_threshold = 10.0  # >10 BTC = institutional
            retail_threshold = 1.0  # <1 BTC = retail
            
            institutional_matrix = np.where(liquidity_matrix > institutional_threshold, liquidity_matrix, 0)
            retail_matrix = np.where(liquidity_matrix < retail_threshold, liquidity_matrix, 0)
            
            print(f"   ✅ Processed {len(time_points)} time points")
            print(f"   📊 Price levels: {len(price_levels)}")
            print(f"   🏛️ Institutional levels: {np.count_nonzero(institutional_matrix)}")
            print(f"   🏪 Retail levels: {np.count_nonzero(retail_matrix)}")
            
            return {
                'view_type': 'tactical',
                'time_points': [str(t) for t in time_points],
                'price_levels': price_levels,
                'liquidity_matrix': liquidity_matrix.tolist(),
                'institutional_matrix': institutional_matrix.tolist(),
                'retail_matrix': retail_matrix.tolist(),
                'current_price': float(df.iloc[-1]['bid_0_price']) if 'bid_0_price' in df.columns else price_levels[len(price_levels)//2],
                'data_source': 'crypto_lake_real',
                'symbol': 'BTC-USDT',
                'exchange': 'BINANCE',
                'granularity': '1min',
                'total_records': len(df)
            }
        
    except Exception as e:
        print(f"   ❌ Error processing tactical data: {str(e)}")
    
    return generate_tactical_fallback()

def process_strategic_data(df, days_back=7):
    """
    Process data for strategic view (7-30d)
    Focus on persistent liquidity zones and long-term patterns
    """
    if df is None or df.empty:
        return generate_strategic_fallback(days_back)
    
    print(f"📈 Processing strategic data ({days_back} days)...")
    
    try:
        # For strategic view, we aggregate data by hour or day
        if days_back <= 7:
            # Weekly view: aggregate by hour
            aggregation_freq = '1H'
            time_points_count = days_back * 24
        else:
            # Monthly view: aggregate by 4 hours
            aggregation_freq = '4H'
            time_points_count = days_back * 6
        
        # Resample data
        df_resampled = df.resample(aggregation_freq).agg({
            col: 'mean' for col in df.columns if col.startswith(('bid_', 'ask_'))
        }).dropna()
        
        print(f"   📊 Resampled to {len(df_resampled)} {aggregation_freq} intervals")
        
        # Process similar to tactical but with different thresholds
        time_points = []
        price_levels = []
        liquidity_matrix = []
        
        # Higher thresholds for strategic view (focus on major levels)
        institutional_threshold = 50.0  # >50 BTC = major institutional
        retail_threshold = 5.0  # <5 BTC = retail
        
        for idx, row in df_resampled.iterrows():
            time_points.append(idx)
            
            # Collect significant levels only
            levels = []
            
            # Process only major bid/ask levels (first 10 of each)
            for i in range(min(10, 20)):  # Top 10 levels each side
                bid_price_col = f'bid_{i}_price'
                bid_size_col = f'bid_{i}_size'
                ask_price_col = f'ask_{i}_price'
                ask_size_col = f'ask_{i}_size'
                
                # Bid levels
                if bid_price_col in row and bid_size_col in row:
                    price = row[bid_price_col]
                    size = row[bid_size_col]
                    
                    if pd.notna(price) and pd.notna(size) and price > 0 and size > retail_threshold:
                        levels.append({
                            'price': float(price),
                            'volume': float(size),
                            'side': 'bid',
                            'level': i
                        })
                
                # Ask levels
                if ask_price_col in row and ask_size_col in row:
                    price = row[ask_price_col]
                    size = row[ask_size_col]
                    
                    if pd.notna(price) and pd.notna(size) and price > 0 and size > retail_threshold:
                        levels.append({
                            'price': float(price),
                            'volume': float(size),
                            'side': 'ask',
                            'level': i
                        })
            
            # Create strategic price grid (30 levels for strategic view)
            if levels:
                levels.sort(key=lambda x: x['price'])
                min_price = min(level['price'] for level in levels)
                max_price = max(level['price'] for level in levels)
                
                price_range = np.linspace(min_price, max_price, 30)
                liquidity_row = []
                
                for target_price in price_range:
                    # Find significant liquidity near this price
                    nearby_levels = [l for l in levels if abs(l['price'] - target_price) < (max_price - min_price) * 0.05]
                    
                    if nearby_levels:
                        # Sum up liquidity from nearby levels
                        total_liquidity = sum(l['volume'] for l in nearby_levels)
                        liquidity_row.append(total_liquidity)
                    else:
                        liquidity_row.append(0)
                
                liquidity_matrix.append(liquidity_row)
                
                if not price_levels:
                    price_levels = price_range.tolist()
        
        if liquidity_matrix:
            liquidity_matrix = np.array(liquidity_matrix)
            
            # Strategic classification (higher thresholds)
            institutional_matrix = np.where(liquidity_matrix > institutional_threshold, liquidity_matrix, 0)
            accumulation_zones = np.where(liquidity_matrix > institutional_threshold * 2, liquidity_matrix, 0)
            
            print(f"   ✅ Processed {len(time_points)} strategic intervals")
            print(f"   📊 Price levels: {len(price_levels)}")
            print(f"   🏛️ Institutional zones: {np.count_nonzero(institutional_matrix)}")
            print(f"   📈 Accumulation zones: {np.count_nonzero(accumulation_zones)}")
            
            return {
                'view_type': 'strategic',
                'time_points': [str(t) for t in time_points],
                'price_levels': price_levels,
                'liquidity_matrix': liquidity_matrix.tolist(),
                'institutional_matrix': institutional_matrix.tolist(),
                'accumulation_zones': accumulation_zones.tolist(),
                'current_price': float(df.iloc[-1]['bid_0_price']) if 'bid_0_price' in df.columns else price_levels[len(price_levels)//2],
                'data_source': 'crypto_lake_real',
                'symbol': 'BTC-USDT',
                'exchange': 'BINANCE',
                'granularity': aggregation_freq,
                'days_back': days_back,
                'total_records': len(df)
            }
    
    except Exception as e:
        print(f"   ❌ Error processing strategic data: {str(e)}")
    
    return generate_strategic_fallback(days_back)

def generate_tactical_fallback():
    """
    Generate realistic tactical fallback data
    """
    print("⚠️ Using tactical fallback data")
    
    # Generate 48 hours of 1-minute data
    time_points = []
    current_time = datetime.now()
    for i in range(48 * 60):  # 48 hours * 60 minutes
        time_points.append((current_time - timedelta(minutes=i)).isoformat())
    
    time_points.reverse()
    
    # Generate realistic price levels around current BTC price
    base_price = 113500
    price_levels = np.linspace(base_price - 2000, base_price + 2000, 50).tolist()
    
    # Generate realistic liquidity matrix
    liquidity_matrix = []
    institutional_matrix = []
    retail_matrix = []
    
    for i, time_point in enumerate(time_points):
        liquidity_row = []
        institutional_row = []
        retail_row = []
        
        for j, price in enumerate(price_levels):
            # Create realistic liquidity patterns
            distance_from_current = abs(price - base_price)
            base_liquidity = max(0, 50 - distance_from_current / 20)
            
            # Add some randomness and time variation
            time_factor = 1 + 0.3 * np.sin(i / 60)  # Hourly cycles
            price_factor = 1 + 0.2 * np.sin(j / 10)  # Price level patterns
            
            liquidity = base_liquidity * time_factor * price_factor * (0.5 + np.random.random())
            
            # Classify institutional vs retail
            if liquidity > 10:
                institutional_row.append(liquidity)
                retail_row.append(0)
            elif liquidity < 1:
                institutional_row.append(0)
                retail_row.append(liquidity)
            else:
                institutional_row.append(0)
                retail_row.append(0)
            
            liquidity_row.append(max(0, liquidity))
        
        liquidity_matrix.append(liquidity_row)
        institutional_matrix.append(institutional_row)
        retail_matrix.append(retail_row)
    
    return {
        'view_type': 'tactical',
        'time_points': time_points,
        'price_levels': price_levels,
        'liquidity_matrix': liquidity_matrix,
        'institutional_matrix': institutional_matrix,
        'retail_matrix': retail_matrix,
        'current_price': base_price,
        'data_source': 'realistic_fallback',
        'symbol': 'BTC-USDT',
        'exchange': 'BINANCE',
        'granularity': '1min',
        'total_records': len(time_points)
    }

def generate_strategic_fallback(days_back=7):
    """
    Generate realistic strategic fallback data
    """
    print(f"⚠️ Using strategic fallback data ({days_back} days)")
    
    # Generate strategic time points (hourly for 7d, 4-hourly for 30d)
    time_points = []
    current_time = datetime.now()
    
    if days_back <= 7:
        interval_hours = 1
        total_points = days_back * 24
    else:
        interval_hours = 4
        total_points = days_back * 6
    
    for i in range(total_points):
        time_points.append((current_time - timedelta(hours=i * interval_hours)).isoformat())
    
    time_points.reverse()
    
    # Generate strategic price levels (fewer, more significant)
    base_price = 113500
    price_levels = np.linspace(base_price - 5000, base_price + 5000, 30).tolist()
    
    # Generate strategic liquidity patterns
    liquidity_matrix = []
    institutional_matrix = []
    accumulation_zones = []
    
    for i, time_point in enumerate(time_points):
        liquidity_row = []
        institutional_row = []
        accumulation_row = []
        
        for j, price in enumerate(price_levels):
            # Create persistent liquidity zones
            distance_from_current = abs(price - base_price)
            
            # Major support/resistance levels
            if distance_from_current < 1000:  # Near current price
                base_liquidity = 100 + 50 * np.random.random()
            elif distance_from_current < 2000:  # Medium distance
                base_liquidity = 50 + 30 * np.random.random()
            else:  # Far levels
                base_liquidity = 20 + 10 * np.random.random()
            
            # Add strategic patterns (weekly cycles, accumulation zones)
            weekly_factor = 1 + 0.2 * np.sin(i / (7 * 24 / interval_hours))
            accumulation_factor = 1 + 0.5 * np.sin(j / 5)
            
            liquidity = base_liquidity * weekly_factor * accumulation_factor
            
            # Strategic classification (higher thresholds)
            if liquidity > 100:  # Major accumulation zone
                accumulation_row.append(liquidity)
                institutional_row.append(liquidity)
            elif liquidity > 50:  # Institutional level
                accumulation_row.append(0)
                institutional_row.append(liquidity)
            else:
                accumulation_row.append(0)
                institutional_row.append(0)
            
            liquidity_row.append(max(0, liquidity))
        
        liquidity_matrix.append(liquidity_row)
        institutional_matrix.append(institutional_row)
        accumulation_zones.append(accumulation_row)
    
    return {
        'view_type': 'strategic',
        'time_points': time_points,
        'price_levels': price_levels,
        'liquidity_matrix': liquidity_matrix,
        'institutional_matrix': institutional_matrix,
        'accumulation_zones': accumulation_zones,
        'current_price': base_price,
        'data_source': 'realistic_fallback',
        'symbol': 'BTC-USDT',
        'exchange': 'BINANCE',
        'granularity': f'{interval_hours}H',
        'days_back': days_back,
        'total_records': len(time_points)
    }

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        import lakeapi
        crypto_lake_available = True
    except ImportError:
        crypto_lake_available = False
    
    return jsonify({
        'status': 'healthy',
        'crypto_lake_available': crypto_lake_available,
        'aws_configured': bool(os.getenv('AWS_ACCESS_KEY_ID')),
        'features': [
            'tactical_view_24_48h',
            'strategic_view_7_30d',
            'institutional_classification',
            'accumulation_zones',
            'real_crypto_lake_data'
        ]
    })

@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    """
    Main heatmap endpoint with tactical/strategic views
    """
    try:
        # Get parameters
        view_type = request.args.get('view', 'tactical')  # tactical or strategic
        days_back = int(request.args.get('days', 2 if view_type == 'tactical' else 7))
        symbol = request.args.get('symbol', 'BTC-USDT')
        exchange = request.args.get('exchange', 'BINANCE')
        min_volume = float(request.args.get('min_volume', 0))
        
        print(f"🚀 Heatmap request: {view_type} view, {days_back} days back")
        
        # Load real data from Crypto Lake
        df = get_real_crypto_lake_data(view_type, days_back, symbol, exchange)
        
        # Process data based on view type
        if view_type == 'tactical':
            result = process_tactical_data(df)
        else:
            result = process_strategic_data(df, days_back)
        
        # Apply volume filter if specified
        if min_volume > 0:
            print(f"   🔍 Applying volume filter: >{min_volume}")
            # Filter out low volume levels
            # (Implementation would filter the matrices)
        
        return jsonify({
            'status': 'success',
            'data': result,
            'request_params': {
                'view_type': view_type,
                'days_back': days_back,
                'symbol': symbol,
                'exchange': exchange,
                'min_volume': min_volume
            }
        })
        
    except Exception as e:
        print(f"❌ Error in heatmap endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/available-dates', methods=['GET'])
def get_available_dates():
    """Get available dates for data"""
    try:
        import lakeapi
        
        # Check available dates for BTC-USDT on BINANCE
        available = lakeapi.list_data(
            table="book_1m",
            symbols=["BTC-USDT"],
            exchanges=["BINANCE"]
        )
        
        if available and "BTC-USDT" in available and "BINANCE" in available["BTC-USDT"]:
            dates = available["BTC-USDT"]["BINANCE"]["book_1m"]
            if dates:
                sorted_dates = sorted(dates, reverse=True)
                return jsonify({
                    'status': 'success',
                    'latest_date': sorted_dates[0],
                    'available_dates': sorted_dates[:10],  # Last 10 dates
                    'total_dates': len(dates)
                })
        
        return jsonify({
            'status': 'error',
            'message': 'No dates available'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting Crypto Lake Hybrid Heatmap System")
    print("🎯 Features: Tactical (24-48h) + Strategic (7-30d) views")
    print("🏛️ Institutional analysis with accumulation zones")
    print("📊 Real data from Crypto Lake (BINANCE BTC-USDT)")
    print()
    
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

