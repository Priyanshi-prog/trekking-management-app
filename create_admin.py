from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    existing_admin = User.query.filter_by(role='admin').first()

    if existing_admin:
        print("Admin already exists. Skipping creation.")
    else:
        admin = User(
            name='Admin',
            email='admin@trekapp.com',
            password=generate_password_hash('admin123'),
            role='admin',
            is_approved=True,
            is_blacklisted=False
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully.")
        print("Login email: admin@trekapp.com | password: admin123")