#!/usr/bin/env python3
"""
Database Management Script for Health Appointment System
Usage:
- List all users: python manage_db.py list_users
- List all patients: python manage_db.py list_patients
- List all doctors: python manage_db.py list_doctors
- Add admin user: python manage_db.py add_admin <email> <password>
- Delete user: python manage_db.py delete_user <user_id>
- Verify doctor: python manage_db.py verify_doctor <doctor_id>
- Activate user: python manage_db.py activate_user <user_id>
"""

import sys
import os
from app import create_app
from models import db, User, Patient, Doctor, UserType, VerificationStatus, VerificationDocument
from werkzeug.security import generate_password_hash

def list_users():
    """List all users in the database."""
    users = User.query.all()
    print(f"Total users: {len(users)}")
    print("-" * 80)
    print(f"{'ID':<5} {'Email':<30} {'User Type':<15} {'Active':<10} {'Created At'}")
    print("-" * 80)
    for user in users:
        print(f"{user.id:<5} {user.email:<30} {user.user_type.name:<15} {user.is_active:<10} {user.created_at}")

def list_patients():
    """List all patients in the database."""
    patients = Patient.query.all()
    print(f"Total patients: {len(patients)}")
    print("-" * 80)
    print(f"{'ID':<5} {'User ID':<10} {'Name':<20} {'Gender':<10} {'Blood Type':<10} {'DOB'}")
    print("-" * 80)
    for patient in patients:
        user = User.query.get(patient.user_id)
        name = f"{user.first_name} {user.last_name}" if user else "Unknown"
        print(f"{patient.id:<5} {patient.user_id:<10} {name:<20} {patient.gender:<10} {patient.blood_type:<10} {patient.date_of_birth}")

def list_doctors():
    """List all doctors in the database."""
    doctors = Doctor.query.all()
    print(f"Total doctors: {len(doctors)}")
    print("-" * 80)
    print(f"{'ID':<5} {'User ID':<10} {'Name':<20} {'Specialty':<20} {'License':<15} {'Status'}")
    print("-" * 80)
    for doctor in doctors:
        user = User.query.get(doctor.user_id)
        name = f"{user.first_name} {user.last_name}" if user else "Unknown"
        status = doctor.verification_status.name
        print(f"{doctor.id:<5} {doctor.user_id:<10} {name:<20} {doctor.specialty:<20} {doctor.license_number:<15} {status}")

def add_admin(email, password):
    """Add an admin user to the database."""
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print(f"User with email {email} already exists.")
        return
    
    # Create new admin user - since there's no ADMIN type, we'll use DOCTOR type
    admin = User(
        email=email,
        password_hash=generate_password_hash(password),
        first_name="Admin",
        last_name="User",
        phone="+1234567890",  # Placeholder
        user_type=UserType.DOCTOR,  # Using DOCTOR type as there's no ADMIN
        email_verified=True,
        phone_verified=True,
        is_active=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    # Create a doctor profile for the admin
    doctor = Doctor(
        user_id=admin.id,
        specialty="Administration",
        license_number="ADMIN-" + str(admin.id),
        years_of_experience=10,
        education="System Administrator",
        bio="System Administrator",
        verification_status=VerificationStatus.VERIFIED
    )
    
    db.session.add(doctor)
    db.session.commit()
    
    print(f"Admin user created with ID: {admin.id}")

def delete_user(user_id):
    """Delete a user and associated records from the database."""
    user = User.query.get(user_id)
    if not user:
        print(f"User with ID {user_id} not found.")
        return
    
    # Delete associated patient or doctor record
    if user.user_type == UserType.PATIENT:
        patient = Patient.query.filter_by(user_id=user.id).first()
        if patient:
            db.session.delete(patient)
    elif user.user_type == UserType.DOCTOR:
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        if doctor:
            # Delete verification documents
            docs = VerificationDocument.query.filter_by(doctor_id=doctor.id).all()
            for doc in docs:
                db.session.delete(doc)
            db.session.delete(doctor)
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    print(f"User with ID {user_id} and associated records deleted.")

def verify_doctor(doctor_id):
    """Verify a doctor's account."""
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        print(f"Doctor with ID {doctor_id} not found.")
        return
    
    user = User.query.get(doctor.user_id)
    if not user:
        print(f"User associated with doctor ID {doctor_id} not found.")
        return
    
    doctor.verification_status = VerificationStatus.VERIFIED
    user.is_active = True
    db.session.commit()
    print(f"Doctor with ID {doctor_id} has been verified.")

def activate_user(user_id):
    """Activate a user account."""
    user = User.query.get(user_id)
    if not user:
        print(f"User with ID {user_id} not found.")
        return
    
    user.is_active = True
    user.email_verified = True
    user.phone_verified = True
    db.session.commit()
    print(f"User with ID {user_id} has been activated.")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        command = sys.argv[1]
        
        if command == "list_users":
            list_users()
        elif command == "list_patients":
            list_patients()
        elif command == "list_doctors":
            list_doctors()
        elif command == "add_admin" and len(sys.argv) == 4:
            add_admin(sys.argv[2], sys.argv[3])
        elif command == "delete_user" and len(sys.argv) == 3:
            delete_user(int(sys.argv[2]))
        elif command == "verify_doctor" and len(sys.argv) == 3:
            verify_doctor(int(sys.argv[2]))
        elif command == "activate_user" and len(sys.argv) == 3:
            activate_user(int(sys.argv[2]))
        else:
            print("Invalid command or missing arguments.")
            print(__doc__)

if __name__ == "__main__":
    main()
