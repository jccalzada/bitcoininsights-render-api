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
            "/api/hodl-waves",
            "/api/macro-correlations",
            "/api/asset-performance",
            "/api/asset-performance-historical-real"
        ]
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
                
                current_response = requests.get(current_url, params=current_params, timeout=10)
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
                
                historical_response = requests.get(historical_url, params=historical_params, timeout=10)
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

# [RESTO DE ENDPOINTS AQUÍ - TRUNCADO POR ESPACIO]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)

