from app import create_app, bcrypt
from models import db, User, UserType

def create_admin_user(email, password, first_name, last_name, phone):
    """Create an admin user in the database."""
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        existing_admin = User.query.filter_by(email=email).first()
        if existing_admin:
            print(f"Admin user with email {email} already exists.")
            return
        
        # Create new admin user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        admin_user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            user_type=UserType.ADMIN,
            is_active=True,
            email_verified=True,
            phone_verified=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user {email} created successfully!")

if __name__ == "__main__":
    # Default admin credentials
    admin_email = "admin@healthapp.com"
    admin_password = "Admin123!"
    admin_first_name = "Admin"
    admin_last_name = "User"
    admin_phone = "1234567890"
    
    create_admin_user(admin_email, admin_password, admin_first_name, admin_last_name, admin_phone)
    print(f"\nAdmin credentials:")
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
