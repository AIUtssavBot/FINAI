from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import ChatSession, ChatMessage, db
import os
import uuid
import requests
import json
from PyPDF2 import PdfReader
import io
import groq

chatbot_bp = Blueprint('chatbot', __name__)

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

def get_system_prompt():
    return """You are FinAI, an advanced financial AI assistant specialized in providing investment advice, market analysis, and financial education. 
    
Key capabilities:
1. Stock Market Analysis: You can analyze market trends, explain stock movements, and provide context about financial events.
2. Financial Concepts: You explain complex financial concepts in simple terms, including investment strategies, market mechanics, and financial ratios.
3. Investment Guidance: You provide general investment principles, asset allocation strategies, and portfolio diversification advice.
4. Economic Context: You understand macroeconomic factors like interest rates, inflation, fiscal policies, and their impact on markets.
5. Risk Management: You educate users about investment risks and risk management strategies.

Important guidelines:
- Always clarify that you provide educational information, not personalized financial advice.
- When discussing investments, emphasize the importance of research and possibly consulting a financial advisor.
- Present balanced perspectives on investment opportunities, including potential risks.
- If you don't know something specific or current, acknowledge your limitations.
- Avoid making specific price predictions or guarantees about future returns.
- Be helpful, clear, and educational in your responses.
- Use plain language while accurately representing financial concepts.

The user is seeking financial information and guidance. Provide thoughtful, balanced responses that educate rather than prescribe specific actions."""

def get_basic_response(message):
    """Generate a basic response when Groq API is unavailable"""
    # Common financial questions and pre-determined responses
    faq = {
        "what is a stock": "A stock represents ownership in a company. When you buy a stock, you're purchasing a small piece of that company, which makes you a shareholder.",
        "what is investing": "Investing is allocating money with the expectation of generating income or profit over time. Common investments include stocks, bonds, mutual funds, and real estate.",
        "how do i start investing": "To start investing, first establish an emergency fund, set clear goals, open a brokerage account, learn basic investment concepts, start with diversified investments like index funds, and consider dollar-cost averaging.",
        "what is a bear market": "A bear market is when a market experiences prolonged price declines, typically a drop of 20% or more from recent highs. It's often accompanied by negative investor sentiment and pessimism.",
        "what is a bull market": "A bull market refers to a financial market condition where prices are rising or expected to rise. It's characterized by optimism, investor confidence, and strong economic indicators.",
        "what is diversification": "Diversification is spreading investments across various assets to reduce risk. By not 'putting all your eggs in one basket,' you can potentially minimize losses during market downturns.",
        "what is the s&p 500": "The S&P 500 is a stock market index that tracks the performance of 500 large companies listed on U.S. stock exchanges. It's widely regarded as a gauge of the overall U.S. stock market performance.",
        "what is a dividend": "A dividend is a payment made by a corporation to its shareholders as a distribution of profits. Companies may issue dividends regularly, typically quarterly."
    }
    
    # Check if the message matches any FAQ
    message_lower = message.lower()
    for keyword, response in faq.items():
        if keyword in message_lower:
            return response
    
    # Default response if no match
    return "I'm currently operating in offline mode with limited capabilities. When online, I can provide detailed financial analysis and personalized responses to your questions. For now, I can answer basic financial questions - try asking about stocks, investing basics, or market terminology."

class GroqClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, user_message, context=None):
        messages = []
        
        # Add system message
        messages.append({
            "role": "system", 
            "content": "You are FinAI, a financial assistant specializing in stock market analysis, investment strategies, and financial education. Provide helpful, accurate, and concise responses."
        })
        
        # Add context if available
        if context:
            messages.append({
                "role": "system",
                "content": f"Here is some context that might be helpful: {context}"
            })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            payload = {
                "model": "llama3-8b-8192",  # Using Llama 3 8B model
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data["choices"][0]["message"]["content"]
            else:
                # Fallback response if API call fails
                return f"I apologize, but I'm having trouble connecting to my knowledge base right now. Error: {response.status_code}"
        
        except Exception as e:
            return f"I apologize for the inconvenience. There was an error processing your request: {str(e)}"

# Initialize the real Groq client if API key exists, otherwise use mock client
if GROQ_API_KEY:
    groq_client = GroqClient(GROQ_API_KEY)
else:
    # Mock client for when API key is not available
    class MockGroqClient:
        def generate_response(self, user_message, context=None):
            return f"This is a mock response to: '{user_message}'. Please set the GROQ_API_KEY environment variable for real responses."
    
    groq_client = MockGroqClient()

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(io.BytesIO(pdf_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

@chatbot_bp.route('/session', methods=['POST'])
@jwt_required()
def create_session():
    current_user_id = get_jwt_identity()
    
    session = ChatSession(
        user_id=current_user_id,
        session_id=str(uuid.uuid4())
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'session_id': session.session_id
    }), 201

@chatbot_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400
    
    try:
        text_content = extract_text_from_pdf(file)
        
        # Store the extracted text in the session for context
        session_id = request.form.get('session_id')
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
            
        system_message = ChatMessage(
            session_id=session_id,
            message=text_content,
            is_user=False
        )
        db.session.add(system_message)
        db.session.commit()
        
        return jsonify({
            'message': 'Document uploaded and processed successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    data = request.get_json()
    if not 'message' in data:
        return jsonify({'error': 'Missing message field'}), 400
    
    try:
        # Get session ID or create a new one
        session_id = data.get('session_id')
        if not session_id:
            # Create a new session
            current_user_id = get_jwt_identity()
            session = ChatSession(
                user_id=current_user_id,
                session_id=str(uuid.uuid4())
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.session_id
        
        # Store user message
        user_message = ChatMessage(
            session_id=session_id,
            message=data['message'],
            is_user=True
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Get context from previous messages if available
        context = None
        previous_messages = ChatMessage.query.filter_by(
            session_id=session_id,
            is_user=False
        ).order_by(ChatMessage.timestamp.desc()).first()
        
        if previous_messages and len(previous_messages.message) > 1000:
            context = previous_messages.message[:1000] + "..."
        
        # Get response from Groq
        assistant_response = groq_client.generate_response(data['message'], context)
        
        # Store assistant response
        assistant_message = ChatMessage(
            session_id=session_id,
            message=assistant_response,
            is_user=False
        )
        db.session.add(assistant_message)
        db.session.commit()
        
        return jsonify({
            'response': assistant_response,
            'session_id': session_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/history/<session_id>', methods=['GET'])
@jwt_required()
def get_chat_history(session_id):
    messages = ChatMessage.query.filter_by(
        session_id=session_id
    ).order_by(ChatMessage.timestamp).all()
    
    history = []
    for message in messages:
        # Skip very long messages (likely document uploads)
        if len(message.message) > 1000 and not message.is_user:
            continue
            
        history.append({
            'message': message.message,
            'is_user': message.is_user,
            'timestamp': message.timestamp.isoformat()
        })
    
    return jsonify(history), 200

@chatbot_bp.route('/message', methods=['POST'])
@jwt_required()
def send_message():
    """Send message to chatbot and get response"""
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Get Groq API key
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            current_app.logger.warning("Groq API key not found. Using fallback response.")
            response = get_basic_response(message)
            return jsonify({'response': response}), 200
        
        # Initialize Groq client
        client = groq.Client(api_key=api_key)
        
        # Get user identity for context
        user_id = get_jwt_identity()
        
        # Get user's message history (simplified version - would be expanded with database integration)
        # In a real implementation, you would retrieve previous messages from a database
        message_history = []
        
        # Prepare chat completion request
        system_prompt = get_system_prompt()
        
        # Create messages array with system prompt and user message
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add message history if available
        for msg in message_history:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": message})
        
        # Make request to Groq API
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",  # Using Llama 3 70B model
            temperature=0.7,
            max_tokens=800,
            top_p=0.9,
            stream=False
        )
        
        # Extract response
        response = chat_completion.choices[0].message.content
        
        # Store the message and response for future context
        # This would be implemented with a database in a real application
        
        return jsonify({'response': response}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in chatbot: {str(e)}")
        # Provide a fallback response
        fallback_response = get_basic_response(message)
        return jsonify({'response': fallback_response}), 200 