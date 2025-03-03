from app import create_app, db
from models import Doctor, DoctorAvailability

def check_doctor_availability():
    """Check the doctor availability data"""
    app = create_app()
    with app.app_context():
        # Get the first doctor
        doctor = Doctor.query.first()
        print(f'Availability for: {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})')
        print('-' * 50)
        
        # Get availability slots
        availability_slots = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id
        ).order_by(
            DoctorAvailability.day_of_week, DoctorAvailability.start_time
        ).all()
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_num in range(7):
            day_slots = [slot for slot in availability_slots if slot.day_of_week == day_num]
            
            if day_slots:
                print(f'\n{days[day_num]}:')
                for slot in day_slots:
                    print(f'  {slot.start_time} - {slot.end_time}')
            else:
                print(f'\n{days[day_num]}: No availability')
        
        # Check another doctor
        doctor = Doctor.query.filter_by(specialty='Dermatology').first()
        print('\n\n' + '-' * 50)
        print(f'Availability for: {doctor.user.first_name} {doctor.user.last_name} ({doctor.specialty})')
        print('-' * 50)
        
        # Get availability slots
        availability_slots = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id
        ).order_by(
            DoctorAvailability.day_of_week, DoctorAvailability.start_time
        ).all()
        
        for day_num in range(7):
            day_slots = [slot for slot in availability_slots if slot.day_of_week == day_num]
            
            if day_slots:
                print(f'\n{days[day_num]}:')
                for slot in day_slots:
                    print(f'  {slot.start_time} - {slot.end_time}')
            else:
                print(f'\n{days[day_num]}: No availability')

if __name__ == "__main__":
    check_doctor_availability()
