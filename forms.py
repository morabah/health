from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Regexp
import phonenumbers
from models import User

class PhoneValidator:
    """Custom validator for phone numbers using the phonenumbers library."""
    def __call__(self, form, field):
        try:
            input_number = phonenumbers.parse(field.data, None)
            if not phonenumbers.is_valid_number(input_number):
                raise ValidationError('Invalid phone number format.')
        except:
            raise ValidationError('Invalid phone number format.')

class RegistrationBaseForm(FlaskForm):
    """Base registration form for both patients and doctors."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), PhoneValidator()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
               message='Password must contain at least one lowercase letter, one uppercase letter, and one number')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or log in.')
    
    def validate_phone(self, phone):
        user = User.query.filter_by(phone=phone.data).first()
        if user:
            raise ValidationError('Phone number already registered. Please use a different phone number or log in.')

class PatientRegistrationForm(RegistrationBaseForm):
    """Registration form specific to patients."""
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    blood_type = SelectField('Blood Type', choices=[
        ('', 'Select Blood Type'),
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ])
    medical_history = TextAreaField('Medical History')
    submit = SubmitField('Register as Patient')

class DoctorRegistrationForm(RegistrationBaseForm):
    """Registration form specific to doctors."""
    specialty = StringField('Specialty', validators=[DataRequired()])
    license_number = StringField('License Number', validators=[DataRequired()])
    years_of_experience = IntegerField('Years of Experience', validators=[DataRequired()])
    education = TextAreaField('Education', validators=[DataRequired()])
    bio = TextAreaField('Professional Bio', validators=[DataRequired()])
    license_document = FileField('License Document', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Only PDF and images are allowed!')
    ])
    certificate = FileField('Medical Certificate', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Only PDF and images are allowed!')
    ])
    terms_agreement = BooleanField('I agree that my credentials will be verified before my account is activated', validators=[DataRequired()])
    submit = SubmitField('Register as Doctor')

class LoginForm(FlaskForm):
    """Login form for all users."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class PhoneVerificationForm(FlaskForm):
    """Form for phone verification."""
    verification_code = StringField('Verification Code', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Verification code must be 6 digits'),
        Regexp(r'^\d{6}$', message='Verification code must be 6 digits')
    ])
    submit = SubmitField('Verify Phone')

class ResendVerificationForm(FlaskForm):
    """Form to resend verification code."""
    submit = SubmitField('Resend Verification Code')

class ForgotPasswordForm(FlaskForm):
    """Form for initiating password reset."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    """Form for resetting password."""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
               message='Password must contain at least one lowercase letter, one uppercase letter, and one number')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')

class DoctorProfileForm(FlaskForm):
    """Form for doctor profile management."""
    specialty = StringField('Specialty', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    languages = StringField('Languages (comma separated)', validators=[DataRequired()])
    years_of_experience = IntegerField('Years of Experience', validators=[DataRequired()])
    education = TextAreaField('Education', validators=[DataRequired()])
    bio = TextAreaField('Professional Bio', validators=[DataRequired()])
    consultation_fee = StringField('Consultation Fee', validators=[DataRequired()])
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only images are allowed!')
    ])
    submit = SubmitField('Update Profile')

class DoctorAvailabilityForm(FlaskForm):
    """Form for doctor availability management."""
    day_of_week = SelectField('Day of Week', choices=[
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ], coerce=int, validators=[DataRequired()])
    start_time = StringField('Start Time (HH:MM)', validators=[
        DataRequired(),
        Regexp(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', message='Time must be in HH:MM format')
    ])
    end_time = StringField('End Time (HH:MM)', validators=[
        DataRequired(),
        Regexp(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', message='Time must be in HH:MM format')
    ])
    submit = SubmitField('Add Availability')

class DoctorSearchForm(FlaskForm):
    """Form for searching doctors."""
    specialty = StringField('Specialty')
    location = StringField('Location')
    language = StringField('Language')
    submit = SubmitField('Search')

class AppointmentBookingForm(FlaskForm):
    """Form for booking appointments."""
    appointment_date = DateField('Appointment Date', validators=[DataRequired()])
    time_slot = SelectField('Time Slot', validators=[DataRequired()])
    reason = TextAreaField('Reason for Visit', validators=[DataRequired()])
    notes = TextAreaField('Additional Notes')
    submit = SubmitField('Book Appointment')

class AppointmentCancellationForm(FlaskForm):
    """Form for cancelling appointments."""
    reason = TextAreaField('Reason for Cancellation', validators=[DataRequired()])
    submit = SubmitField('Cancel Appointment')

class AppointmentRescheduleForm(FlaskForm):
    """Form for rescheduling appointments."""
    appointment_date = DateField('New Appointment Date', validators=[DataRequired()])
    time_slot = SelectField('New Time Slot', validators=[DataRequired()])
    reason = TextAreaField('Reason for Rescheduling', validators=[DataRequired()])
    submit = SubmitField('Reschedule Appointment')
