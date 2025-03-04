import os
import random
import string
from datetime import datetime, timedelta
import uuid
from flask import current_app, url_for
from flask_mail import Message
from werkzeug.utils import secure_filename
from models import User, VerificationStatus, Notification, DoctorAvailability, Appointment, AppointmentStatus, db
import logging
import secrets
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

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
    if not file:
        return None
    
    # Create directory if it doesn't exist
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f'doctor_{user_id}')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1]
    unique_filename = f"{document_type}_{uuid.uuid4().hex}{file_ext}"
    
    # Save file
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    # Return relative path for database storage
    return os.path.join(f'uploads/doctor_{user_id}', unique_filename)

def save_profile_picture(form_picture, user_id):
    """
    Save a profile picture uploaded by a doctor.
    
    Args:
        form_picture: The uploaded file from the form
        user_id: The ID of the user uploading the picture
        
    Returns:
        The relative path to the saved picture
    """
    # Generate a random filename to avoid collisions
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_picture.filename)
    picture_filename = f"profile_{user_id}_{random_hex}{file_extension}"
    
    # Create the path to save the picture
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_filename)
    
    # Resize the image to save space and ensure consistent size
    output_size = (300, 300)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    
    # Save the picture
    img.save(picture_path)
    
    # Return the relative path to be stored in the database
    return f'profile_pics/{picture_filename}'

def create_notification(user_id, title, message):
    """Create and store a notification with database context"""
    with current_app.app_context():
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Notification failed: {str(e)}")

def get_available_slots(doctor_id, date):
    """
    Get available appointment slots for a doctor on a specific date.
    
    Args:
        doctor_id: The ID of the doctor
        date: The date to check for availability
        
    Returns:
        A list of available time slots as (start_time, end_time) tuples
    """
    # Get the day of week (0=Monday, 6=Sunday)
    day_of_week = date.weekday()
    
    # Get the doctor's availability for that day
    availabilities = DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        day_of_week=day_of_week,
        is_available=True
    ).all()
    
    if not availabilities:
        return []
    
    # Get existing appointments for that doctor on that date
    existing_appointments = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=date
    ).filter(
        Appointment.status != AppointmentStatus.CANCELLED
    ).all()
    
    # Create a list of booked time slots
    booked_slots = [(app.start_time, app.end_time) for app in existing_appointments]
    
    # Create a list of all possible time slots based on availability
    all_slots = []
    for availability in availabilities:
        # Create 30-minute slots within the availability period
        current_time = availability.start_time
        while current_time < availability.end_time:
            # Calculate end time of this slot (30 minutes later)
            slot_end_time = (datetime.combine(date, current_time) + timedelta(minutes=30)).time()
            
            # If slot end time exceeds availability end time, use availability end time
            if slot_end_time > availability.end_time:
                slot_end_time = availability.end_time
            
            # Add this slot to all slots
            all_slots.append((current_time, slot_end_time))
            
            # Move to next slot
            current_time = slot_end_time
    
    # Filter out booked slots
    available_slots = []
    for slot in all_slots:
        # Check if this slot overlaps with any booked slot
        is_available = True
        for booked in booked_slots:
            # If slot start time is less than booked end time AND slot end time is greater than booked start time
            if slot[0] < booked[1] and slot[1] > booked[0]:
                is_available = False
                break
        
        if is_available:
            available_slots.append(slot)
    
    return available_slots

def format_time_slot(slot):
    """
    Format a time slot tuple for display.
    
    Args:
        slot: A tuple of (start_time, end_time)
        
    Returns:
        A formatted string representation of the time slot
    """
    start_time, end_time = slot
    return f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

def parse_time_slot(slot_string):
    """
    Parse a time slot string back into a tuple of time objects.
    
    Args:
        slot_string: A string in the format "HH:MM - HH:MM"
        
    Returns:
        A tuple of (start_time, end_time) as time objects
    """
    start_str, end_str = slot_string.split(' - ')
    start_time = datetime.strptime(start_str, '%H:%M').time()
    end_time = datetime.strptime(end_str, '%H:%M').time()
    return (start_time, end_time)

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
