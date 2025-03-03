import os
import sys

# Add the parent directory to sys.path to import app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from app import create_app, db
from models import User, Patient, Doctor, Appointment, DoctorAvailability, Notification, VerificationDocument

def create_tables():
    """Create all tables defined in models.py"""
    print("Creating all database tables...")
    
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if tables were created successfully
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"Tables in database: {tables}")
        
        # Verify specific tables
        expected_tables = [
            'users', 'patients', 'doctors', 'appointments', 
            'doctor_availability', 'notifications', 'verification_documents'
        ]
        
        for table in expected_tables:
            if table in tables:
                print(f"✓ Table '{table}' exists")
            else:
                print(f"✗ Table '{table}' is missing")
        
        print("Database initialization completed!")

if __name__ == "__main__":
    create_tables()
