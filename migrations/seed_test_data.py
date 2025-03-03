import os
import sys
import random
from datetime import datetime, timedelta, time
from werkzeug.security import generate_password_hash

# Add the parent directory to sys.path to import app
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from app import create_app, db
from models import (
    User, Patient, Doctor, Appointment, DoctorAvailability, 
    Notification, VerificationDocument, UserType, VerificationStatus,
    AppointmentStatus
)

def seed_database():
    """Seed the database with test data"""
    print("Seeding database with test data...")
    
    app = create_app()
    with app.app_context():
        # Clear existing data
        print("Clearing existing data...")
        Notification.query.delete()
        Appointment.query.delete()
        DoctorAvailability.query.delete()
        VerificationDocument.query.delete()
        Doctor.query.delete()
        Patient.query.delete()
        User.query.delete()
        db.session.commit()
        print("Existing data cleared.")
        
        # Create admin user
        admin_user = User(
            email='admin@example.com',
            password_hash=generate_password_hash('password'),
            first_name='Admin',
            last_name='User',
            phone='+213500000000',
            user_type=UserType.ADMIN,
            is_active=True,
            email_verified=True,
            phone_verified=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created.")
        
        # Create test doctors
        specialties = [
            'Cardiology', 'Dermatology', 'Neurology', 'Pediatrics', 
            'Orthopedics', 'Ophthalmology', 'Psychiatry', 'Gynecology'
        ]
        
        locations = [
            'Algiers', 'Oran', 'Constantine', 'Annaba', 
            'Batna', 'Setif', 'Djelfa', 'Biskra'
        ]
        
        languages = ['Arabic', 'French', 'English', 'Berber']
        
        doctors = []
        for i in range(1, 9):
            # Create user for doctor
            doctor_user = User(
                email=f'doctor{i}@example.com',
                password_hash=generate_password_hash('password'),
                first_name=f'Doctor{i}',
                last_name=f'LastName{i}',
                phone=f'+21351{i}000000',
                user_type=UserType.DOCTOR,
                is_active=True,
                email_verified=True,
                phone_verified=True
            )
            db.session.add(doctor_user)
            db.session.commit()  # Commit to get the ID
            
            # Create doctor profile
            doctor = Doctor(
                user_id=doctor_user.id,
                specialty=specialties[i-1],
                license_number=f'LIC-{1000+i}',
                years_of_experience=random.randint(1, 20),
                education=f'Medical School {i}, Graduated {2010-random.randint(0, 15)}',
                bio=f'Experienced {specialties[i-1]} specialist with a focus on patient care.',
                verification_status=VerificationStatus.VERIFIED,
                location=locations[i-1],
                languages=', '.join(random.sample(languages, random.randint(1, 3))),
                consultation_fee=random.randint(2000, 5000),
                profile_picture=None
            )
            db.session.add(doctor)
            db.session.commit()  # Commit to get the ID
            doctors.append(doctor)
            
            # Create availability for each doctor
            for day in range(7):  # 0=Monday, 6=Sunday
                # Morning slot
                morning_start = time(9, 0)
                morning_end = time(12, 0)
                
                # Afternoon slot
                afternoon_start = time(14, 0)
                afternoon_end = time(17, 0)
                
                # Add morning availability
                if random.choice([True, False]):
                    availability = DoctorAvailability(
                        doctor_id=doctor.id,
                        day_of_week=day,
                        start_time=morning_start,
                        end_time=morning_end
                    )
                    db.session.add(availability)
                
                # Add afternoon availability
                if random.choice([True, False]):
                    availability = DoctorAvailability(
                        doctor_id=doctor.id,
                        day_of_week=day,
                        start_time=afternoon_start,
                        end_time=afternoon_end
                    )
                    db.session.add(availability)
            
            # Commit availability
            db.session.commit()
        
        print(f"Created {len(doctors)} doctors with availability.")
        
        # Create test patients
        patients = []
        for i in range(1, 11):
            # Create user for patient
            patient_user = User(
                email=f'patient{i}@example.com',
                password_hash=generate_password_hash('password'),
                first_name=f'Patient{i}',
                last_name=f'LastName{i}',
                phone=f'+21352{i}000000',
                user_type=UserType.PATIENT,
                is_active=True,
                email_verified=True,
                phone_verified=True
            )
            db.session.add(patient_user)
            db.session.commit()  # Commit to get the ID
            
            # Create patient profile
            blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            genders = ['Male', 'Female']
            
            patient = Patient(
                user_id=patient_user.id,
                date_of_birth=datetime.now() - timedelta(days=365*random.randint(18, 70)),
                gender=random.choice(genders),
                blood_type=random.choice(blood_types),
                medical_history=f'Patient {i} medical history: No significant medical issues.'
            )
            db.session.add(patient)
            db.session.commit()  # Commit to get the ID
            patients.append(patient)
        
        print(f"Created {len(patients)} patients.")
        
        # Create appointments
        appointment_reasons = [
            'Regular check-up', 'Follow-up visit', 'Consultation for symptoms',
            'Prescription renewal', 'Test results review', 'Chronic condition management'
        ]
        
        # Today's date
        today = datetime.now().date()
        
        # Create some past appointments
        past_appointments = []
        for _ in range(15):
            appointment_date = today - timedelta(days=random.randint(1, 30))
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            
            # Create a completed appointment
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_date=appointment_date,
                start_time=time(9 + random.randint(0, 7), 0),
                end_time=time(10 + random.randint(0, 7), 0),
                status=AppointmentStatus.COMPLETED,
                reason=random.choice(appointment_reasons),
                notes=f'Appointment completed on {appointment_date}',
                created_at=datetime.now() - timedelta(days=random.randint(40, 60)),
                updated_at=datetime.now() - timedelta(days=random.randint(1, 10))
            )
            db.session.add(appointment)
            past_appointments.append(appointment)
            
            # Add notification for completed appointment
            notification = Notification(
                user_id=patient.user_id,
                title='Appointment Completed',
                message=f'Your appointment with Dr. {doctor.user.last_name} on {appointment_date} has been marked as completed.',
                is_read=random.choice([True, False]),
                created_at=datetime.now() - timedelta(days=random.randint(1, 10))
            )
            db.session.add(notification)
        
        # Commit past appointments
        db.session.commit()
        print(f"Created {len(past_appointments)} past appointments.")
        
        # Create today's appointments
        today_appointments = []
        for _ in range(5):
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            
            # Create appointment for today
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_date=today,
                start_time=time(9 + random.randint(0, 7), 0),
                end_time=time(10 + random.randint(0, 7), 0),
                status=random.choice([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]),
                reason=random.choice(appointment_reasons),
                notes=f'Today\'s appointment',
                created_at=datetime.now() - timedelta(days=random.randint(1, 7)),
                updated_at=datetime.now() - timedelta(days=random.randint(0, 1))
            )
            db.session.add(appointment)
            today_appointments.append(appointment)
            
            # Add notification for today's appointment
            notification = Notification(
                user_id=doctor.user_id,
                title='Appointment Today',
                message=f'You have an appointment with {patient.user.first_name} {patient.user.last_name} today at {appointment.start_time.strftime("%H:%M")}.',
                is_read=False,
                created_at=datetime.now() - timedelta(hours=random.randint(1, 12))
            )
            db.session.add(notification)
        
        # Commit today's appointments
        db.session.commit()
        print(f"Created {len(today_appointments)} today's appointments.")
        
        # Create future appointments
        future_appointments = []
        for _ in range(10):
            appointment_date = today + timedelta(days=random.randint(1, 14))
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            
            # Create a future appointment
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_date=appointment_date,
                start_time=time(9 + random.randint(0, 7), 0),
                end_time=time(10 + random.randint(0, 7), 0),
                status=random.choice([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]),
                reason=random.choice(appointment_reasons),
                notes=f'Future appointment scheduled for {appointment_date}',
                created_at=datetime.now() - timedelta(days=random.randint(1, 5)),
                updated_at=datetime.now() - timedelta(days=random.randint(0, 1))
            )
            db.session.add(appointment)
            future_appointments.append(appointment)
            
            # Add notification for booking confirmation
            notification = Notification(
                user_id=patient.user_id,
                title='Appointment Booked',
                message=f'Your appointment with Dr. {doctor.user.last_name} has been scheduled for {appointment_date} at {appointment.start_time.strftime("%H:%M")}.',
                is_read=random.choice([True, False]),
                created_at=datetime.now() - timedelta(days=random.randint(1, 5))
            )
            db.session.add(notification)
        
        # Commit future appointments
        db.session.commit()
        print(f"Created {len(future_appointments)} future appointments.")
        
        # Create some cancelled appointments
        cancelled_appointments = []
        for _ in range(3):
            appointment_date = today + timedelta(days=random.randint(-10, 10))
            doctor = random.choice(doctors)
            patient = random.choice(patients)
            
            # Create a cancelled appointment
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_date=appointment_date,
                start_time=time(9 + random.randint(0, 7), 0),
                end_time=time(10 + random.randint(0, 7), 0),
                status=AppointmentStatus.CANCELLED,
                reason=random.choice(appointment_reasons),
                notes=f'Appointment cancelled',
                created_at=datetime.now() - timedelta(days=random.randint(5, 15)),
                updated_at=datetime.now() - timedelta(days=random.randint(1, 4))
            )
            db.session.add(appointment)
            cancelled_appointments.append(appointment)
            
            # Add notification for cancellation
            notification = Notification(
                user_id=doctor.user_id,
                title='Appointment Cancelled',
                message=f'The appointment with {patient.user.first_name} {patient.user.last_name} scheduled for {appointment_date} has been cancelled.',
                is_read=random.choice([True, False]),
                created_at=datetime.now() - timedelta(days=random.randint(1, 4))
            )
            db.session.add(notification)
        
        # Commit all changes
        db.session.commit()
        print(f"Created {len(cancelled_appointments)} cancelled appointments.")
        
        # Print summary
        print("\nDatabase Seeding Summary:")
        print(f"Created {len(doctors)} doctors")
        print(f"Created {len(patients)} patients")
        print(f"Created {Appointment.query.count()} appointments")
        print(f"Created {Notification.query.count()} notifications")
        print(f"Created {DoctorAvailability.query.count()} availability slots")
        
        print("\nTest User Credentials:")
        print("Admin: admin@example.com / password")
        print("Doctors: doctor1@example.com through doctor8@example.com / password")
        print("Patients: patient1@example.com through patient10@example.com / password")
        
        print("\nDatabase seeded successfully!")

if __name__ == "__main__":
    seed_database()
