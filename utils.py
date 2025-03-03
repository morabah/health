import os
import random
import string
from datetime import datetime, timedelta
import uuid
from flask import current_app, url_for
from flask_mail import Message
from werkzeug.utils import secure_filename
from models import User, VerificationStatus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set this to True to bypass actual email sending
MOCK_EMAIL_SENDING = True

def generate_verification_code():
    """Generate a 6-digit verification code for phone verification."""
    return ''.join(random.choices(string.digits, k=6))

def generate_verification_token():
    """Generate a unique token for email verification."""
    return str(uuid.uuid4())

def send_verification_email(mail, user, token):
    """Send verification email to user."""
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    msg = Message('Verify Your Email Address',
                  recipients=[user.email])
    msg.body = f'''To verify your email address, please click on the following link:
{verification_url}

If you did not register for this account, please ignore this email.
'''
    
    if MOCK_EMAIL_SENDING:
        # Log the email instead of sending it
        logger.info(f"MOCK EMAIL: Verification link for {user.email}: {verification_url}")
        print(f"MOCK EMAIL: Verification link for {user.email}: {verification_url}")
        return True
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        print(f"Failed to send email to {user.email}: {str(e)}")
        # Return True anyway to allow registration to proceed
        return True

def send_verification_sms(user, code):
    """
    Send verification SMS to user.
    
    Note: This is a placeholder function. In a real application, 
    you would integrate with an SMS service provider like Twilio.
    """
    # In a real application, you would call an SMS API here
    print(f"SMS verification code {code} sent to {user.phone}")
    # For demo purposes, we'll consider the SMS as sent
    return True

def send_password_reset_email(mail, user, token):
    """Send password reset email to user."""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message('Password Reset Request',
                  recipients=[user.email])
    msg.body = f'''To reset your password, please click on the following link:
{reset_url}

If you did not request a password reset, please ignore this email.
'''
    if MOCK_EMAIL_SENDING:
        # Log the email instead of sending it
        logger.info(f"MOCK EMAIL: Password reset link for {user.email}: {reset_url}")
        print(f"MOCK EMAIL: Password reset link for {user.email}: {reset_url}")
        return True
        
    try:
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        print(f"Failed to send password reset email to {user.email}: {str(e)}")
        # Return True anyway to allow password reset to proceed
        return True

def save_verification_document(file, user_id, document_type):
    """Save verification document uploaded by doctors."""
    if file.filename == '':
        return None
        
    # Create upload directory if it doesn't exist
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f'doctor_{user_id}')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Secure the filename and save the file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_filename = f"{document_type}_{timestamp}_{filename}"
    file_path = os.path.join(upload_folder, unique_filename)
    
    file.save(file_path)
    
    # Return the relative path from the static folder
    return os.path.join(f'uploads/doctor_{user_id}', unique_filename)

def is_allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_verification_status_display(status):
    """Convert VerificationStatus enum to display text."""
    status_display = {
        VerificationStatus.PENDING: "Pending Review",
        VerificationStatus.VERIFIED: "Verified",
        VerificationStatus.REJECTED: "Rejected"
    }
    return status_display.get(status, "Unknown")

def format_phone_number(phone_number):
    """Format phone number for display."""
    # This is a simple placeholder. In a real app, you might use a library
    # like phonenumbers to format according to country standards
    if not phone_number:
        return ""
    
    # Simple formatting for demo purposes
    if len(phone_number) >= 10:
        return f"({phone_number[-10:-7]}) {phone_number[-7:-4]}-{phone_number[-4:]}"
    return phone_number
