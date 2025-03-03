from app import create_app, bcrypt
from models import db, User, UserType

def fix_admin_password():
    """Fix the admin user password hash."""
    app = create_app()
    with app.app_context():
        # Find admin user
        admin_user = User.query.filter_by(email="admin@healthapp.com").first()
        
        if not admin_user:
            print("Admin user not found!")
            return
        
        # Update password with proper hash
        new_password = "Admin123!"
        admin_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        
        db.session.commit()
        print(f"Admin password reset successfully to: {new_password}")
        print(f"Email: {admin_user.email}")

if __name__ == "__main__":
    fix_admin_password()
