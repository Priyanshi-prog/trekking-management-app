# Trekking Management Application

A web application to manage trekking activities, including treks, staff, and trekker
bookings, built for the Modern Application Development I (MAD-I) course project, May 2026 term.

## Problem Statement

Adventure organizations often rely on spreadsheets, phone calls, or manual coordination
to manage trek approvals, bookings, and trek history. This application digitizes that
workflow for three roles: **Admin**, **Trek Staff**, and **Users (Trekkers)**.

## Tech Stack

- **Backend:** Flask
- **Templating/Frontend:** Jinja2, HTML, CSS, Bootstrap
- **Database:** SQLite (created programmatically via SQLAlchemy)

## Roles

- **Admin**: pre-created superuser; manages treks, staff, users, and bookings.
- **Trek Staff**: registers and logs in (requires admin approval); manages assigned treks.
- **User (Trekker)**: registers, browses/books treks, tracks booking and trek history.

## Project Structure

```
trekking-management-app/
├── app.py
├── models.py
├── create_admin.py
├── init_db.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── register_staff.html
│   ├── admin_dashboard.html
│   ├── manage_treks.html
│   ├── trek_form.html
│   ├── manage_users.html
│   ├── all_bookings.html
│   ├── staff_dashboard.html
│   ├── manage_trek_staff.html
│   ├── trekker_dashboard.html
│   ├── my_bookings.html
│   └── edit_profile.html
├── static/
│   ├── style.css
│   └── mountain-pattern.svg
├── requirements.txt
├── .gitignore
└── README.md
```




## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it and install dependencies: `pip install -r requirements.txt`
4. Run the admin creation script: `python create_admin.py`
5. Run the app: `python app.py`

## Milestones

Progress is tracked via unique Git commit messages per milestone, as required by the
course. See commit history for milestone-wise progress.

## Issues & Resolutions

- **Admin login failed with "Invalid email or password" despite correct credentials**: traced to a missing `return render_template('login.html')` at the end of the `login` route, causing a `TypeError` on GET requests. Fixed by ensuring every branch of the route returns a valid response.
- **`sqlite3.IntegrityError: NOT NULL constraint failed: staff_profiles.user_id` on rejecting a staff account**: deleting a `User` left an orphaned `StaffProfile` since `user_id` was `nullable=False`. Fixed by adding `cascade='all, delete-orphan'` to the `User.staff_profile` relationship so the profile is deleted alongside the user.
- **`ERR_TOO_MANY_REDIRECTS` on `/manage-trek-staff/<id>`**: code meant to run only on `POST` (updating slots/status, marking bookings Completed, redirecting) was not indented inside the `if request.method == 'POST':` block, so it ran on every `GET` request too, causing an infinite redirect loop. Fixed by correcting indentation so the redirect only happens on form submission.
- **Stale SQLite database causing `no such column` errors after adding new model fields**: Flask-SQLAlchemy does not auto-migrate existing tables. Resolved by locating and deleting the old `trekking.db` (found inside the auto-created `instance/` folder) and letting `db.create_all()` regenerate it with the updated schema.
- **Admin dashboard staff count included rejected staff**: refined the query to exclude `is_rejected=True` accounts so the count reflects only active/pending staff.
- **Duplicate bookings and overbooking**: prevented by checking for an existing `Booking` record and available slot count before creating a new booking in the `book_trek` route.
- **Re-booking after cancellation**: initially a cancelled booking could be re-booked since the duplicate check only looked for `status='Booked'`. Fixed by checking for any existing booking record regardless of status, and blocking re-booking if it was previously cancelled.
