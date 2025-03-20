from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import requests
import groq
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
import json
import random

analysis_bp = Blueprint('analysis', __name__)

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Mock Groq client for development
class MockGroqClient:
    def generate_analysis(self, symbol, prompt):
        return f"""
# Analysis for {symbol}

## Summary
This is a mock analysis for {symbol}. The Groq API integration is temporarily disabled for development.

## Technical Analysis
- The stock is showing a generally positive trend
- RSI indicates the stock is currently at a neutral level
- MACD suggests a potential bullish crossover may be forming

## News Impact
Recent news appears to be moderately positive for the company, with no major negative headlines.

## Recommendation
**HOLD**

Based on the current technical indicators and recent news, maintaining current positions is advised. 
The stock shows relative stability with potential for modest growth in the near term.

## Risks and Opportunities
Risks:
- General market volatility
- Sector-specific challenges

Opportunities:
- Potential product announcements
- Expanding market share
"""

# Use mock client
groq_client = MockGroqClient()

def get_stock_data(symbol):
    # Get historical data
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    data = response.json()
    
    if 'Time Series (Daily)' not in data:
        raise Exception('Unable to fetch stock data')
    
    # Convert to DataFrame
    df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.astype(float)
    df = df.rename(columns={
        '1. open': 'open',
        '2. high': 'high',
        '3. low': 'low',
        '4. close': 'close',
        '5. volume': 'volume'
    })
    
    return df

def get_company_news(symbol):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    url = f'https://finnhub.io/api/v1/company-news'
    params = {
        'symbol': symbol,
        'from': start_date.strftime('%Y-%m-%d'),
        'to': end_date.strftime('%Y-%m-%d'),
        'token': FINNHUB_API_KEY
    }
    
    response = requests.get(url, params=params)
    news_items = response.json()
    
    if not isinstance(news_items, list):
        raise Exception('Unable to fetch company news')
    
    return news_items

def calculate_technical_indicators(df):
    # Moving averages
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    
    # Relative Strength Index (RSI)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # Bollinger Bands
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_upper'] = df['BB_middle'] + 2 * df['close'].rolling(window=20).std()
    df['BB_lower'] = df['BB_middle'] - 2 * df['close'].rolling(window=20).std()
    
    return df

def get_analysis_system_prompt(symbol, data=None):
    prompt = f"""You are FinAI's stock analysis expert. Analyze the stock {symbol} based on available data.
    
    Provide a comprehensive analysis including:
    1. Overview of the company and its business model
    2. Recent performance and key metrics
    3. Technical analysis (if applicable)
    4. Fundamental analysis (if applicable)
    5. Industry context and competitive positioning
    6. Potential risks and opportunities
    7. General outlook (bullish, neutral, or bearish)
    
    Important guidelines:
    - Make it clear you are providing educational analysis, not financial advice
    - Present a balanced view that covers both bullish and bearish perspectives
    - Do not make specific price predictions or guarantees
    - Acknowledge limitations in your analysis based on available data
    - Focus on facts and objective analysis
    - Use standard financial terminology and explain complex concepts
    
    """
    
    if data:
        prompt += f"Here is the available data for {symbol}: {json.dumps(data)}\n\n"
    
    prompt += "Provide your analysis in a clear, structured format that would be helpful for an investor wanting to understand this stock better."
    
    return prompt

def generate_mock_analysis(symbol):
    """Generate mock stock analysis when Groq API is unavailable"""
    # Define company data for popular stocks
    company_data = {
        'AAPL': {
            'name': 'Apple Inc.',
            'sector': 'Technology',
            'business': 'Consumer electronics, software, and services',
            'products': 'iPhone, iPad, Mac, Apple Watch, Services (App Store, Apple Music, iCloud)'
        },
        'MSFT': {
            'name': 'Microsoft Corporation',
            'sector': 'Technology',
            'business': 'Software, cloud computing, and hardware',
            'products': 'Windows, Office 365, Azure, Surface devices, Xbox'
        },
        'GOOGL': {
            'name': 'Alphabet Inc.',
            'sector': 'Technology',
            'business': 'Internet services and products',
            'products': 'Google Search, YouTube, Android, Google Cloud, Advertising'
        },
        'AMZN': {
            'name': 'Amazon.com Inc.',
            'sector': 'Consumer Cyclical',
            'business': 'E-commerce, cloud computing, and digital streaming',
            'products': 'Online marketplace, AWS, Prime Video, Alexa, Kindle'
        },
        'META': {
            'name': 'Meta Platforms Inc.',
            'sector': 'Technology',
            'business': 'Social media and virtual reality',
            'products': 'Facebook, Instagram, WhatsApp, Oculus VR'
        },
        'TSLA': {
            'name': 'Tesla Inc.',
            'sector': 'Automotive',
            'business': 'Electric vehicles and clean energy',
            'products': 'Model S, Model 3, Model X, Model Y, Powerwall, Solar Roof'
        },
        'NVDA': {
            'name': 'NVIDIA Corporation',
            'sector': 'Technology',
            'business': 'Graphics processing units and artificial intelligence',
            'products': 'GPUs, Gaming, Data Center, Professional Visualization, Automotive'
        }
    }
    
    # Generate random sentiment (biased towards neutral)
    sentiment_options = ['Bullish', 'Somewhat Bullish', 'Neutral', 'Somewhat Bearish', 'Bearish']
    sentiment_weights = [0.2, 0.3, 0.3, 0.1, 0.1]  # Weighted probability
    sentiment = random.choices(sentiment_options, weights=sentiment_weights, k=1)[0]
    
    # Define template sections
    if symbol in company_data:
        company = company_data[symbol]
        company_name = company['name']
        sector = company['sector']
        business = company['business']
        products = company['products']
    else:
        company_name = f"{symbol} Inc."
        sector = random.choice(['Technology', 'Healthcare', 'Financial Services', 'Consumer Goods', 'Industrial'])
        business = f"Business operations in the {sector} sector"
        products = "Various products and services in their industry"
    
    # Create analysis sections
    overview = f"# {company_name} ({symbol}) Analysis\n\n"
    overview += f"{company_name} operates in the {sector} sector, focusing on {business}. "
    overview += f"Their main products/services include {products}."
    
    performance = "\n\n## Recent Performance\n\n"
    performance += "Based on available data, " + random.choice([
        f"{symbol} has shown strong performance in recent quarters, with revenue growth exceeding market expectations.",
        f"{symbol} has been performing in line with sector averages, with stable revenue and earnings.",
        f"{symbol} has faced some challenges recently, though there are signs of potential stabilization.",
        f"{symbol} has demonstrated mixed results, with strength in some areas offset by weaknesses in others."
    ])
    
    technical = "\n\n## Technical Analysis\n\n"
    technical += random.choice([
        f"The stock is trading above its 50-day and 200-day moving averages, suggesting positive momentum.",
        f"The stock is currently trading near its support level, which could present a potential entry point if it holds.",
        f"Recent price action shows consolidation after a period of volatility, suggesting indecision in the market.",
        f"The relative strength index (RSI) indicates {symbol} may be approaching overbought/oversold territory."
    ])
    
    fundamental = "\n\n## Fundamental Analysis\n\n"
    fundamental += random.choice([
        f"The company maintains a strong balance sheet with substantial cash reserves and manageable debt levels.",
        f"Valuation metrics suggest {symbol} is trading at a premium/discount compared to industry peers.",
        f"Recent earnings reports show improving profit margins and operational efficiency.",
        f"The company's price-to-earnings ratio is in line with historical averages, suggesting fair valuation."
    ])
    
    industry = "\n\n## Industry Context\n\n"
    industry += random.choice([
        f"{company_name} holds a dominant position in their market segment, with strong competitive advantages.",
        f"The company faces intense competition but maintains differentiation through innovation and quality.",
        f"Industry trends appear favorable for {company_name}'s long-term growth strategy.",
        f"Regulatory and market changes present both challenges and opportunities for {company_name}."
    ])
    
    risks = "\n\n## Risks and Opportunities\n\n"
    risks += "**Risks:**\n"
    risks += "- " + random.choice(["Increasing competition in core markets", "Potential regulatory challenges", 
                               "Macroeconomic uncertainties affecting consumer spending", 
                               "Supply chain disruptions affecting production capacity"]) + "\n"
    risks += "- " + random.choice(["Margin pressure due to rising costs", "Technology shifts requiring significant R&D investment",
                               "Dependence on specific markets or products", "Currency fluctuations affecting international operations"]) + "\n\n"
    
    risks += "**Opportunities:**\n"
    risks += "- " + random.choice(["Expansion into new geographic markets", "Product diversification potential",
                               "Strategic acquisitions to enhance capabilities", "Growing demand in emerging market segments"]) + "\n"
    risks += "- " + random.choice(["Innovation pipeline showing promise", "Cost optimization initiatives underway",
                               "Strong brand value providing pricing power", "Digital transformation creating new revenue streams"])
    
    outlook = f"\n\n## Overall Outlook: {sentiment}\n\n"
    outlook += random.choice([
        f"The overall outlook for {symbol} appears positive, with growth potential outweighing identified risks.",
        f"The outlook for {symbol} is cautiously optimistic, with several positive catalysts balanced by notable challenges.",
        f"The outlook for {symbol} suggests a neutral position is warranted, with both positive and negative factors at play.",
        f"There are concerns about {symbol}'s near-term prospects, though long-term fundamentals remain intact."
    ])
    
    disclaimer = "\n\n## Disclaimer\n\n"
    disclaimer += "This analysis is generated automatically and is for educational purposes only. It does not constitute financial advice. "
    disclaimer += "Always conduct your own research or consult a financial advisor before making investment decisions."
    
    # Combine all sections
    full_analysis = overview + performance + technical + fundamental + industry + risks + outlook + disclaimer
    
    return {
        'symbol': symbol,
        'analysis': full_analysis,
        'sentiment': sentiment,
        'generated_at': datetime.now().isoformat(),
        'source': 'Mock Analysis Engine'
    }

@analysis_bp.route('/stock/<symbol>', methods=['GET'])
@jwt_required()
def analyze_stock(symbol):
    """Get AI analysis for a specific stock"""
    if not symbol:
        return jsonify({'error': 'No symbol provided'}), 400
    
    symbol = symbol.upper()
    
    try:
        # First, try to get stock data from Alpha Vantage
        stock_data = None
        api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        
        if api_key:
            # Get overview data
            overview_url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}'
            overview_response = requests.get(overview_url)
            overview_data = overview_response.json()
            
            # Get global quote
            quote_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}'
            quote_response = requests.get(quote_url)
            quote_data = quote_response.json()
            
            # Combine data if valid
            if 'Symbol' in overview_data and 'Global Quote' in quote_data:
                stock_data = {
                    'overview': overview_data,
                    'quote': quote_data['Global Quote']
                }
        
        # Get Groq API key
        groq_api_key = os.environ.get('GROQ_API_KEY')
        
        # If Groq API key is not available or invalid, use mock analysis
        if not groq_api_key or groq_api_key.startswith('placeholder'):
            current_app.logger.warning("Groq API key not found or invalid. Using mock analysis.")
            mock_result = generate_mock_analysis(symbol)
            return jsonify(mock_result), 200
        
        # Initialize Groq client
        client = groq.Client(api_key=groq_api_key)
        
        # Get user identity for context
        user_id = get_jwt_identity()
        
        # Prepare chat completion request
        system_prompt = get_analysis_system_prompt(symbol, stock_data)
        
        # Create messages array with system prompt
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please provide a comprehensive analysis of {symbol} stock."}
        ]
        
        # Make request to Groq API
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama3-70b-8192",  # Using Llama 3 70B model
                temperature=0.7,
                max_tokens=2000,
                top_p=0.9,
                stream=False
            )
            
            # Extract response
            analysis_text = chat_completion.choices[0].message.content
            
            # Determine sentiment from analysis (very basic approach)
            sentiment = "Neutral"  # Default
            if "bullish" in analysis_text.lower():
                sentiment = "Bullish"
            elif "bearish" in analysis_text.lower():
                sentiment = "Bearish"
            
            result = {
                'symbol': symbol,
                'analysis': analysis_text,
                'sentiment': sentiment,
                'generated_at': datetime.now().isoformat(),
                'source': 'Groq LLM Analysis'
            }
            
            return jsonify(result), 200
            
        except Exception as e:
            current_app.logger.error(f"Error from Groq API: {str(e)}")
            # Fall back to mock analysis
            mock_result = generate_mock_analysis(symbol)
            return jsonify(mock_result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in stock analysis: {str(e)}")
        # Return mock analysis as fallback
        mock_result = generate_mock_analysis(symbol)
        return jsonify(mock_result), 200 