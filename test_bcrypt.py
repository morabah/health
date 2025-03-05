#!/usr/bin/env python3
"""
Test bcrypt password hashing in Python 3.13
"""
import bcrypt
from flask import Flask
from flask_bcrypt import Bcrypt
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a minimal Flask app for testing
app = Flask(__name__)
flask_bcrypt = Bcrypt(app)

def test_password_hashing():
    """Test password hashing with both bcrypt and Flask-Bcrypt"""
    password = "test123"
    
    # Test with raw bcrypt
    logger.info("Testing with raw bcrypt:")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    logger.info(f"Raw bcrypt hash: {hashed.decode('utf-8')}")
    
    # Verify with raw bcrypt
    is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed)
    logger.info(f"Raw bcrypt verification: {is_valid}")
    
    # Test with Flask-Bcrypt
    logger.info("\nTesting with Flask-Bcrypt:")
    flask_hash = flask_bcrypt.generate_password_hash(password).decode('utf-8')
    logger.info(f"Flask-Bcrypt hash: {flask_hash}")
    
    # Verify with Flask-Bcrypt
    is_valid = flask_bcrypt.check_password_hash(flask_hash, password)
    logger.info(f"Flask-Bcrypt verification: {is_valid}")
    
    # Cross-verification tests
    logger.info("\nCross-verification tests:")
    try:
        # Try to verify Flask-Bcrypt hash with raw bcrypt
        is_valid = bcrypt.checkpw(password.encode('utf-8'), flask_hash.encode('utf-8'))
        logger.info(f"Verifying Flask-Bcrypt hash with raw bcrypt: {is_valid}")
    except Exception as e:
        logger.error(f"Error verifying Flask-Bcrypt hash with raw bcrypt: {e}")
    
    try:
        # Try to verify raw bcrypt hash with Flask-Bcrypt
        is_valid = flask_bcrypt.check_password_hash(hashed.decode('utf-8'), password)
        logger.info(f"Verifying raw bcrypt hash with Flask-Bcrypt: {is_valid}")
    except Exception as e:
        logger.error(f"Error verifying raw bcrypt hash with Flask-Bcrypt: {e}")

if __name__ == "__main__":
    test_password_hashing()
