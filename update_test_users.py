from app import create_app, db
from models import User, UserType
from werkzeug.security import generate_password_hash, check_password_hash

def update_test_users():
    """Update test users to be compatible with the login system"""
    app = create_app()
    with app.app_context():
        print("Updating test users for login compatibility...")
        
        # Update doctor users
        doctor_users = User.query.filter_by(user_type=UserType.DOCTOR).all()
        for i, user in enumerate(doctor_users, 1):
            # Skip the first user as we'll use it for testing
            if i == 1:
                # Update the first doctor's password using werkzeug's check_password_hash compatible format
                user.password_hash = generate_password_hash('password')
                print(f"Updated Doctor1 (email: {user.email}) with password: 'password'")
        
        # Update patient users
        patient_users = User.query.filter_by(user_type=UserType.PATIENT).all()
        for i, user in enumerate(patient_users, 1):
            # Skip the first user as we'll use it for testing
            if i == 1:
                # Update the first patient's password using werkzeug's check_password_hash compatible format
                user.password_hash = generate_password_hash('password')
                print(f"Updated Patient1 (email: {user.email}) with password: 'password'")
        
        # Commit changes
        db.session.commit()
        print("Test users updated successfully!")
        
        # Print login credentials for testing
        doctor = User.query.filter_by(user_type=UserType.DOCTOR).first()
        patient = User.query.filter_by(user_type=UserType.PATIENT).first()
        
        print("\nTest Login Credentials:")
        print(f"Doctor: {doctor.email} / password")
        print(f"Patient: {patient.email} / password")

if __name__ == "__main__":
    update_test_users()
