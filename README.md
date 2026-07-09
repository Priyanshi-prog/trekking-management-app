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
├── config.py
├── create_admin.py
├── templates/
├── static/
├── requirements.txt
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

(Log issues encountered during development and how they were resolved here.)
