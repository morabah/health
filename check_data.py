from app import create_app, db
from models import User, Doctor, Patient, Appointment, DoctorAvailability, Notification

def check_database():
    """Check the database contents"""
    app = create_app()
    with app.app_context():
        print('Database Contents:')
        print('-----------------')
        print(f'Users: {User.query.count()}')
        print(f'Doctors: {Doctor.query.count()}')
        print(f'Patients: {Patient.query.count()}')
        print(f'Appointments: {Appointment.query.count()}')
        print(f'Doctor Availability Slots: {DoctorAvailability.query.count()}')
        print(f'Notifications: {Notification.query.count()}')
        
        print('\nSample Doctor:')
        doctor = Doctor.query.first()
        print(f'Name: {doctor.user.first_name} {doctor.user.last_name}')
        print(f'Specialty: {doctor.specialty}')
        print(f'Location: {doctor.location}')
        print(f'Languages: {doctor.languages}')
        print(f'Consultation Fee: {doctor.consultation_fee}')
        
        print('\nSample Patient:')
        patient = Patient.query.first()
        print(f'Name: {patient.user.first_name} {patient.user.last_name}')
        print(f'Gender: {patient.gender}')
        print(f'Blood Type: {patient.blood_type}')
        
        print('\nSample Appointment:')
        appointment = Appointment.query.first()
        print(f'Doctor: {appointment.doctor.user.first_name} {appointment.doctor.user.last_name}')
        print(f'Patient: {appointment.patient.user.first_name} {appointment.patient.user.last_name}')
        print(f'Date: {appointment.appointment_date}')
        print(f'Time: {appointment.start_time} - {appointment.end_time}')
        print(f'Status: {appointment.status}')
        print(f'Reason: {appointment.reason}')
        
        print('\nSample Doctor Availability:')
        availability = DoctorAvailability.query.first()
        print(f'Doctor: {availability.doctor.user.first_name} {availability.doctor.user.last_name}')
        print(f'Day of Week: {availability.day_of_week}')
        print(f'Time: {availability.start_time} - {availability.end_time}')

if __name__ == "__main__":
    check_database()
