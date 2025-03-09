from app import create_app, db
from models import User

app = create_app()

with app.app_context():
    email = "doctor1@example.com"
    user = User.query.filter_by(email=email).first()
    if user:
        print(f"User found: {user.email}")
        print(f"Password hash: {user.password_hash}")
        print(f"Hash length: {len(user.password_hash)}")
        print(f"Hash format: {'pbkdf2:' in user.password_hash}")
    else:
        print(f"No user found with email: {email}")
