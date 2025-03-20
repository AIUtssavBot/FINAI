from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required
import os
import requests
from datetime import datetime, timedelta
import random

news_bp = Blueprint('news', __name__)

NEWS_API_KEY = os.getenv('NEWS_API_KEY')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')

# Mock news data for fallback when API fails
MOCK_NEWS = [
    {
        'title': 'Markets Rally on Tech Earnings',
        'description': 'Major indices rose after strong quarterly results from tech giants.',
        'url': 'https://example.com/tech-earnings',
        'image_url': 'https://via.placeholder.com/400x200?text=Financial+News',
        'source': 'Financial Times',
        'published_at': (datetime.now() - timedelta(hours=3)).isoformat()
    },
    {
        'title': 'Fed Signals Interest Rate Changes',
        'description': 'Federal Reserve chair hints at potential shift in monetary policy.',
        'url': 'https://example.com/fed-policy',
        'image_url': 'https://via.placeholder.com/400x200?text=Economic+Update',
        'source': 'Wall Street Journal',
        'published_at': (datetime.now() - timedelta(hours=8)).isoformat()
    },
    {
        'title': 'Cryptocurrency Market Update',
        'description': 'Bitcoin and Ethereum prices fluctuate amid regulatory news.',
        'url': 'https://example.com/crypto-news',
        'image_url': 'https://via.placeholder.com/400x200?text=Crypto+Market',
        'source': 'CoinDesk',
        'published_at': (datetime.now() - timedelta(hours=5)).isoformat()
    },
    {
        'title': 'Emerging Markets Show Strong Growth',
        'description': 'Investors look to developing economies as growth opportunity.',
        'url': 'https://example.com/emerging-markets',
        'image_url': 'https://via.placeholder.com/400x200?text=Global+Markets',
        'source': 'Bloomberg',
        'published_at': (datetime.now() - timedelta(hours=12)).isoformat()
    },
    {
        'title': 'Sustainable Investing Trends',
        'description': 'ESG funds continue to attract record inflows as investors prioritize sustainability.',
        'url': 'https://example.com/esg-investing',
        'image_url': 'https://via.placeholder.com/400x200?text=ESG+Investing',
        'source': 'Reuters',
        'published_at': (datetime.now() - timedelta(days=1)).isoformat()
    }
]

# Mock company-specific news
def generate_company_news(symbol):
    company_name = f"{symbol}"
    news_items = [
        {
            'headline': f'{company_name} Reports Quarterly Earnings Above Expectations',
            'summary': f'The company reported strong growth in its core business segments.',
            'url': 'https://example.com/earnings-report',
            'source': 'Business Insider',
            'datetime': (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat()
        },
        {
            'headline': f'{company_name} Announces New Product Line',
            'summary': 'The company is expanding its offerings to capture additional market share.',
            'url': 'https://example.com/product-announcement',
            'source': 'TechCrunch',
            'datetime': (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat()
        },
        {
            'headline': f'Analysts Upgrade {company_name} Stock',
            'summary': 'Several analysts have raised their price targets following recent developments.',
            'url': 'https://example.com/analyst-upgrade',
            'source': 'MarketWatch',
            'datetime': (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat()
        }
    ]
    return news_items

def generate_mock_news(query=None, count=10):
    """Generate mock financial news when API calls fail"""
    now = datetime.now()
    mock_sources = ["Bloomberg", "CNBC", "Reuters", "Wall Street Journal", "Financial Times", 
                   "MarketWatch", "Business Insider", "Yahoo Finance", "Seeking Alpha", "Motley Fool"]
    
    mock_topics = {
        "markets": ["Market rally continues as tech stocks surge", 
                  "Investors optimistic as market reaches new highs",
                  "Markets close mixed after volatile trading session",
                  "Global markets respond to central bank decisions",
                  "Market analysis: What to expect this earnings season"],
                  
        "technology": ["Tech giants announce new AI partnerships",
                     "Semiconductor shortage impacts tech sector", 
                     "Big Tech faces new regulatory challenges",
                     "Cloud computing stocks show strong performance",
                     "Tech innovation drives market growth"],
                     
        "economy": ["Fed signals potential interest rate changes",
                  "Inflation data shows economic pressures",
                  "Job market remains strong despite economic concerns",
                  "Economic indicators point to continued growth",
                  "Treasury yields shift as economic outlook changes"],
                  
        "companies": ["Apple unveils new product lineup",
                    "Amazon expands into healthcare sector",
                    "Tesla production numbers exceed expectations",
                    "Microsoft announces strategic acquisition",
                    "Google faces antitrust investigation"]
    }
    
    # Generate articles related to the query if provided
    articles = []
    categories = list(mock_topics.keys())
    
    # If query is provided, prioritize relevant topics
    relevant_categories = []
    if query:
        query = query.lower()
        # Check if query matches a company name
        company_keywords = {
            "apple": "companies", "microsoft": "companies", "amazon": "companies", 
            "google": "companies", "meta": "companies", "tesla": "companies",
            "market": "markets", "stock": "markets", "tech": "technology", 
            "economy": "economy", "inflation": "economy", "interest": "economy"
        }
        
        for keyword, category in company_keywords.items():
            if keyword in query:
                relevant_categories.append(category)
    
    if not relevant_categories:
        relevant_categories = categories
    
    for i in range(count):
        # Select random category with higher probability for relevant ones
        if random.random() < 0.7 and relevant_categories:
            category = random.choice(relevant_categories)
        else:
            category = random.choice(categories)
            
        # Generate publication time (random within last 24 hours)
        hours_ago = random.randint(0, 24)
        published_at = (now - timedelta(hours=hours_ago)).isoformat()
        
        # Select headline based on category
        headline = random.choice(mock_topics[category])
        
        # Customize headline if query is a stock symbol
        if query and len(query) <= 5 and query.isupper():
            if random.random() < 0.6:  # 60% chance to customize headline
                stock_headlines = [
                    f"{query} shares jump on strong earnings report",
                    f"{query} announces new strategic initiative",
                    f"Analysts upgrade {query} stock to 'buy'",
                    f"{query} faces challenges in quarterly results",
                    f"Investors react to {query}'s latest announcement"
                ]
                headline = random.choice(stock_headlines)
        
        article = {
            "title": headline,
            "url": f"https://example.com/financial-news/{i}",
            "source": random.choice(mock_sources),
            "publishedAt": published_at,
            "category": category,
            "sentiment": random.choice(["positive", "neutral", "negative"]),
            "content": f"This is a mock article about {category} topics. It would contain detailed information about {headline}."
        }
        articles.append(article)
    
    return articles

@news_bp.route('/latest', methods=['GET'])
@jwt_required()
def get_latest_news():
    """Get latest financial news"""
    try:
        # First try NewsAPI
        api_key = os.environ.get('NEWS_API_KEY')
        if api_key:
            url = f'https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={api_key}'
            response = requests.get(url)
            data = response.json()
            
            if data.get('status') == 'ok' and data.get('articles'):
                articles = []
                for article in data['articles'][:10]:  # Get top 10
                    articles.append({
                        'title': article.get('title'),
                        'url': article.get('url'),
                        'source': article.get('source', {}).get('name'),
                        'publishedAt': article.get('publishedAt'),
                        'content': article.get('description')
                    })
                return jsonify(articles), 200
        
        # If NewsAPI fails, try Finnhub
        finnhub_key = os.environ.get('FINNHUB_API_KEY')
        if finnhub_key:
            url = f'https://finnhub.io/api/v1/news?category=general&token={finnhub_key}'
            response = requests.get(url)
            data = response.json()
            
            if data and isinstance(data, list):
                articles = []
                for article in data[:10]:  # Get top 10
                    articles.append({
                        'title': article.get('headline'),
                        'url': article.get('url'),
                        'source': article.get('source'),
                        'publishedAt': article.get('datetime'),
                        'content': article.get('summary')
                    })
                return jsonify(articles), 200
        
        # If both APIs fail, return mock data
        mock_articles = generate_mock_news(count=10)
        return jsonify(mock_articles), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting news: {str(e)}")
        # Fallback to mock data if there's any error
        mock_articles = generate_mock_news(count=10)
        return jsonify(mock_articles), 200

@news_bp.route('/search/<query>', methods=['GET'])
def search_news(query):
    """Search for news by query"""
    try:
        # First try NewsAPI
        api_key = os.environ.get('NEWS_API_KEY')
        if api_key:
            url = f'https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={api_key}'
            response = requests.get(url)
            data = response.json()
            
            if data.get('status') == 'ok' and data.get('articles'):
                articles = []
                for article in data['articles'][:10]:  # Get top 10
                    articles.append({
                        'title': article.get('title'),
                        'url': article.get('url'),
                        'source': article.get('source', {}).get('name'),
                        'publishedAt': article.get('publishedAt'),
                        'content': article.get('description')
                    })
                return jsonify(articles), 200
        
        # If NewsAPI fails, try Finnhub
        finnhub_key = os.environ.get('FINNHUB_API_KEY')
        if finnhub_key:
            url = f'https://finnhub.io/api/v1/news?category=general&token={finnhub_key}'
            response = requests.get(url)
            data = response.json()
            
            if data and isinstance(data, list):
                # Filter to find relevant articles
                relevant_articles = [
                    article for article in data 
                    if query.lower() in article.get('headline', '').lower() or
                       query.lower() in article.get('summary', '').lower()
                ]
                
                articles = []
                for article in relevant_articles[:10]:  # Get top 10
                    articles.append({
                        'title': article.get('headline'),
                        'url': article.get('url'),
                        'source': article.get('source'),
                        'publishedAt': article.get('datetime'),
                        'content': article.get('summary')
                    })
                return jsonify(articles), 200
        
        # If both APIs fail, return mock data
        mock_articles = generate_mock_news(query=query, count=10)
        return jsonify(mock_articles), 200
        
    except Exception as e:
        current_app.logger.error(f"Error searching news: {str(e)}")
        # Fallback to mock data if there's any error
        mock_articles = generate_mock_news(query=query, count=10)
        return jsonify(mock_articles), 200

@news_bp.route('/company/<symbol>', methods=['GET'])
@jwt_required()
def get_company_news(symbol):
    try:
        # Using Finnhub API for company-specific news
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        url = f'https://finnhub.io/api/v1/company-news'
        params = {
            'symbol': symbol.upper(),
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'token': FINNHUB_API_KEY
        }
        
        response = requests.get(url, params=params)
        news_items = response.json()
        
        if not isinstance(news_items, list) or not news_items:
            # Return mock data if API fails
            return jsonify(generate_company_news(symbol)), 200
            
        formatted_news = []
        for item in news_items[:20]:  # Limit to 20 most recent news items
            if not item.get('headline') or not item.get('url'):
                continue
                
            formatted_news.append({
                'headline': item.get('headline'),
                'summary': item.get('summary', 'No summary available'),
                'url': item.get('url'),
                'source': item.get('source', 'Financial News'),
                'datetime': datetime.fromtimestamp(item.get('datetime', int(datetime.now().timestamp()))).isoformat()
            })
        
        # If we got no usable news items, use mock data
        if not formatted_news:
            return jsonify(generate_company_news(symbol)), 200
            
        return jsonify(formatted_news), 200
        
    except Exception as e:
        print(f"Error in company news API: {str(e)}")
        return jsonify(generate_company_news(symbol)), 200 