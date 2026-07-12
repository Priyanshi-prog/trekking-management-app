from flask import Flask, render_template, request, redirect, url_for, flash
from flask import Flask
from models import db, User, StaffProfile, Trek, Booking
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change-this-later-to-something-random'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # redirects here if login required but user not logged in


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('register'))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='trekker',
            is_approved=True  # trekkers don't need approval, only staff does
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/register-staff', methods=['GET', 'POST'])
def register_staff():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        contact_number = request.form['contact_number']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('register_staff'))

        new_staff = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='staff',
            is_approved=False  # requires admin approval
        )
        db.session.add(new_staff)
        db.session.commit()

        profile = StaffProfile(user_id=new_staff.id, contact_number=contact_number)
        db.session.add(profile)
        db.session.commit()

        flash('Registration successful! Please wait for Admin approval before logging in.', 'info')
        return redirect(url_for('home'))

    return render_template('register_staff.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

        if user.is_blacklisted:
            flash('Your account has been blacklisted. Contact Admin.', 'danger')
            return redirect(url_for('login'))

        if user.role == 'staff' and user.is_rejected:
            flash('Your registration was rejected by Admin. Please contact Admin for details.', 'danger')
            return redirect(url_for('login'))

        if user.role == 'staff' and not user.is_approved:
            flash('Your account is pending Admin approval.', 'warning')
            return redirect(url_for('login'))

        login_user(user)
        flash(f'Welcome, {user.name}!', 'success')

        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        else:
            return redirect(url_for('trekker_dashboard'))

    return render_template('login.html')


@app.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    pending_staff = User.query.filter_by(role='staff', is_approved=False, is_rejected=False).all()

    return render_template(
        'admin_dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        pending_staff=pending_staff
    )


@app.route('/approve-staff/<int:staff_id>', methods=['POST'])
@login_required
def approve_staff(staff_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    staff = db.session.get(User, staff_id)
    if staff and staff.role == 'staff':
        staff.is_approved = True
        db.session.commit()
        flash(f'{staff.name} has been approved.', 'success')

    return redirect(url_for('admin_dashboard'))


@app.route('/reject-staff/<int:staff_id>', methods=['POST'])
@login_required
def reject_staff(staff_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    staff = db.session.get(User, staff_id)
    if staff and staff.role == 'staff':
        staff.is_rejected = True
        db.session.commit()
        flash(f'{staff.name} has been rejected.', 'info')

    return redirect(url_for('admin_dashboard'))

@app.route('/staff-dashboard')
@login_required
def staff_dashboard():
    return render_template('dashboard_placeholder.html')


@app.route('/trekker-dashboard')
@login_required
def trekker_dashboard():
    return render_template('dashboard_placeholder.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True)