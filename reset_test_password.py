#!/usr/bin/env python3
"""
Reset a user's password for testing with Python 3.13
"""
import sys
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from models import User, db
from utils import generate_password_hash

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a minimal Flask app for testing
app = Flask(__name__)
from config import get_config
app.config.from_object(get_config())

# Initialize extensions
bcrypt = Bcrypt(app)
db.init_app(app)

def reset_password(email, new_password):
    """Reset a user's password"""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            logger.info(f"Resetting password for user: {user.email}, ID: {user.id}")
            
            # Generate a new password hash
            password_hash = generate_password_hash(new_password)
            logger.info(f"New hash: {password_hash}")
            logger.info(f"Hash length: {len(password_hash)}")
            
            # Update the user's password hash
            user.password_hash = password_hash
            db.session.commit()
            
            logger.info(f"Password reset successful for user: {user.email}")
            return True
        else:
            logger.error(f"User not found: {email}")
            return False

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python reset_test_password.py <email> <new_password>")
        return
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    success = reset_password(email, new_password)
    if success:
        print(f"Password reset successful for user: {email}")
        print(f"New password: {new_password}")
    else:
        print(f"Password reset failed for user: {email}")

if __name__ == "__main__":
    main()
