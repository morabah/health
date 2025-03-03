from app import create_app, db
from models import Patient, Appointment, Notification, AppointmentStatus
from datetime import datetime

def check_patient_dashboard():
    """Check the patient dashboard data"""
    app = create_app()
    with app.app_context():
        # Get the first patient
        patient = Patient.query.first()
        print(f'Patient Dashboard for: {patient.user.first_name} {patient.user.last_name}')
        print('-' * 50)
        
        # Get today's date
        today = datetime.now().date()
        
        # Get upcoming appointments
        upcoming_appointments = Appointment.query.filter_by(
            patient_id=patient.id
        ).filter(
            Appointment.appointment_date >= today,
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING])
        ).order_by(
            Appointment.appointment_date, Appointment.start_time
        ).all()
        
        print(f'\nUpcoming Appointments ({len(upcoming_appointments)}):')
        for appointment in upcoming_appointments:
            print(f'Date: {appointment.appointment_date}, Time: {appointment.start_time} - {appointment.end_time}')
            print(f'Doctor: {appointment.doctor.user.first_name} {appointment.doctor.user.last_name} ({appointment.doctor.specialty})')
            print(f'Status: {appointment.status}')
            print(f'Reason: {appointment.reason}')
            print('-' * 30)
        
        # Get past appointments
        past_appointments = Appointment.query.filter_by(
            patient_id=patient.id
        ).filter(
            Appointment.status == AppointmentStatus.COMPLETED
        ).order_by(
            Appointment.appointment_date.desc(), Appointment.start_time
        ).limit(5).all()
        
        print(f'\nPast Appointments ({len(past_appointments)}):')
        for appointment in past_appointments:
            print(f'Date: {appointment.appointment_date}, Time: {appointment.start_time} - {appointment.end_time}')
            print(f'Doctor: {appointment.doctor.user.first_name} {appointment.doctor.user.last_name} ({appointment.doctor.specialty})')
            print(f'Status: {appointment.status}')
            print(f'Reason: {appointment.reason}')
            print('-' * 30)
        
        # Get notifications
        notifications = Notification.query.filter_by(
            user_id=patient.user_id
        ).order_by(
            Notification.created_at.desc()
        ).limit(5).all()
        
        print(f'\nNotifications ({len(notifications)}):')
        for notification in notifications:
            print(f'Title: {notification.title}')
            print(f'Message: {notification.message}')
            print(f'Read: {notification.is_read}')
            print(f'Created: {notification.created_at}')
            print('-' * 30)

if __name__ == "__main__":
    check_patient_dashboard()
