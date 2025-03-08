#!/usr/bin/env python3
import os
import sys
from flask import Flask, session, request, jsonify
from flask_login import LoginManager
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from models import db, User
from routes import main, auth, patient, doctor, admin
from admin_routes import admin_panel
from config import get_config
import datetime
import uuid
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mfa import send_verification_code

# Initialize extensions
login_manager = LoginManager()
mail = Mail()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(get_config())
    
    # Use a unique session cookie name to avoid conflicts
    app.config['SESSION_COOKIE_NAME'] = f'session_{uuid.uuid4().hex[:8]}'
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    mail.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(patient, url_prefix='/patient')
    app.register_blueprint(doctor, url_prefix='/doctor')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(admin_panel)
    
    # Add context processor to make 'now' available in all templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}
    
    # Register custom template filters
    @app.template_filter('time_ago')
    def time_ago_filter(timestamp):
        """Format timestamp as time ago text"""
        now = datetime.datetime.now()
        diff = now - timestamp
        
        if diff.days > 365:
            return f"{diff.days // 365} year{'s' if diff.days // 365 != 1 else ''} ago"
        elif diff.days > 30:
            return f"{diff.days // 30} month{'s' if diff.days // 30 != 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 != 1 else ''} ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 != 1 else ''} ago"
        else:
            return "Just now"
    
    @app.route('/login', methods=['POST'])
    @limiter.limit('5 per minute')  # Limit to 5 login attempts per minute
    def login():
        # Existing login logic
        # After successful login, send verification code
        phone_number = request.form.get('phone_number')
        verification_code = generate_verification_code()
        send_verification_code(phone_number, verification_code)
        # Save the verification code in session or database for later verification
        return jsonify({'message': 'Verification code sent!'}), 200
    
    return app

def init_db():
    """Initialize the database with tables."""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database tables created.")

if __name__ == '__main__':
    app = create_app()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'init_db':
            with app.app_context():
                init_db()
                print("Database initialized successfully.")
            sys.exit(0)
    
    # Run the app
    app.run(host='0.0.0.0', port=9998, debug=True)
