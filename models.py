from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'staff', 'trekker'
    is_approved = db.Column(db.Boolean, default=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', lazy=True)
    treks_assigned = db.relationship('Trek', backref='assigned_staff', lazy=True)


class StaffProfile(db.Model):
    __tablename__ = 'staff_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contact_number = db.Column(db.String(20))


class Trek(db.Model):
    __tablename__ = 'treks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150))
    difficulty = db.Column(db.String(20))
    duration = db.Column(db.Integer)
    available_slots = db.Column(db.Integer, default=0)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='Pending')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    bookings = db.relationship('Booking', backref='trek', lazy=True)


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Booked')