from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user, login_user, logout_user
from models import db, User, Patient, Doctor, UserType, VerificationStatus, VerificationDocument
from werkzeug.security import generate_password_hash
import os
import signal
import sys
import subprocess
from datetime import datetime
from flask_bcrypt import Bcrypt

# Create bcrypt instance
bcrypt = Bcrypt()

admin_panel = Blueprint('admin_panel', __name__, url_prefix='/admin_panel')

def admin_required(f):
    """Decorator to check if user is an admin."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Check if user is an admin
        if current_user.user_type == UserType.ADMIN:
            return f(*args, **kwargs)
            
        # Check if user is a doctor with admin privileges
        if current_user.user_type == UserType.DOCTOR:
            doctor = Doctor.query.filter_by(user_id=current_user.id).first()
            if doctor and doctor.specialty == "Administration":
                return f(*args, **kwargs)
        
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Preserve the original function name and docstring
    decorated_function.__name__ = f.__name__
    decorated_function.__doc__ = f.__doc__
    return decorated_function

@admin_panel.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    # If user is already logged in and is an admin, redirect to dashboard
    if current_user.is_authenticated:
        if current_user.user_type == UserType.ADMIN or (
            current_user.user_type == UserType.DOCTOR and 
            Doctor.query.filter_by(user_id=current_user.id).first() and 
            Doctor.query.filter_by(user_id=current_user.id).first().specialty == "Administration"
        ):
            return redirect(url_for('admin_panel.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Try to verify password directly
            try:
                # Check if the password hash is valid
                if bcrypt.check_password_hash(user.password_hash, password):
                    # Check if user is an admin or a doctor with admin privileges
                    if user.user_type == UserType.ADMIN or (
                        user.user_type == UserType.DOCTOR and 
                        Doctor.query.filter_by(user_id=user.id).first() and 
                        Doctor.query.filter_by(user_id=user.id).first().specialty == "Administration"
                    ):
                        login_user(user)
                        return redirect(url_for('admin_panel.dashboard'))
                    else:
                        flash('Access denied. Admin privileges required.', 'danger')
                else:
                    flash('Login failed. Please check your email and password.', 'danger')
            except ValueError:
                # If there's an issue with the password hash, show error
                flash('Login failed. Invalid password format.', 'danger')
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    
    return render_template('admin/login.html')

@admin_panel.route('/logout')
@login_required
def logout():
    """Admin logout."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_panel.login'))

@admin_panel.route('/')
@login_required
@admin_required
def dashboard():
    """Admin panel dashboard."""
    user_count = User.query.count()
    patient_count = Patient.query.count()
    doctor_count = Doctor.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get pending doctor verifications
    pending_doctors = db.session.query(User, Doctor).join(Doctor).filter(
        User.user_type == UserType.DOCTOR,
        Doctor.verification_status == VerificationStatus.PENDING
    ).all()
    
    return render_template(
        'admin/dashboard.html',
        user_count=user_count,
        patient_count=patient_count,
        doctor_count=doctor_count,
        recent_users=recent_users,
        pending_doctors=pending_doctors
    )

@admin_panel.route('/users')
@login_required
@admin_required
def users():
    """List all users."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/users.html', users=users)

@admin_panel.route('/patients')
@login_required
@admin_required
def patients():
    """List all patients."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    patients_data = db.session.query(User, Patient).join(Patient).filter(
        User.user_type == UserType.PATIENT
    ).order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/patients.html', patients=patients_data)

@admin_panel.route('/doctors')
@login_required
@admin_required
def doctors():
    """List all doctors."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    doctors_data = db.session.query(User, Doctor).join(Doctor).filter(
        User.user_type == UserType.DOCTOR
    ).order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin/doctors.html', doctors=doctors_data)

@admin_panel.route('/user/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """View user details."""
    user = User.query.get_or_404(user_id)
    
    # Get associated patient or doctor record
    profile = None
    if user.user_type == UserType.PATIENT:
        profile = Patient.query.filter_by(user_id=user.id).first()
    elif user.user_type == UserType.DOCTOR:
        profile = Doctor.query.filter_by(user_id=user.id).first()
    
    return render_template('admin/user_detail.html', user=user, profile=profile)

@admin_panel.route('/user/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user."""
    if request.method == 'POST':
        # Extract form data
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        user_type = request.form.get('user_type')
        
        # Validate data
        if not all([email, password, first_name, last_name, phone, user_type]):
            flash('All fields are required', 'danger')
            return redirect(url_for('admin_panel.create_user'))
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('admin_panel.create_user'))
        
        # Create user
        user = User(
            email=email,
            password_hash=bcrypt.generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            user_type=UserType(user_type),
            email_verified=True,
            phone_verified=True,
            is_active=True
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create associated profile
        if user.user_type == UserType.PATIENT:
            patient = Patient(
                user_id=user.id,
                gender=request.form.get('gender', 'other'),
                date_of_birth=datetime.strptime(request.form.get('date_of_birth', '2000-01-01'), '%Y-%m-%d'),
                blood_type=request.form.get('blood_type', 'O+'),
                medical_history=request.form.get('medical_history', '')
            )
            db.session.add(patient)
            
        elif user.user_type == UserType.DOCTOR:
            doctor = Doctor(
                user_id=user.id,
                specialty=request.form.get('specialty', ''),
                license_number=request.form.get('license_number', ''),
                years_of_experience=int(request.form.get('years_of_experience', 0)),
                education=request.form.get('education', ''),
                bio=request.form.get('bio', ''),
                verification_status=VerificationStatus.VERIFIED
            )
            db.session.add(doctor)
        
        db.session.commit()
        flash('User created successfully', 'success')
        return redirect(url_for('admin_panel.users'))
    
    return render_template('admin/create_user.html')

@admin_panel.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit an existing user."""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Update user data
        user.email = request.form.get('email')
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        user.is_active = 'is_active' in request.form
        user.email_verified = 'email_verified' in request.form
        user.phone_verified = 'phone_verified' in request.form
        
        # Update password if provided
        if request.form.get('password'):
            user.password_hash = bcrypt.generate_password_hash(request.form.get('password'))
        
        # Update profile data
        if user.user_type == UserType.PATIENT:
            patient = Patient.query.filter_by(user_id=user.id).first()
            if patient:
                patient.gender = request.form.get('gender')
                patient.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d')
                patient.blood_type = request.form.get('blood_type')
                patient.medical_history = request.form.get('medical_history')
                
        elif user.user_type == UserType.DOCTOR:
            doctor = Doctor.query.filter_by(user_id=user.id).first()
            if doctor:
                doctor.specialty = request.form.get('specialty')
                doctor.license_number = request.form.get('license_number')
                doctor.years_of_experience = int(request.form.get('years_of_experience', 0))
                doctor.education = request.form.get('education')
                doctor.bio = request.form.get('bio')
                doctor.verification_status = VerificationStatus(request.form.get('verification_status'))
        
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin_panel.user_detail', user_id=user.id))
    
    # Get associated profile
    profile = None
    if user.user_type == UserType.PATIENT:
        profile = Patient.query.filter_by(user_id=user.id).first()
    elif user.user_type == UserType.DOCTOR:
        profile = Doctor.query.filter_by(user_id=user.id).first()
    
    return render_template('admin/edit_user.html', user=user, profile=profile)

@admin_panel.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin_panel.users'))
    
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
                # Delete the actual file
                if doc.file_path and os.path.exists(doc.file_path):
                    os.remove(doc.file_path)
                db.session.delete(doc)
            db.session.delete(doctor)
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin_panel.users'))

@admin_panel.route('/verify-doctor/<int:doctor_id>/<action>', methods=['POST'])
@login_required
@admin_required
def verify_doctor(doctor_id, action):
    """Verify or reject a doctor."""
    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get(doctor.user_id)
    
    if action == 'approve':
        doctor.verification_status = VerificationStatus.VERIFIED
        user.is_active = True
        flash('Doctor approved successfully', 'success')
    elif action == 'reject':
        doctor.verification_status = VerificationStatus.REJECTED
        doctor.verification_notes = request.form.get('rejection_reason', '')
        flash('Doctor rejected', 'info')
    
    db.session.commit()
    return redirect(url_for('admin_panel.doctors'))

# API endpoints for AJAX operations
@admin_panel.route('/api/users')
@login_required
@admin_required
def api_users():
    """API endpoint to get users."""
    users = User.query.all()
    result = []
    
    for user in users:
        result.append({
            'id': user.id,
            'email': user.email,
            'name': f"{user.first_name} {user.last_name}",
            'user_type': user.user_type.name,
            'is_active': user.is_active,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(result)

@admin_panel.route('/api/activate-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def api_activate_user(user_id):
    """API endpoint to activate a user."""
    user = User.query.get_or_404(user_id)
    user.is_active = True
    user.email_verified = True
    user.phone_verified = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User activated successfully'})

@admin_panel.route('/restart', methods=['GET'])
@login_required
@admin_required
def restart_page():
    """Display the restart server page"""
    return render_template('admin/restart.html')

@admin_panel.route('/restart-server', methods=['POST'])
@login_required
@admin_required
def restart_server():
    """Restart the Flask server"""
    try:
        # Get the current process ID
        pid = os.getpid()
        
        # Start a new process that will restart the server
        # This uses a separate Python process to avoid killing the current request
        restart_command = f"""
import os
import time
import signal
import subprocess

# Wait a moment to allow the current request to complete
time.sleep(1)

# Kill the Flask process
try:
    os.kill({pid}, signal.SIGTERM)
except:
    pass

# Start the server again
subprocess.Popen(['python3', 'app.py'], 
                 cwd='{os.getcwd()}', 
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE)
"""
        
        # Execute the restart command in a separate process
        subprocess.Popen([sys.executable, '-c', restart_command],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
        
        flash('Server restart initiated. Please wait a moment...', 'info')
        return redirect(url_for('main.index'))
    except Exception as e:
        flash(f'Error restarting server: {str(e)}', 'danger')
        return redirect(url_for('admin_panel.restart_page'))
