from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, StaffProfile, Trek, Booking
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change-this-later-to-something-random'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


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


@app.route('/')
def home():
    return render_template('index.html')


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
            is_approved=True
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
            is_approved=False
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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.email = request.form['email']

        if current_user.role == 'staff':
            contact_number = request.form.get('contact_number')
            if current_user.staff_profile:
                current_user.staff_profile.contact_number = contact_number
            else:
                new_profile = StaffProfile(user_id=current_user.id, contact_number=contact_number)
                db.session.add(new_profile)

        db.session.commit()
        flash('Profile updated successfully.', 'success')

        if current_user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        else:
            return redirect(url_for('trekker_dashboard'))

    return render_template('edit_profile.html')


# ---------------- ADMIN ROUTES ----------------

@app.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff', is_rejected=False).count()
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


@app.route('/manage-treks')
@login_required
def manage_treks():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    query = request.args.get('q', '').strip()

    if query:
        if query.isdigit():
            treks = Trek.query.filter(Trek.id == int(query)).all()
        else:
            treks = Trek.query.filter(Trek.name.ilike(f'%{query}%')).all()
    else:
        treks = Trek.query.all()

    return render_template('manage_treks.html', treks=treks)


@app.route('/add-trek', methods=['GET', 'POST'])
@login_required
def add_trek():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        difficulty = request.form['difficulty']
        duration = request.form['duration']
        available_slots = request.form['available_slots']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        assigned_staff_id = request.form.get('assigned_staff_id')
        status = request.form.get('status', 'Pending')

        new_trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration=int(duration) if duration else None,
            available_slots=int(available_slots),
            assigned_staff_id=int(assigned_staff_id) if assigned_staff_id else None,
            status=status,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        )

        db.session.add(new_trek)
        db.session.commit()
        flash('Trek added successfully.', 'success')
        return redirect(url_for('manage_treks'))

    approved_staff = User.query.filter_by(role='staff', is_approved=True).all()
    return render_template('trek_form.html', trek=None, approved_staff=approved_staff)


@app.route('/edit-trek/<int:trek_id>', methods=['GET', 'POST'])
@login_required
def edit_trek(trek_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    trek = db.session.get(Trek, trek_id)
    if not trek:
        flash('Trek not found.', 'danger')
        return redirect(url_for('manage_treks'))

    if request.method == 'POST':
        trek.name = request.form['name']
        trek.location = request.form['location']
        trek.difficulty = request.form['difficulty']
        trek.duration = int(request.form['duration']) if request.form['duration'] else None
        trek.available_slots = int(request.form['available_slots'])

        start_date = request.form['start_date']
        end_date = request.form['end_date']
        trek.start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        trek.end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None

        assigned_staff_id = request.form.get('assigned_staff_id')
        trek.assigned_staff_id = int(assigned_staff_id) if assigned_staff_id else None
        trek.status = request.form.get('status', trek.status)

        if trek.status == 'Completed':
            for booking in trek.bookings:
                if booking.status == 'Booked':
                    booking.status = 'Completed'

        db.session.commit()
        flash('Trek updated successfully.', 'success')
        return redirect(url_for('manage_treks'))

    approved_staff = User.query.filter_by(role='staff', is_approved=True).all()
    return render_template('trek_form.html', trek=trek, approved_staff=approved_staff)


@app.route('/delete-trek/<int:trek_id>', methods=['POST'])
@login_required
def delete_trek(trek_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    trek = db.session.get(Trek, trek_id)
    if trek:
        db.session.delete(trek)
        db.session.commit()
        flash('Trek deleted successfully.', 'info')

    return redirect(url_for('manage_treks'))


@app.route('/manage-users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    query = request.args.get('q', '').strip()

    if query:
        if query.isdigit():
            users = User.query.filter(User.id == int(query), User.role != 'admin').all()
        else:
            users = User.query.filter(
                db.or_(
                    User.name.ilike(f'%{query}%'),
                    User.email.ilike(f'%{query}%')
                ),
                User.role != 'admin'
            ).all()
    else:
        users = User.query.filter(User.role != 'admin').all()

    return render_template('manage_users.html', users=users)


@app.route('/toggle-blacklist/<int:user_id>', methods=['POST'])
@login_required
def toggle_blacklist(user_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    user = db.session.get(User, user_id)
    if user and user.role != 'admin':
        user.is_blacklisted = not user.is_blacklisted
        db.session.commit()
        action = 'blacklisted' if user.is_blacklisted else 'unblacklisted'
        flash(f'{user.name} has been {action}.', 'info')

    return redirect(url_for('manage_users'))


@app.route('/all-bookings')
@login_required
def all_bookings():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    bookings = Booking.query.all()
    return render_template('all_bookings.html', bookings=bookings)


# ---------------- STAFF ROUTES ----------------

@app.route('/staff-dashboard')
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()

    trek_data = []
    for trek in assigned_treks:
        booking_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        trek_data.append({'trek': trek, 'booking_count': booking_count})

    return render_template('staff_dashboard.html', trek_data=trek_data)


@app.route('/manage-trek-staff/<int:trek_id>', methods=['GET', 'POST'])
@login_required
def manage_trek_staff(trek_id):
    if current_user.role != 'staff':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    trek = db.session.get(Trek, trek_id)

    if not trek or trek.assigned_staff_id != current_user.id:
        flash('You are not assigned to this trek.', 'danger')
        return redirect(url_for('staff_dashboard'))

    if request.method == 'POST':
        trek.available_slots = int(request.form['available_slots'])
        trek.status = request.form['status']

        if trek.status == 'Completed':
            for booking in trek.bookings:
                if booking.status == 'Booked':
                    booking.status = 'Completed'

        db.session.commit()
        flash('Trek updated successfully.', 'success')
        return redirect(url_for('manage_trek_staff', trek_id=trek.id))

    bookings = Booking.query.filter_by(trek_id=trek.id).all()
    return render_template('manage_trek_staff.html', trek=trek, bookings=bookings)


# ---------------- TREKKER ROUTES ----------------

@app.route('/trekker-dashboard')
@login_required
def trekker_dashboard():
    if current_user.role != 'trekker':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    difficulty_filter = request.args.get('difficulty', '')
    location_filter = request.args.get('location', '')

    treks_query = Trek.query.filter_by(status='Open')

    if difficulty_filter:
        treks_query = treks_query.filter_by(difficulty=difficulty_filter)
    if location_filter:
        treks_query = treks_query.filter(Trek.location.ilike(f'%{location_filter}%'))

    available_treks = treks_query.all()

    my_bookings = Booking.query.filter_by(user_id=current_user.id).all()
    booked_trek_ids = [b.trek_id for b in my_bookings if b.status == 'Booked']
    cancelled_trek_ids = [b.trek_id for b in my_bookings if b.status == 'Cancelled']

    return render_template(
        'trekker_dashboard.html',
        available_treks=available_treks,
        booked_trek_ids=booked_trek_ids,
        cancelled_trek_ids=cancelled_trek_ids,
        difficulty_filter=difficulty_filter,
        location_filter=location_filter
    )

@app.route('/book-trek/<int:trek_id>', methods=['POST'])
@login_required
def book_trek(trek_id):
    if current_user.role != 'trekker':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    trek = db.session.get(Trek, trek_id)

    if not trek or trek.status != 'Open':
        flash('This trek is not open for booking.', 'danger')
        return redirect(url_for('trekker_dashboard'))

    if trek.available_slots <= 0:
        flash('This trek is fully booked.', 'danger')
        return redirect(url_for('trekker_dashboard'))

    existing_booking = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek.id
    ).first()

    if existing_booking:
        if existing_booking.status == 'Booked':
            flash('You have already booked this trek.', 'warning')
        elif existing_booking.status == 'Cancelled':
            flash('You previously cancelled this trek and cannot book it again.', 'danger')
        return redirect(url_for('trekker_dashboard'))

    new_booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        status='Booked'
    )
    trek.available_slots -= 1

    db.session.add(new_booking)
    db.session.commit()

    flash('Trek booked successfully!', 'success')
    return redirect(url_for('trekker_dashboard'))


@app.route('/my-bookings')
@login_required
def my_bookings():
    if current_user.role != 'trekker':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('my_bookings.html', bookings=bookings)


@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    if current_user.role != 'trekker':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    booking = db.session.get(Booking, booking_id)

    if not booking or booking.user_id != current_user.id:
        flash('Booking not found.', 'danger')
        return redirect(url_for('my_bookings'))

    if booking.status == 'Booked':
        booking.status = 'Cancelled'
        booking.trek.available_slots += 1
        db.session.commit()
        flash('Booking cancelled successfully.', 'info')

    return redirect(url_for('my_bookings'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True)