from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import enum

db = SQLAlchemy()

class UserType(enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class VerificationStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class User(db.Model, UserMixin):
    """Base user model for both patients and doctors."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False)
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
    
    def __repr__(self):
        return f'<User {self.email}>'

class Patient(db.Model):
    """Patient-specific information."""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_type = db.Column(db.String(5))
    medical_history = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Patient {self.user.first_name} {self.user.last_name}>'

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
    
    # Documents for verification
    license_document_path = db.Column(db.String(255))
    certificate_path = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Doctor {self.user.first_name} {self.user.last_name}>'

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
    
    def __repr__(self):
        return f'<VerificationDocument {self.document_type} for Doctor {self.doctor_id}>'
