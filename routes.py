from datetime import datetime, time
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient, Doctor, UserType, VerificationStatus, VerificationDocument, DoctorAvailability, Appointment, AppointmentStatus, Notification
from forms import (PatientRegistrationForm, DoctorRegistrationForm, LoginForm, 
                  PhoneVerificationForm, ResendVerificationForm, ForgotPasswordForm, 
                  ResetPasswordForm, DoctorProfileForm, DoctorAvailabilityForm, DoctorSearchForm,
                  AppointmentBookingForm, AppointmentCancellationForm, AppointmentRescheduleForm)
from utils import (generate_verification_code, generate_verification_token, 
                  send_verification_email, send_verification_sms, 
                  send_password_reset_email, save_verification_document, save_profile_picture,
                  create_notification, get_available_slots, format_time_slot, parse_time_slot)
import os

# Create blueprints for different sections of the app
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
patient = Blueprint('patient', __name__)
doctor = Blueprint('doctor', __name__)
admin = Blueprint('admin', __name__)

# Main routes
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')

# Authentication routes
@auth.route('/register', methods=['GET'])
def register():
    return render_template('auth/register_choice.html')

@auth.route('/register/patient', methods=['GET', 'POST'])
def register_patient():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = PatientRegistrationForm()
    
    if form.validate_on_submit():
        # Create user
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            email=form.email.data,
            phone=form.phone.data,
            password_hash=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            user_type=UserType.PATIENT,
            is_active=False
        )
        
        # Generate verification codes
        phone_code = generate_verification_code()
        email_token = generate_verification_token()
        
        user.phone_verification_code = phone_code
        user.phone_verification_sent_at = datetime.utcnow()
        user.email_verification_token = email_token
        user.email_verification_sent_at = datetime.utcnow()
        
        db.session.add(user)
        db.session.flush()  # Get user ID without committing
        
        # Create patient profile
        patient = Patient(
            user_id=user.id,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            blood_type=form.blood_type.data,
            medical_history=form.medical_history.data
        )
        
        db.session.add(patient)
        db.session.commit()
        
        # Send verification emails and SMS
        send_verification_email(current_app.extensions['mail'], user, email_token)
        send_verification_sms(user, phone_code)
        
        flash('Registration successful! Please verify your email and phone number.', 'success')
        return redirect(url_for('auth.verify_phone', user_id=user.id))
    
    return render_template('auth/register_patient.html', form=form)

@auth.route('/register/doctor', methods=['GET', 'POST'])
def register_doctor():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = DoctorRegistrationForm()
    
    if form.validate_on_submit():
        # Create user
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            email=form.email.data,
            phone=form.phone.data,
            password_hash=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            user_type=UserType.DOCTOR,
            is_active=False
        )
        
        # Generate verification codes
        phone_code = generate_verification_code()
        email_token = generate_verification_token()
        
        user.phone_verification_code = phone_code
        user.phone_verification_sent_at = datetime.utcnow()
        user.email_verification_token = email_token
        user.email_verification_sent_at = datetime.utcnow()
        
        db.session.add(user)
        db.session.flush()  # Get user ID without committing
        
        # Create doctor profile
        doctor = Doctor(
            user_id=user.id,
            specialty=form.specialty.data,
            license_number=form.license_number.data,
            years_of_experience=form.years_of_experience.data,
            education=form.education.data,
            bio=form.bio.data,
            verification_status=VerificationStatus.PENDING
        )
        
        db.session.add(doctor)
        db.session.flush()  # Get doctor ID without committing
        
        # Save verification documents
        if form.license_document.data:
            license_path = save_verification_document(
                form.license_document.data, 
                user.id, 
                'license'
            )
            doctor.license_document_path = license_path
            
            # Create document record
            license_doc = VerificationDocument(
                doctor_id=doctor.id,
                document_type='License',
                file_path=license_path
            )
            db.session.add(license_doc)
        
        if form.certificate.data:
            cert_path = save_verification_document(
                form.certificate.data, 
                user.id, 
                'certificate'
            )
            doctor.certificate_path = cert_path
            
            # Create document record
            cert_doc = VerificationDocument(
                doctor_id=doctor.id,
                document_type='Certificate',
                file_path=cert_path
            )
            db.session.add(cert_doc)
        
        db.session.commit()
        
        # Send verification emails and SMS
        send_verification_email(current_app.extensions['mail'], user, email_token)
        send_verification_sms(user, phone_code)
        
        flash('Registration successful! Please verify your email and phone number. Your account will be activated after credential verification.', 'success')
        return redirect(url_for('auth.verify_phone', user_id=user.id))
    
    return render_template('auth/register_doctor.html', form=form)

@auth.route('/verify/phone/<int:user_id>', methods=['GET', 'POST'])
def verify_phone(user_id):
    user = User.query.get_or_404(user_id)
    
    # If already verified, redirect
    if user.phone_verified:
        flash('Phone already verified!', 'info')
        return redirect(url_for('auth.login'))
    
    form = PhoneVerificationForm()
    resend_form = ResendVerificationForm()
    
    if form.validate_on_submit():
        if form.verification_code.data == user.phone_verification_code:
            user.phone_verified = True
            db.session.commit()
            flash('Phone verification successful!', 'success')
            
            # Check if email is also verified
            if user.email_verified:
                # For patients, activate account immediately
                if user.user_type == UserType.PATIENT:
                    user.is_active = True
                    db.session.commit()
                    flash('Your account is now active. You can log in.', 'success')
                else:
                    flash('Your account will be activated after credential verification.', 'info')
                
                return redirect(url_for('auth.login'))
            else:
                flash('Please also verify your email address.', 'info')
                return redirect(url_for('auth.pending_verification', user_id=user.id))
        else:
            flash('Invalid verification code. Please try again.', 'danger')
    
    if resend_form.validate_on_submit():
        # Generate new code and update user
        new_code = generate_verification_code()
        user.phone_verification_code = new_code
        user.phone_verification_sent_at = datetime.utcnow()
        db.session.commit()
        
        # Send new SMS
        send_verification_sms(user, new_code)
        
        flash('A new verification code has been sent to your phone.', 'success')
    
    return render_template('auth/verify_phone.html', form=form, resend_form=resend_form)

@auth.route('/verify/email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('auth.login'))
    
    user.email_verified = True
    db.session.commit()
    
    flash('Email verification successful!', 'success')
    
    # Check if phone is also verified
    if user.phone_verified:
        # For patients, activate account immediately
        if user.user_type == UserType.PATIENT:
            user.is_active = True
            db.session.commit()
            flash('Your account is now active. You can log in.', 'success')
        else:
            flash('Your account will be activated after credential verification.', 'info')
        
        return redirect(url_for('auth.login'))
    else:
        flash('Please also verify your phone number.', 'info')
        return redirect(url_for('auth.verify_phone', user_id=user.id))

@auth.route('/pending-verification/<int:user_id>')
def pending_verification(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('auth/pending_verification.html', user=user)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            # Check if user is active
            if not user.is_active:
                # Check verification status
                if not user.email_verified or not user.phone_verified:
                    flash('Please verify your email and phone number before logging in.', 'warning')
                    return redirect(url_for('auth.pending_verification', user_id=user.id))
                
                # For doctors, check credential verification
                if user.user_type == UserType.DOCTOR:
                    if user.doctor.verification_status == VerificationStatus.PENDING:
                        flash('Your account is pending credential verification. You will be notified once verified.', 'info')
                        return redirect(url_for('main.index'))
                    elif user.doctor.verification_status == VerificationStatus.REJECTED:
                        flash('Your credential verification was rejected. Please contact support for more information.', 'danger')
                        return redirect(url_for('main.index'))
                
                # If we get here, something else is preventing activation
                flash('Your account is not active. Please contact support.', 'warning')
                return redirect(url_for('main.index'))
            
            # If all checks pass, log in the user
            login_user(user, remember=form.remember.data)
            
            # Redirect to appropriate dashboard
            next_page = request.args.get('next')
            if user.user_type == UserType.PATIENT:
                return redirect(next_page or url_for('patient.dashboard'))
            else:
                return redirect(next_page or url_for('doctor.dashboard'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            token = generate_verification_token()
            user.email_verification_token = token
            user.email_verification_sent_at = datetime.utcnow()
            db.session.commit()
            
            send_password_reset_email(current_app.extensions['mail'], user, token)
        
        # Always show success message to prevent email enumeration
        flash('If your email is registered, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        user.email_verification_token = None
        db.session.commit()
        
        flash('Your password has been reset. You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)

# Patient routes
@patient.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type != UserType.PATIENT:
        abort(403)
    
    return render_template('patient/dashboard.html')

# Doctor routes
@doctor.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type != UserType.DOCTOR:
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    # Get today's appointments
    today = datetime.now().date()
    today_appointments = Appointment.query.filter_by(
        doctor_id=doctor.id, 
        appointment_date=today
    ).order_by(Appointment.start_time).all()
    
    # Get upcoming appointments (excluding today)
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date > today,
        Appointment.status != AppointmentStatus.CANCELLED
    ).order_by(Appointment.appointment_date, Appointment.start_time).all()
    
    # Get unread notifications count
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).count()
    
    return render_template(
        'doctor/dashboard.html', 
        doctor=doctor,
        today_appointments=today_appointments,
        upcoming_appointments=upcoming_appointments,
        unread_notifications=unread_notifications
    )

@doctor.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Doctor profile management."""
    if current_user.user_type != UserType.DOCTOR:
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    form = DoctorProfileForm()
    
    if request.method == 'GET':
        # Pre-populate form with existing data
        form.specialty.data = doctor.specialty
        form.location.data = doctor.location
        form.languages.data = doctor.languages
        form.years_of_experience.data = doctor.years_of_experience
        form.education.data = doctor.education
        form.bio.data = doctor.bio
        form.consultation_fee.data = str(doctor.consultation_fee) if doctor.consultation_fee else ""
    
    if form.validate_on_submit():
        doctor.specialty = form.specialty.data
        doctor.location = form.location.data
        doctor.languages = form.languages.data
        doctor.years_of_experience = form.years_of_experience.data
        doctor.education = form.education.data
        doctor.bio = form.bio.data
        
        try:
            doctor.consultation_fee = float(form.consultation_fee.data)
        except ValueError:
            flash('Invalid consultation fee format. Please enter a valid number.', 'danger')
            return render_template('doctor/profile.html', form=form, doctor=doctor)
        
        # Handle profile picture upload
        if form.profile_picture.data:
            profile_pic_path = save_profile_picture(form.profile_picture.data, current_user.id)
            if profile_pic_path:
                doctor.profile_picture = profile_pic_path
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('doctor.profile'))
    
    # Get doctor's availability for display
    availability = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    
    return render_template('doctor/profile.html', form=form, doctor=doctor, availability=availability)

@doctor.route('/availability', methods=['GET', 'POST'])
@login_required
def manage_availability():
    """Manage doctor's available consultation times."""
    if current_user.user_type != UserType.DOCTOR:
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    form = DoctorAvailabilityForm()
    
    if form.validate_on_submit():
        try:
            # Parse time strings to time objects
            start_time_str = form.start_time.data
            end_time_str = form.end_time.data
            
            # Convert to time objects
            start_time_obj = datetime.strptime(start_time_str, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Validate time range
            if start_time_obj >= end_time_obj:
                flash('End time must be after start time.', 'danger')
                return redirect(url_for('doctor.manage_availability'))
            
            # Check for overlapping time slots
            day = form.day_of_week.data
            existing_slots = DoctorAvailability.query.filter_by(
                doctor_id=doctor.id,
                day_of_week=day
            ).all()
            
            for slot in existing_slots:
                if (start_time_obj < slot.end_time and end_time_obj > slot.start_time):
                    flash('This time slot overlaps with an existing one.', 'danger')
                    return redirect(url_for('doctor.manage_availability'))
            
            # Create new availability
            availability = DoctorAvailability(
                doctor_id=doctor.id,
                day_of_week=day,
                start_time=start_time_obj,
                end_time=end_time_obj,
                is_available=True
            )
            
            db.session.add(availability)
            db.session.commit()
            flash('Availability added successfully!', 'success')
            return redirect(url_for('doctor.manage_availability'))
            
        except ValueError as e:
            flash(f'Invalid time format: {str(e)}', 'danger')
    
    # Get all availabilities for display
    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    return render_template('doctor/availability.html', form=form, availabilities=availabilities, days=days)

@doctor.route('/availability/delete/<int:availability_id>', methods=['POST'])
@login_required
def delete_availability(availability_id):
    """Delete a doctor's availability time slot."""
    if current_user.user_type != UserType.DOCTOR:
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    availability = DoctorAvailability.query.get_or_404(availability_id)
    
    # Ensure the doctor can only delete their own availability
    if availability.doctor_id != doctor.id:
        flash('You do not have permission to delete this availability.', 'danger')
        return redirect(url_for('doctor.manage_availability'))
    
    db.session.delete(availability)
    db.session.commit()
    flash('Availability deleted successfully!', 'success')
    return redirect(url_for('doctor.manage_availability'))

# Main routes for doctor search
@main.route('/doctors', methods=['GET', 'POST'])
def find_doctors():
    """Search for doctors by specialty, location, and language."""
    form = DoctorSearchForm()
    doctors = []
    
    if request.method == 'POST' and form.validate():
        # Get search parameters
        specialty = form.specialty.data
        location = form.location.data
        language = form.language.data
        
        # Build query
        query = Doctor.query.filter_by(verification_status=VerificationStatus.VERIFIED)
        
        if specialty:
            query = query.filter(Doctor.specialty.ilike(f'%{specialty}%'))
        
        if location:
            query = query.filter(Doctor.location.ilike(f'%{location}%'))
        
        if language:
            query = query.filter(Doctor.languages.ilike(f'%{language}%'))
        
        doctors = query.all()
    
    # For GET requests or if no search parameters, show all verified doctors
    if not doctors and request.method == 'GET':
        doctors = Doctor.query.filter_by(verification_status=VerificationStatus.VERIFIED).all()
    
    return render_template('main/find_doctors.html', form=form, doctors=doctors)

@main.route('/doctor/<int:doctor_id>')
def doctor_profile(doctor_id):
    """View a doctor's public profile."""
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Only show verified doctors
    if doctor.verification_status != VerificationStatus.VERIFIED:
        flash('This doctor profile is not available.', 'info')
        return redirect(url_for('main.find_doctors'))
    
    # Get doctor's user information
    user = User.query.get(doctor.user_id)
    
    # Get doctor's availability
    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    return render_template('main/doctor_profile.html', doctor=doctor, user=user, availabilities=availabilities, days=days)

# Admin routes
@admin.route('/dashboard')
@login_required
def dashboard():
    # In a real app, you would check if the user is an admin
    return render_template('admin/dashboard.html')

@admin.route('/doctor-verification')
@login_required
def doctor_verification():
    # In a real app, you would check if the user is an admin
    doctors = Doctor.query.filter_by(verification_status=VerificationStatus.PENDING).all()
    return render_template('admin/doctor_verification.html', doctors=doctors)

@admin.route('/verify-doctor/<int:doctor_id>/<action>', methods=['POST'])
@login_required
def verify_doctor(doctor_id, action):
    # In a real app, you would check if the user is an admin
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if action == 'approve':
        doctor.verification_status = VerificationStatus.VERIFIED
        doctor.user.is_active = True
        flash(f'Doctor {doctor.user.first_name} {doctor.user.last_name} has been verified.', 'success')
    elif action == 'reject':
        doctor.verification_status = VerificationStatus.REJECTED
        doctor.verification_notes = request.form.get('rejection_reason', '')
        flash(f'Doctor {doctor.user.first_name} {doctor.user.last_name} has been rejected.', 'info')
    
    db.session.commit()
    return redirect(url_for('admin.doctor_verification'))

# Appointment routes
@main.route('/book-appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def book_appointment(doctor_id):
    """Book an appointment with a doctor."""
    if current_user.user_type != UserType.PATIENT:
        flash('Only patients can book appointments.', 'danger')
        return redirect(url_for('main.index'))
    
    doctor = Doctor.query.get_or_404(doctor_id)
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    
    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    # Check if doctor is verified
    if doctor.verification_status != VerificationStatus.VERIFIED:
        flash('This doctor is not available for appointments.', 'danger')
        return redirect(url_for('main.find_doctors'))
    
    form = AppointmentBookingForm()
    
    # For GET requests, initialize the form
    if request.method == 'GET':
        # Set default date to tomorrow
        tomorrow = datetime.now().date() + datetime.timedelta(days=1)
        form.appointment_date.data = tomorrow
    
    # For POST requests, process the form
    if form.validate_on_submit():
        # Parse the selected time slot
        start_time, end_time = parse_time_slot(form.time_slot.data)
        
        # Check if the slot is still available (prevent double booking)
        appointment_date = form.appointment_date.data
        available_slots = get_available_slots(doctor.id, appointment_date)
        formatted_available_slots = [format_time_slot(slot) for slot in available_slots]
        
        if form.time_slot.data not in formatted_available_slots:
            flash('Sorry, this time slot is no longer available. Please select another.', 'danger')
            return redirect(url_for('main.book_appointment', doctor_id=doctor.id))
        
        # Create the appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            reason=form.reason.data,
            notes=form.notes.data,
            status=AppointmentStatus.CONFIRMED
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Create notifications for both patient and doctor
        patient_message = f"Your appointment with Dr. {doctor.user.last_name} on {appointment_date.strftime('%d/%m/%Y')} at {start_time.strftime('%H:%M')} has been confirmed."
        create_notification(current_user.id, "Appointment Confirmed", patient_message)
        
        doctor_message = f"New appointment with {current_user.first_name} {current_user.last_name} on {appointment_date.strftime('%d/%m/%Y')} at {start_time.strftime('%H:%M')}."
        create_notification(doctor.user_id, "New Appointment", doctor_message)
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.appointments'))
    
    # Get doctor's user information
    doctor_user = User.query.get(doctor.user_id)
    
    return render_template('main/book_appointment.html', form=form, doctor=doctor, doctor_user=doctor_user)

@main.route('/get-available-slots/<int:doctor_id>', methods=['POST'])
@login_required
def get_available_slots_api(doctor_id):
    """API endpoint to get available slots for a specific date."""
    if current_user.user_type != UserType.PATIENT:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get date from request
    date_str = request.form.get('date')
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        # Parse date string to date object
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get available slots
        available_slots = get_available_slots(doctor_id, date_obj)
        
        # Format slots for display
        formatted_slots = [format_time_slot(slot) for slot in available_slots]
        
        return jsonify({'slots': formatted_slots})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@patient.route('/appointments')
@login_required
def appointments():
    """View all patient appointments."""
    if current_user.user_type != UserType.PATIENT:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all appointments for this patient
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.appointment_date.desc()).all()
    
    # Group appointments by status
    upcoming_appointments = []
    past_appointments = []
    cancelled_appointments = []
    
    today = datetime.now().date()
    
    for appointment in appointments:
        if appointment.status == AppointmentStatus.CANCELLED:
            cancelled_appointments.append(appointment)
        elif appointment.appointment_date < today or (appointment.appointment_date == today and appointment.end_time < datetime.now().time()):
            past_appointments.append(appointment)
        else:
            upcoming_appointments.append(appointment)
    
    return render_template('patient/appointments.html', 
                          upcoming_appointments=upcoming_appointments,
                          past_appointments=past_appointments,
                          cancelled_appointments=cancelled_appointments)

@patient.route('/cancel-appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def cancel_appointment(appointment_id):
    """Cancel an appointment."""
    if current_user.user_type != UserType.PATIENT:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Patient profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Ensure the appointment belongs to this patient
    if appointment.patient_id != patient.id:
        flash('You do not have permission to cancel this appointment.', 'danger')
        return redirect(url_for('patient.appointments'))
    
    # Ensure the appointment is not in the past
    if appointment.appointment_date < datetime.now().date():
        flash('Cannot cancel past appointments.', 'danger')
        return redirect(url_for('patient.appointments'))
    
    form = AppointmentCancellationForm()
    
    if form.validate_on_submit():
        # Update appointment status
        appointment.status = AppointmentStatus.CANCELLED
        appointment.notes = appointment.notes + "\n\nCancellation reason: " + form.reason.data if appointment.notes else "Cancellation reason: " + form.reason.data
        db.session.commit()
        
        # Create notifications
        doctor = Doctor.query.get(appointment.doctor_id)
        doctor_user = User.query.get(doctor.user_id)
        
        patient_message = f"Your appointment with Dr. {doctor_user.last_name} on {appointment.appointment_date.strftime('%d/%m/%Y')} has been cancelled."
        create_notification(current_user.id, "Appointment Cancelled", patient_message)
        
        doctor_message = f"Appointment with {current_user.first_name} {current_user.last_name} on {appointment.appointment_date.strftime('%d/%m/%Y')} at {appointment.start_time.strftime('%H:%M')} has been cancelled."
        create_notification(doctor_user.id, "Appointment Cancelled", doctor_message)
        
        flash('Appointment cancelled successfully.', 'success')
        return redirect(url_for('patient.appointments'))
    
    return render_template('patient/cancel_appointment.html', form=form, appointment=appointment)

@doctor.route('/appointments')
@login_required
def doctor_appointments():
    """View all doctor appointments."""
    if current_user.user_type != UserType.DOCTOR:
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all appointments for this doctor
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.appointment_date.desc()).all()
    
    # Group appointments by status and date
    today_appointments = []
    upcoming_appointments = []
    past_appointments = []
    
    today = datetime.now().date()
    
    for appointment in appointments:
        if appointment.status == AppointmentStatus.CANCELLED:
            continue
        elif appointment.appointment_date == today:
            today_appointments.append(appointment)
        elif appointment.appointment_date > today:
            upcoming_appointments.append(appointment)
        else:
            past_appointments.append(appointment)
    
    return render_template('doctor/appointments.html', 
                          today_appointments=today_appointments,
                          upcoming_appointments=upcoming_appointments,
                          past_appointments=past_appointments)

@doctor.route('/complete-appointment/<int:appointment_id>', methods=['POST'])
@login_required
def complete_appointment(appointment_id):
    """Mark an appointment as completed."""
    if current_user.user_type != UserType.DOCTOR:
        flash('Access denied. Doctor privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('main.index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Ensure the appointment belongs to this doctor
    if appointment.doctor_id != doctor.id:
        flash('You do not have permission to update this appointment.', 'danger')
        return redirect(url_for('doctor.doctor_appointments'))
    
    # Update appointment status
    appointment.status = AppointmentStatus.COMPLETED
    db.session.commit()
    
    # Create notification for patient
    patient = Patient.query.get(appointment.patient_id)
    patient_user = User.query.get(patient.user_id)
    
    message = f"Your appointment with Dr. {current_user.last_name} on {appointment.appointment_date.strftime('%d/%m/%Y')} has been marked as completed."
    create_notification(patient_user.id, "Appointment Completed", message)
    
    flash('Appointment marked as completed.', 'success')
    return redirect(url_for('doctor.doctor_appointments'))

@main.route('/notifications')
@login_required
def notifications():
    """View all notifications for the current user."""
    # Get all notifications for this user
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark all as read
    for notification in user_notifications:
        if not notification.is_read:
            notification.is_read = True
    
    db.session.commit()
    
    return render_template('main/notifications.html', notifications=user_notifications)

@main.route('/unread-notifications-count')
@login_required
def unread_notifications_count():
    """Get the count of unread notifications for the current user."""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})
