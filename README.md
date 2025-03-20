# FinAI - Intelligent Financial Analysis Platform

A comprehensive financial analysis platform that combines real-time market data, AI-powered insights, and interactive stock trading capabilities.

## Developer
- **Name:** Utsav Mehta
- **Institution:** AIML, DJ Sanghvi College

## Features
- Real-time stock price tracking and analysis
- AI-powered stock predictions and insights
- Interactive stock trading platform
- Real-time financial news updates
- Intelligent chatbot with RAG capabilities
- Secure user authentication
- Personalized user dashboard

## Tech Stack
- **Backend:** Flask (Python)
- **Frontend:** ReactJS
- **APIs:** 
  - Alpha Vantage/Finnhub for stock data
  - NewsAPI/Finnhub for financial news
  - Groq for LLM capabilities
- **Database:** PostgreSQL

## Setup Instructions

### Backend Setup
1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Run the Flask server:
```bash
python run.py
```

### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

## API Keys Required
- Alpha Vantage/Finnhub API key
- NewsAPI key
- Groq API key

## Contributing
This is a student project developed by Utsav Mehta. For any queries or suggestions, please reach out to the developer.

## License
MIT License 