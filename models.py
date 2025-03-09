from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import enum
from typing import Optional, List
from sqlalchemy.types import TypeDecorator, DateTime as BaseDateTime
import logging

db = SQLAlchemy()
logger = logging.getLogger(__name__)

class UserType(enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class VerificationStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class AppointmentStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class DateTime(TypeDecorator):
    impl = BaseDateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        # Store as a proper datetime (not as string)
        return value

    def process_result_value(self, value, dialect):
        logger.info(f"Processing result value: {value}, type: {type(value)}")
        if value is None:
            return None
        # We always want to ensure a datetime is returned, nothing else
        if isinstance(value, datetime):
            return value
        # Try to convert strings or other formats to datetime
        try:
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            # Last resort for other formats
            return datetime.fromtimestamp(value.timestamp())
        except (AttributeError, ValueError) as e:
            logger.error(f"Failed to convert value to datetime: {value}, error: {e}")
            # Return a default datetime rather than failing
            return datetime.utcnow()

class User(db.Model, UserMixin):
    """Base user model for both patients and doctors."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Phone verification
    phone_verified = db.Column(db.Boolean, default=False)
    phone_verification_code = db.Column(db.String(6))
    phone_verification_sent_at = db.Column(db.DateTime)
    
    # Email verification
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100))
    email_verification_sent_at = db.Column(db.DateTime)
    
    # Relationship with specific user type
    patient = db.relationship('Patient', backref='user', uselist=False, cascade='all, delete-orphan')
    doctor = db.relationship('Doctor', backref='user', uselist=False, cascade='all, delete-orphan')
    
    # Relationships
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        """Return string representation of User."""
        return f"User(id={self.id}, email={self.email}, type={self.user_type.value})"
    
    def get_full_name(self) -> str:
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}"
    
    def get_unread_notifications_count(self) -> int:
        """Get count of unread notifications for this user."""
        from sqlalchemy import func
        from sqlalchemy.orm import Session
        
        session = Session.object_session(self)
        return session.query(func.count(Notification.id)).filter(
            Notification.user_id == self.id,
            Notification.is_read == False
        ).scalar() or 0

class Patient(db.Model):
    """Patient-specific information."""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_type = db.Column(db.String(5))
    medical_history = db.Column(db.Text)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient_appointments', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='patient_reviews', lazy='dynamic')
    
    def __repr__(self) -> str:
        """Return string representation of Patient."""
        return f"Patient(id={self.id}, user_id={self.user_id}, date_of_birth={self.date_of_birth})"

class Doctor(db.Model):
    """Doctor-specific information with credential verification."""
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialty = db.Column(db.String(100))
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    years_of_experience = db.Column(db.Integer)
    education = db.Column(db.Text)
    bio = db.Column(db.Text)
    verification_status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING)
    verification_notes = db.Column(db.Text)
    
    # Profile information
    location = db.Column(db.String(255))
    languages = db.Column(db.String(255))  # Comma-separated list of languages
    consultation_fee = db.Column(db.Float)
    profile_picture = db.Column(db.String(255))
    
    # Documents for verification
    license_document_path = db.Column(db.String(255))
    certificate_path = db.Column(db.String(255))
    
    # Relationships
    availability = db.relationship('DoctorAvailability', backref='doctor', lazy=True, cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='doctor_appointments', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='doctor_reviews', lazy='dynamic')
    
    def __repr__(self) -> str:
        """Return string representation of Doctor."""
        return f"Doctor(id={self.id}, user_id={self.user_id}, specialty={self.specialty})"

class DoctorAvailability(db.Model):
    """Doctor's available consultation times."""
    __tablename__ = 'doctor_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    def __repr__(self) -> str:
        """Return string representation of DoctorAvailability."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = days[self.day_of_week]
        return f"Availability(id={self.id}, doctor_id={self.doctor_id}, day={day_name}, start_time={self.start_time}, end_time={self.end_time})"

class VerificationDocument(db.Model):
    """Documents uploaded by doctors for verification."""
    __tablename__ = 'verification_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    doctor = db.relationship('Doctor', backref=db.backref('documents', lazy=True))
    
    def __repr__(self) -> str:
        """Return string representation of VerificationDocument."""
        return f"VerificationDocument(id={self.id}, doctor_id={self.doctor_id}, document_type={self.document_type})"

class Appointment(db.Model):
    """Appointment booking between patients and doctors."""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), index=True, nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), index=True, nullable=False)
    appointment_date = db.Column(DateTime, index=True, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum(AppointmentStatus), index=True, default=AppointmentStatus.PENDING)
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship definitions
    patient = db.relationship('Patient', backref='appointments_list')
    doctor = db.relationship('Doctor', backref='appointments_list')
    
    def __repr__(self) -> str:
        """Return string representation of Appointment."""
        return f"Appointment(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, appointment_date={self.appointment_date})"

class Review(db.Model):
    """Reviews for doctors."""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', backref='patient_reviews', lazy='select')
    doctor = db.relationship('Doctor', backref='doctor_reviews', lazy='select')
    
    def __repr__(self) -> str:
        """Return string representation of Review."""
        return f"Review(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, rating={self.rating})"

class Notification(db.Model):
    """Notifications for users."""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        """Return string representation of Notification."""
        return f"Notification(id={self.id}, user_id={self.user_id}, title={self.title})"
