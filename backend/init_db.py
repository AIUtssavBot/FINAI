from app import create_app, db
from app.models import User, StockHolding, Transaction, ChatSession, ChatMessage

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Create a test user if it doesn't exist
        if not User.query.filter_by(username='test').first():
            test_user = User(
                username='test',
                email='test@example.com'
            )
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()  # Commit to get the user ID
            
            # Add some sample stocks for the test user
            stocks = [
                {'symbol': 'AAPL', 'quantity': 10, 'price': 175.50},
                {'symbol': 'MSFT', 'quantity': 5, 'price': 380.25},
                {'symbol': 'GOOGL', 'quantity': 3, 'price': 142.90}
            ]
            
            for stock in stocks:
                # Create a transaction
                transaction = Transaction(
                    user_id=test_user.id,
                    symbol=stock['symbol'],
                    transaction_type='BUY',
                    quantity=stock['quantity'],
                    price=stock['price']
                )
                db.session.add(transaction)
                
                # Create a holding
                holding = StockHolding(
                    user_id=test_user.id,
                    symbol=stock['symbol'],
                    quantity=stock['quantity'],
                    average_price=stock['price']
                )
                db.session.add(holding)
            
            db.session.commit()
            print("Database initialized with test data")
        else:
            print("Database already initialized")

if __name__ == '__main__':
    init_db() 