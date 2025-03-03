from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient, Doctor, UserType, VerificationStatus, VerificationDocument
from forms import (PatientRegistrationForm, DoctorRegistrationForm, LoginForm, 
                  PhoneVerificationForm, ResendVerificationForm, ForgotPasswordForm, 
                  ResetPasswordForm)
from utils import (generate_verification_code, generate_verification_token, 
                  send_verification_email, send_verification_sms, 
                  send_password_reset_email, save_verification_document)
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
        abort(403)
    
    return render_template('doctor/dashboard.html')

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
