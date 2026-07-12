from flask import Flask
from models import db, User
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def create_default_admin():
    existing_admin = User.query.filter_by(role='admin').first()
    if not existing_admin:
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
        print("Default admin created.")


@app.route('/')
def home():
    return "Trekking Management App is running!"


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True)