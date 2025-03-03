from app import create_app, db
from models import Doctor
from sqlalchemy import or_

def check_doctor_search():
    """Check the doctor search functionality"""
    app = create_app()
    with app.app_context():
        print('Doctor Search Results')
        print('-' * 50)
        
        # Search by specialty
        print('\nSearch by Specialty: Cardiology')
        doctors = Doctor.query.filter_by(specialty='Cardiology').all()
        for doctor in doctors:
            print(f'Name: {doctor.user.first_name} {doctor.user.last_name}')
            print(f'Specialty: {doctor.specialty}')
            print(f'Location: {doctor.location}')
            print(f'Languages: {doctor.languages}')
            print(f'Consultation Fee: {doctor.consultation_fee}')
            print('-' * 30)
        
        # Search by location
        print('\nSearch by Location: Algiers')
        doctors = Doctor.query.filter_by(location='Algiers').all()
        for doctor in doctors:
            print(f'Name: {doctor.user.first_name} {doctor.user.last_name}')
            print(f'Specialty: {doctor.specialty}')
            print(f'Location: {doctor.location}')
            print(f'Languages: {doctor.languages}')
            print(f'Consultation Fee: {doctor.consultation_fee}')
            print('-' * 30)
        
        # Search by language
        print('\nSearch by Language: French')
        doctors = Doctor.query.filter(Doctor.languages.like('%French%')).all()
        for doctor in doctors:
            print(f'Name: {doctor.user.first_name} {doctor.user.last_name}')
            print(f'Specialty: {doctor.specialty}')
            print(f'Location: {doctor.location}')
            print(f'Languages: {doctor.languages}')
            print(f'Consultation Fee: {doctor.consultation_fee}')
            print('-' * 30)
        
        # Combined search
        print('\nCombined Search: Specialty=Neurology OR Location=Oran')
        doctors = Doctor.query.filter(
            or_(
                Doctor.specialty == 'Neurology',
                Doctor.location == 'Oran'
            )
        ).all()
        for doctor in doctors:
            print(f'Name: {doctor.user.first_name} {doctor.user.last_name}')
            print(f'Specialty: {doctor.specialty}')
            print(f'Location: {doctor.location}')
            print(f'Languages: {doctor.languages}')
            print(f'Consultation Fee: {doctor.consultation_fee}')
            print('-' * 30)

if __name__ == "__main__":
    check_doctor_search()
