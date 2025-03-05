#!/usr/bin/env python3
"""
Test script to diagnose login issues with Python 3.13
"""
import sys
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User
import bcrypt
from flask_bcrypt import Bcrypt
from flask import Flask

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a minimal Flask app for testing
app = Flask(__name__)
flask_bcrypt = Bcrypt(app)

# Connect to the database
from config import get_config
config = get_config()
engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

def test_raw_bcrypt(password_hash, password):
    """Test password verification using raw bcrypt"""
    try:
        result = bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
        logger.info(f"Raw bcrypt verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Raw bcrypt verification error: {e}")
        return False

def test_flask_bcrypt(password_hash, password):
    """Test password verification using Flask-Bcrypt"""
    try:
        result = flask_bcrypt.check_password_hash(password_hash, password)
        logger.info(f"Flask-Bcrypt verification result: {result}")
        return result
    except Exception as e:
        logger.error(f"Flask-Bcrypt verification error: {e}")
        return False

def test_custom_verification(password_hash, password):
    """Test a custom verification approach"""
    try:
        # Try to extract the salt from the hash
        parts = password_hash.split('$')
        if len(parts) >= 4:
            salt = '$'.join(parts[:3]) + '$'
            logger.info(f"Extracted salt: {salt}")
            
            # Generate a new hash with the extracted salt
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8'))
            result = hashed.decode('utf-8') == password_hash
            logger.info(f"Custom verification result: {result}")
            return result
        else:
            logger.error("Could not extract salt from hash")
            return False
    except Exception as e:
        logger.error(f"Custom verification error: {e}")
        return False

def generate_new_hash(password):
    """Generate a new hash using Flask-Bcrypt"""
    try:
        hashed = flask_bcrypt.generate_password_hash(password).decode('utf-8')
        logger.info(f"Generated new hash: {hashed}")
        return hashed
    except Exception as e:
        logger.error(f"Hash generation error: {e}")
        return None

def main():
    """Main test function"""
    # Get all users
    users = session.query(User).all()
    logger.info(f"Found {len(users)} users")
    
    # Test with a specific user if provided
    if len(sys.argv) > 1:
        email = sys.argv[1]
        user = session.query(User).filter_by(email=email).first()
        if user:
            logger.info(f"Testing with user: {user.email}, ID: {user.id}")
            
            # Get password from command line or prompt
            if len(sys.argv) > 2:
                password = sys.argv[2]
            else:
                import getpass
                password = getpass.getpass("Enter password: ")
            
            logger.info(f"User hash: {user.password_hash}")
            logger.info(f"Hash length: {len(user.password_hash)}")
            
            # Test different verification methods
            test_raw_bcrypt(user.password_hash, password)
            test_flask_bcrypt(user.password_hash, password)
            test_custom_verification(user.password_hash, password)
            
            # Generate a new hash for comparison
            new_hash = generate_new_hash(password)
            if new_hash:
                logger.info(f"New hash length: {len(new_hash)}")
                
                # Option to update the user's hash
                if len(sys.argv) > 3 and sys.argv[3] == "--update":
                    user.password_hash = new_hash
                    session.commit()
                    logger.info(f"Updated user {user.email} with new password hash")
        else:
            logger.error(f"User not found: {email}")
    else:
        # Test with the first few users
        for user in users[:5]:
            logger.info(f"User: {user.email}, ID: {user.id}")
            logger.info(f"Hash: {user.password_hash}")
            logger.info(f"Hash length: {len(user.password_hash)}")
            logger.info("---")

if __name__ == "__main__":
    main()
