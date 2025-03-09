import os
import secrets
from PIL import Image
from flask import current_app
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import jwt
import logging
import random
import string
import bcrypt
import json
from flask import current_app
import hashlib

from models import Notification, db

# Use self-documenting f-string format (Python 3.12+)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def generate_verification_token(user_id, expires_in=3600):
    """
    Generate a JWT token for email verification
    
    Args:
        user_id: User ID to encode in the token
        expires_in: Token expiration time in seconds (default: 1 hour)
        
    Returns:
        Encoded JWT token
    """
    now = datetime.utcnow()
    payload = {
        'user_id': user_id,
        'exp': now + timedelta(seconds=expires_in),
        'iat': now
    }
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def send_verification_email(email, token):
    """
    Send verification email with token
    
    Args:
        email: Recipient email address
        token: Verification token
    """
    try:
        # Log with self-documenting f-strings
        logger.info(f"{email=} - Sending verification email")
        
        verification_url = f"{current_app.config['BASE_URL']}/auth/verify-email/{token}"
        
        # Email message setup
        msg = MIMEMultipart()
        msg['From'] = current_app.config['MAIL_USERNAME']
        msg['To'] = email
        msg['Subject'] = "Verify Your Email Address"
        
        body = f"""
        Hello,
        
        Thank you for registering! Please verify your email address by clicking the link below:
        
        {verification_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this verification, please ignore this email.
        
        Best regards,
        Health Appointment Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server and send
        server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        server.starttls()
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"{email=} - Verification email sent successfully")
        return True
    except Exception as e:
        # Log errors with self-documenting f-strings
        logger.error(f"{email=} - Failed to send verification email: {e=}")
        return False

def send_verification_sms(phone, code):
    """
    Send verification SMS with code (placeholder for actual SMS integration)
    
    Args:
        phone: Recipient phone number
        code: Verification code
    """
    # This is a placeholder. In a real app, you would integrate with an SMS service
    logger.info(f"{phone=} - SMS verification code: {code=}")
    return True

def save_verification_document(file, user_id):
    """
    Save a verification document uploaded by a doctor
    
    Args:
        file: The uploaded file from the form
        user_id: The ID of the user uploading the document
        
    Returns:
        The relative path to the saved document
    """
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, 'static/uploads', f'doctor_{user_id}')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate a unique filename
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(8)}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save the file
    file.save(file_path)
    
    # Return the relative path to be stored in the database
    return os.path.join(f'uploads/doctor_{user_id}', unique_filename)

def save_profile_picture(form_picture, user_id):
    """
    Save a profile picture uploaded by a doctor
    
    Args:
        form_picture: The uploaded file from the form
        user_id: The ID of the user uploading the picture
        
    Returns:
        The relative path to the saved picture
    """
    # Create profile pics directory if not exists
    profile_dir = os.path.join(current_app.root_path, 'static/profile_pics')
    os.makedirs(profile_dir, exist_ok=True)
    
    # Generate random filename
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = f"{user_id}_{random_hex}{f_ext}"
    picture_path = os.path.join(profile_dir, picture_fn)

    # Resize and save image
    output_size = (250, 250)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return f'profile_pics/{picture_fn}'

def create_notification(user_id, title, message):
    """Create and store a notification with database context"""
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message
        )
        db.session.add(notification)
        db.session.commit()
        logger.info(f"Notification created for user {user_id=}")
        return True
    except Exception as e:
        logger.error(f"Failed to create notification for user {user_id=}: {e=}")
        db.session.rollback()
        return False

def send_password_reset_email(email, token):
    """
    Send password reset email with token
    
    Args:
        email: Recipient email address
        token: Reset token
    """
    try:
        reset_url = f"{current_app.config['BASE_URL']}/auth/reset-password/{token}"
        
        msg = MIMEMultipart()
        msg['From'] = current_app.config['MAIL_USERNAME']
        msg['To'] = email
        msg['Subject'] = "Reset Your Password"
        
        body = f"""
        Hello,
        
        You've requested to reset your password. Please click the link below to reset it:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        Health Appointment Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
        server.starttls()
        server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"{email=} - Password reset email sent successfully")
        return True
    except Exception as e:
        logger.error(f"{email=} - Failed to send password reset email: {e}")
        return False

def generate_password_hash(password):
    """Generate password hash using Flask-Bcrypt"""
    from app import bcrypt
    # Use Flask-Bcrypt to generate the hash
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    logger.info(f"Generated password hash with length: {len(hashed)}")
    return hashed

def parse_pbkdf2_hash(pbkdf2_hash):
    # Handle the format with colons (pbkdf2:sha256:iterations:salt:hash)
    if ':' in pbkdf2_hash:
        try:
            parts = pbkdf2_hash.split(':')
            logger.info(f"Hash parts: {parts} (count: {len(parts)})")
            
            if len(parts) == 5:
                algorithm, hash_name, iterations, salt, hash_value = parts
                iterations = int(iterations)
            elif len(parts) == 4:
                # Handle the case with only 4 components
                algorithm, hash_name, salt, hash_value = parts
                iterations = 1000  # Default iterations if not specified
            elif len(parts) == 3:
                # This appears to be Flask's Werkzeug format: 'pbkdf2:sha256:iterations+salt+hash'
                algorithm, hash_name, combined = parts
                
                # The third part contains iterations+salt+hash
                # Try to extract these components
                import binascii
                try:
                    # The first few characters of the combined part are the iterations
                    iterations_str = ""
                    for char in combined:
                        if char.isdigit():
                            iterations_str += char
                        else:
                            break
                    
                    iterations = int(iterations_str)
                    
                    # The rest is a base64-encoded salt+hash
                    remaining = combined[len(iterations_str):]
                    
                    # For now, we'll use a dummy salt and the whole remaining string as the hash
                    # This is just to allow the verification to proceed
                    salt = "dummy"
                    hash_value = remaining
                    
                    logger.info(f"Parsed Werkzeug format: algo={algorithm}, hash_name={hash_name}, " + 
                                f"iterations={iterations}, salt={salt}, hash_value={hash_value[:10]}...")
                except Exception as e:
                    logger.error(f"Error parsing Werkzeug format: {str(e)}")
                    raise ValueError(f"Error parsing Werkzeug format: {str(e)}")
            else:
                logger.error(f"Invalid colon-format hash parts count: {len(parts)}")
                raise ValueError("Invalid hash format")
                
            return algorithm, hash_name, iterations, salt, hash_value
        except Exception as e:
            logger.error(f"Error parsing colon-format PBKDF2 hash: {str(e)}")
            raise ValueError("Error parsing PBKDF2 hash")
    
    # Handle the format with dollar signs ($pbkdf2-sha256$iterations=100000,salt=abcdef)
    elif pbkdf2_hash.startswith('$pbkdf2-'):
        try:
            parts = pbkdf2_hash.split('$')
            if len(parts) != 4:
                logger.error(f"Invalid dollar-format hash parts count: {len(parts)}")
                raise ValueError("Invalid hash parts count")
                
            algorithm_info = parts[1]  # e.g., "pbkdf2-sha256"
            algorithm, hash_name = algorithm_info.split('-')
            
            params_salt = parts[2]  # e.g., "iterations=100000,salt=abcdef"
            params_parts = params_salt.split(',')
            iterations = int(params_parts[0].split('=')[1])
            salt = params_parts[1].split('=')[1]
            
            hash_value = parts[3]
            
            return algorithm, hash_name, iterations, salt, hash_value
        except Exception as e:
            logger.error(f"Error parsing dollar-format PBKDF2 hash: {str(e)}")
            raise ValueError("Error parsing PBKDF2 hash")
    
    else:
        logger.error(f"Unrecognized hash format: {pbkdf2_hash[:20]}...")
        raise ValueError("Unrecognized hash format")

def hash_pbkdf2(password, salt, iterations, hash_name, hash_length):
    try:
        new_hash_value = hashlib.pbkdf2_hmac(hash_name, password.encode('utf-8'), salt.encode('utf-8'), iterations)
    except ValueError:
        # Try with sha256 as fallback
        new_hash_value = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), iterations)
    return new_hash_value

def verify_pbkdf2(stored_hash, provided_password):
    logger.info(f"Verifying PBKDF2 hash: {stored_hash[:20]}...")
    
    # Check if this is Werkzeug format (pbkdf2:sha256:iterations+salt+hash)
    if stored_hash.count(':') == 2 and stored_hash.startswith('pbkdf2:sha256:'):
        # Use Werkzeug's built-in check_password_hash for this format
        try:
            from werkzeug.security import check_password_hash as werkzeug_check
            result = werkzeug_check(stored_hash, provided_password)
            logger.info(f"Used Werkzeug's check_password_hash: {result}")
            return result
        except Exception as e:
            logger.error(f"Error using Werkzeug's check_password_hash: {str(e)}")
            # Fall back to our implementation
    
    # Original implementation for other formats
    try:
        algorithm, hash_name, iterations, salt, hash_value = parse_pbkdf2_hash(stored_hash)
    except ValueError:
        logger.error("Failed to parse PBKDF2 hash, verification failed")
        return False
    
    # Generate the new hash
    new_hash_value = hash_pbkdf2(provided_password, salt, int(iterations), hash_name, len(hash_value) // 2)
    logger.info(f"Generated hash (first 10 chars): {new_hash_value.hex()[:10]}...")
    
    # Compare the hashes
    result = new_hash_value.hex() == hash_value
    logger.info(f"Hash comparison: {result}")
    
    return result

def check_password_hash(stored_hash, provided_password):
    """Check if provided password matches stored hash using Flask-Bcrypt and PBKDF2"""
    from app import bcrypt
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Log the hash format for debugging
    logger.info(f"Stored hash format: {stored_hash[:20]}... (length: {len(stored_hash)})")
    
    # Handle both string and bytes formats consistently
    if isinstance(stored_hash, bytes):
        stored_hash_str = stored_hash.decode('utf-8')
        logger.info("Converted bytes to string")
    else:
        stored_hash_str = stored_hash
        logger.info("Hash was already string format")
    
    # Check for PBKDF2 format
    if stored_hash_str.startswith('pbkdf2:'):
        logger.info("Using PBKDF2 verification")
        result = verify_pbkdf2(stored_hash_str, provided_password)
        logger.info(f"PBKDF2 verification result: {result}")
        return result
    else:
        logger.info("Using Bcrypt verification")
    
    # Check for Bcrypt format
    try:
        result = bcrypt.check_password_hash(stored_hash_str, provided_password)
        logger.info(f"Bcrypt verification result: {result}")
        return result
    except ValueError as e:
        logger.error(f"Bcrypt verification error: {e}")
        return False
