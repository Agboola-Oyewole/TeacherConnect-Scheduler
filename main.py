import os
from functools import wraps
from flask_gravatar import Gravatar
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, abort, session
from sqlalchemy import and_
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime, date
import appoint_mail
from appoint_mail import Email
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)
load_dotenv()

# SECRET_KEY='drsvpicgdtbiribs'
# FIRST_EMAIL='emmanueladeyemi472@gmail.com'
EMAIL_ADDRESS = os.getenv('FIRST_EMAIL')
EMAIL_PASSWORD = os.getenv('SECRET_KEY')

mail = Mail(app)
today = datetime.now()
#
# app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # Use SSL
app.config['MAIL_USERNAME'] = EMAIL_ADDRESS
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

SERVICE_ACCOUNT_FILE = 'test-project-405423-6eab057ee9fe.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'bankoleagb@gmail.com'

# Initialize the mail extension
mail.init_app(app)

app.secret_key = os.environ.get('APP_KEY')
app.config['SECURITY_PASSWORD_SALT'] = 'my_precious_two'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_DEFAULT_SENDER'] = EMAIL_ADDRESS
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
# Connect to Database
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
# Connect to Database

year = date.today().strftime("%Y")
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.init_app(app)
is_teacher_yes = False


class Courses(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(db.String(250), nullable=False)
    codes = db.Column(db.String(250), nullable=False)
    season = db.Column(db.String(250), nullable=False)
    card_color = db.Column(db.String(250), nullable=False)
    dashboard_items = relationship('Dashboard', back_populates='dash_post')
    teacher_course = relationship('Teacher', back_populates='courses')


class Dashboard(db.Model):
    __tablename__ = 'dashboard'
    id = db.Column(db.Integer, primary_key=True)
    user = relationship("Users", back_populates="dashboard_items")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    dash_post = relationship('Courses', back_populates='dashboard_items')
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))


class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(250), nullable=False)
    username = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    gender = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    is_teacher = db.Column(db.Boolean, nullable=False, default=False)
    dashboard_items = relationship("Dashboard", back_populates="user")
    user_course = relationship("Teacher", back_populates="user")
    notifications = relationship("Notifications", back_populates="user")


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    availability = db.Column(db.String(250), nullable=False)
    availability_2 = db.Column(db.String(250))
    availability_3 = db.Column(db.String(250))
    courses = relationship('Courses', back_populates='teacher_course')
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    user = relationship('Users', back_populates='user_course')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    available = db.Column(db.Boolean, nullable=False)
    notifications = relationship("Notifications", back_populates="teacher")


class Notifications(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user = relationship("Users", back_populates="notifications")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    teacher = relationship("Teacher", back_populates="notifications")
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    date = db.Column(db.String(250), nullable=False)
    start_time = db.Column(db.String(250), nullable=False)
    end_time = db.Column(db.String(250), nullable=False)
    completed = db.Column(db.Boolean, nullable=False)
    appointment_id = db.Column(db.String(250), nullable=False)
    summary = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


def not_logged(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_teacher != 1:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


def logged(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_teacher == 1:
            return redirect(url_for('teacher_dashboard'))
        return f(*args, **kwargs)

    return decorated_function


def teacher_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_teacher != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


def student_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_teacher == 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


def teacher_logged(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_teacher == 1:
            return redirect(url_for('teacher_dashboard'))
        return f(*args, **kwargs)

    return decorated_function


def format_post(post_time):
    current_date = post_time
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day
    current_hour = current_date.hour
    current_minute = current_date.minute
    current_second = current_date.second
    return datetime(year=current_year, month=current_month, day=current_day, hour=current_hour, minute=current_minute,
                    second=current_second)


def send_calendar_invite(summary, description, start_date, end_date, student_mail, teacher_mail):
    """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "new_credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        event = {
            "summary": summary,
            "location": "17th Avenue North, Nashville, Tennessee.",
            "description": description,
            "colorId": 2,
            "start": {
                "dateTime": start_date,
                "timeZone": "America/Chicago"
            },
            "end": {
                "dateTime": end_date,
                "timeZone": "America/Chicago"
            },
            "attendees": [
                {"email": student_mail},
                {"email": teacher_mail}
            ]
        }

        event = service.events().insert(calendarId="primary", body=event).execute()
        return [event.get('htmlLink'), event.get('id')]

    except HttpError as error:
        print(f"An error occurred: {error}")


def delete_event(event_id):
    """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "new_credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Specify the calendarId (usually 'primary' for the user's primary calendar)
        calendar_id = 'primary'

        # Specify the eventId of the event you want to cancel
        event_id = event_id

        # Call the delete method to cancel the event
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print(f'Event with eventId {event_id} has been canceled.')

    except HttpError as error:
        print(f"An error occurred: {error}")


def update_event(event_id, description, summary, start_date, end_date):
    """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "new_credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Specify the calendarId (usually 'primary' for the user's primary calendar)
        calendar_id = 'primary'

        # Specify the eventId of the event you want to update
        event_id_to_update = event_id

        # Retrieve the existing event details
        existing_event = service.events().get(calendarId=calendar_id, eventId=event_id_to_update).execute()
        if description == '':
            description = existing_event["description"]
        if summary == '':
            summary = existing_event["summary"]
        if start_date == '':
            start_date = existing_event["start"]['dateTime']
        if end_date == '':
            end_date = existing_event["end"]['dateTime']

        # Update the event details
        updated_event = {
            "summary": summary,
            "location": "17th Avenue North, Nashville, Tennessee.",
            "description": description,
            "start": {
                "dateTime": start_date,
                "timeZone": "America/Chicago",
            },
            "end": {
                "dateTime": end_date,
                "timeZone": "America/Chicago",
            },
        }

        # Update the event using the update method
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id_to_update,
            body=updated_event,
        ).execute()
        print(f'Event with eventId {event_id_to_update} has been updated.')

    except HttpError as error:
        print(f"An error occurred: {error}")


@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()


@app.route('/teacher/login', methods=['GET', 'POST'])
@logged
@not_logged
@teacher_logged
def teacher_sign_in():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with app.app_context():
            details = db.session.execute(db.select(Users).where(Users.username == username)).scalar()
            if details:
                if check_password_hash(pwhash=details.password, password=password):
                    login_user(details)
                    if current_user.is_teacher == 0:
                        logout_user()
                        return redirect(url_for('home_sign_in',
                                                message=flash('You are a student, Log In as a Student here instead.',
                                                              'error')))
                    # session['login_successful'] = True
                    return redirect(url_for('teacher_dashboard'))
                else:
                    flash('Password Incorrect, Please try again!', 'error')
            else:
                flash("The account with that username doesn't exist, Please try again!", 'error')

    return render_template("teacher-login.html", logged_in=current_user.is_authenticated, user=current_user)


@app.route('/teacher', methods=['GET', 'POST'])
@logged
@not_logged
@teacher_logged
def teacher_sign_up():
    if request.method == 'POST':
        full_name = request.form.get('fullname')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        repeated_passwords = request.form.get('repeat')
        day_of_the_week = request.form.get('day')
        availability1 = request.form.get('available1')
        availability2 = request.form.get('available2')
        description = request.form.get('description')
        gender = request.form.get('gender')
        if password == repeated_passwords:
            hashed_password = generate_password_hash(password=password, method="pbkdf2:sha256", salt_length=8)

            details = db.session.execute(db.select(Users).where(Users.username == username)).scalar()
            if details:
                flash('This username already exists. Try again.', 'error')
            else:
                details = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
                if details:
                    return redirect(
                        url_for('teacher_sign_in',
                                message=flash('This email already exists. Log In instead.', 'error')))
                else:
                    new_user = Users()
                    new_user.fullname = full_name
                    new_user.email = email
                    new_user.username = username
                    new_user.password = hashed_password
                    new_user.registered_on = format_post(datetime.now())
                    new_user.is_teacher = 1
                    new_user.gender = gender
                    db.session.add(new_user)
                    db.session.commit()

                    already_logged = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
                    if already_logged:
                        login_user(already_logged)

                        new_teacher = Teacher()
                        new_teacher.user_id = current_user.id
                        new_teacher.name = full_name
                        new_teacher.availability = day_of_the_week + ' ' + availability1 + ' - ' + availability2
                        new_teacher.description = description
                        new_teacher.available = 1
                        db.session.add(new_teacher)
                        db.session.commit()
                        return redirect(url_for("add_teacher_course"))

        else:
            flash("That passwords don't match, Please try again!", category='error')

    return render_template("teacher-register.html", logged_in=current_user.is_authenticated,
                           user=current_user)


@app.route('/teacher/yes_available')
@teacher_only
@login_required
def yes_available():
    course_item = db.session.execute(db.select(Teacher).where(Teacher.user_id == current_user.id)).scalar()
    course_item.available = 1
    db.session.commit()
    return redirect(url_for('teacher_dashboard'))


@app.route('/teacher/not_available')
@teacher_only
@login_required
def not_available():
    course_item = db.session.execute(db.select(Teacher).where(Teacher.user_id == current_user.id)).scalar()
    course_item.available = 0
    db.session.commit()
    return redirect(url_for('teacher_dashboard'))


@app.route('/teacher/dashboard', methods=['GET', 'POST'])
@teacher_only
@login_required
def teacher_dashboard():
    course_item = db.session.execute(db.select(Teacher).where(Teacher.user_id == current_user.id)).scalar()
    notifications = db.session.execute(
        db.select(Notifications).where(Notifications.teacher_id == course_item.id)).scalars().all()
    if request.method == 'POST':
        availability1 = request.form.get('available1')
        availability2 = request.form.get('available2')
        description = request.form.get('description')
        day_of_the_week = request.form.get('day')

        availability11 = request.form.get('available11')
        availability21 = request.form.get('available21')
        day_of_the_week1 = request.form.get('day1')

        availability12 = request.form.get('available12')
        availability22 = request.form.get('available22')
        day_of_the_week2 = request.form.get('day2')

        print(request.form)
        check = db.session.query(Teacher).filter(
            and_(Teacher.user_id == current_user.id)
        ).scalar()
        if day_of_the_week == '' or availability1 == '' or availability2 == '':
            pass
        else:
            check.availability = day_of_the_week + ' ' + availability1 + ' - ' + availability2

        if day_of_the_week1 == '' or availability11 == '' or availability21 == '':
            pass
        else:
            check.availability_2 = day_of_the_week1 + ' ' + availability11 + ' - ' + availability21

        if day_of_the_week2 == '' or availability12 == '' or availability22 == '':
            pass
        else:
            check.availability_3 = day_of_the_week2 + ' ' + availability12 + ' - ' + availability22
        if description == '':
            pass
        else:
            check.description = description
        db.session.commit()
        return redirect(url_for('teacher_dashboard'))
    return render_template('teacher-dashboard.html', notifications=notifications, course_item=course_item,
                           logged_in=current_user.is_authenticated,
                           user=current_user)


@app.route('/teacher/appointments', methods=['GET', 'POST'])
@teacher_only
@login_required
def appointments_teacher():
    course_item = db.session.execute(db.select(Teacher).where(Teacher.user_id == current_user.id)).scalar()
    notifications = db.session.execute(
        db.select(Notifications).where(Notifications.teacher_id == course_item.id)).scalars().all()
    appointments_id = request.args.get('appointment_id')
    if request.method == 'POST':
        if request.form.get('start_dates') == '' or request.form.get('end_dates'):
            start_date = ''
            end_date = ''
            summary = ''
            description = ''

            new_notifications = db.session.execute(
                db.select(Notifications).where(Notifications.id == appointments_id)).scalar()
            update_event(event_id=new_notifications.appointment_id, description=description, summary=summary,
                         start_date=start_date, end_date=end_date)
            db.session.commit()
        else:
            start_date = request.form.get('start_dates') + ':00-06:00'
            end_date = request.form.get('end_dates') + ':00-06:00'
            summary = ''
            description = ''

            new_notifications = db.session.execute(
                db.select(Notifications).where(Notifications.id == appointments_id)).scalar()
            update_event(event_id=new_notifications.appointment_id, description=description, summary=summary,
                         start_date=start_date, end_date=end_date)
            new_notifications.date = request.form.get('start_dates').split('T')[0]
            new_notifications.start_time = request.form.get('start_dates').split('T')[1]
            new_notifications.end_time = request.form.get('end_dates').split('T')[1]
            db.session.commit()
        # TODO SEND EMAIL FOR THIS AS WELL
    return render_template('appointments-teachers.html', notifications=notifications,
                           logged_in=current_user.is_authenticated,
                           user=current_user)


@app.route("/completed_teacher")
@login_required
@teacher_only
def completed_teacher():
    appointments_id = request.args.get('appointment_id')
    if current_user.is_authenticated:
        appointment_to_update = Notifications.query.get(appointments_id)
        appointment_to_update.completed = 1
        db.session.commit()
    return redirect(url_for('appointments_teacher'))


@app.route("/cancel/teachers")
@login_required
@teacher_only
def cancel_teacher():
    appointments_id = request.args.get('appointment_id')
    if current_user.is_authenticated:
        appointment_to_update = Notifications.query.get(appointments_id)
        delete_event(appointment_to_update.appointment_id)
        db.session.delete(appointment_to_update)
        db.session.commit()

        with app.app_context():
            appointment_personnel = db.session.execute(
                db.select(Notifications).where(Notifications.id == appointments_id)).scalars().all()
            to_email = os.getenv('FIRST_EMAIL')
            password = os.getenv('SECRET_KEY')
            for people in appointment_personnel:
                message = f'Your appointment with the teacher {people.teacher.name} has been cancelled!'
                appoint_mail.cancel_message(name=people.user.fullname, sender=to_email, message=message,
                                            email_password=password, email=people.user.email)

                message = f'Your appointment with the student {people.user.fullname} has been cancelled!'
                appoint_mail.cancel_message(name=current_user.fullname, sender=to_email, message=message,
                                            email_password=password, email=current_user.email)

    return redirect(url_for('appointments_teacher'))


@app.route('/settings/teacher', methods=['GET', 'POST'])
@login_required
@teacher_only
def settings_teacher():
    course_item = db.session.execute(db.select(Teacher).where(Teacher.user_id == current_user.id)).scalar()
    notifications = db.session.execute(
        db.select(Notifications).where(Notifications.teacher_id == course_item.id)).scalars().all()
    if request.method == 'POST':
        password = request.form.get('current')
        new_password = request.form.get('new')
        repeated = request.form.get('new_again')
        if check_password_hash(pwhash=current_user.password, password=password):
            if new_password == repeated:
                hashed_password = generate_password_hash(password=new_password, method="pbkdf2:sha256", salt_length=8)
                user = db.session.execute(db.select(Users).where(Users.password == current_user.password)).scalar()
                user.password = hashed_password
                db.session.commit()
                flash("Password successfully changed!", 'success')
            else:
                flash("New password doesn't match the repeated password, Please try again!", 'error')
        else:
            flash("Password doesn't match your current password, Please try again!", 'error')

    return render_template('settings-teacher.html', notifications=notifications,
                           logged_in=current_user.is_authenticated, user=current_user)


@app.route('/teacher/add', methods=['GET', 'POST'])
@login_required
@teacher_only
def add_teacher_course():
    courses = Courses.query.all()
    number_of_courses = []

    for item in courses:
        number_of_courses.append(f'checkbox{item.id}')

    if request.method == 'POST':
        selected_checkboxes = []

        # Loop through checkboxes and check if they are selected

        for checkbox_name in number_of_courses:
            if checkbox_name in request.form:
                selected_value = request.form[checkbox_name]
                selected_checkboxes.append(selected_value)

                # Add code here to insert selected_value into your database

        # Print selected values (for demonstration purposes)
        checkbox = selected_checkboxes[0]
        check = db.session.query(Teacher).filter(
            and_(Teacher.user_id == current_user.id)
        ).scalar()
        check.course_id = int(checkbox)
        db.session.commit()
        return redirect(url_for('teacher_dashboard'))
    return render_template('teacher-add-course.html', courses=courses)


@app.route('/teacher/update', methods=['GET', 'POST'])
@login_required
@teacher_only
def update_teacher_course():
    courses = Courses.query.all()
    number_of_courses = []

    for item in courses:
        number_of_courses.append(f'checkbox{item.id}')

    if request.method == 'POST':
        selected_checkboxes = []

        # Loop through checkboxes and check if they are selected

        for checkbox_name in number_of_courses:
            if checkbox_name in request.form:
                selected_value = request.form[checkbox_name]
                selected_checkboxes.append(selected_value)

                # Add code here to insert selected_value into your database

        # Print selected values (for demonstration purposes)
        checkbox = selected_checkboxes[0]
        check = db.session.query(Teacher).filter(
            and_(Teacher.user_id == current_user.id)
        ).scalar()
        check.course_id = int(checkbox)
        db.session.commit()
        return redirect(url_for('teacher_dashboard'))
    return render_template('teacher-update-course.html', courses=courses)


@app.route('/', methods=['GET', 'POST'])
@logged
@not_logged
def home_sign_up():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        repeated_passwords = request.form.get('repeat')
        gender = request.form.get('gender')
        if password == repeated_passwords:
            hashed_password = generate_password_hash(password=password, method="pbkdf2:sha256", salt_length=8)

            details = db.session.execute(db.select(Users).where(Users.username == username)).scalar()
            if details:
                flash('This username already exists. Try again.', 'error')
            else:
                details = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
                if details:
                    return redirect(
                        url_for('home_sign_in', message=flash('This email already exists. Log In instead.', 'error')))
                else:
                    new_user = Users()
                    new_user.fullname = full_name
                    new_user.email = email
                    new_user.username = username
                    new_user.password = hashed_password
                    new_user.registered_on = format_post(datetime.now())
                    new_user.is_teacher = 0
                    new_user.gender = gender
                    db.session.add(new_user)
                    db.session.commit()

                    already_logged = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
                    if already_logged:
                        login_user(already_logged)
                        Email(user=current_user.email, name=current_user.fullname)
                        return redirect(url_for("add_courses"))

        else:
            flash("That passwords don't match, Please try again!", category='error')

    return render_template("register.html", logged_in=current_user.is_authenticated,
                           user=current_user)


@app.route('/login', methods=['GET', 'POST'])
@logged
@not_logged
def home_sign_in():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with app.app_context():
            details = db.session.execute(db.select(Users).where(Users.username == username)).scalar()
            if details:
                if check_password_hash(pwhash=details.password, password=password):
                    login_user(details)
                    if current_user.is_teacher == 1:
                        logout_user()
                        return redirect(url_for('teacher_sign_in',
                                                message=flash('You are a teacher, Log In as a Teacher here instead.',
                                                              'error')))
                    # session['login_successful'] = True
                    return redirect(url_for('dashboard'))
                else:
                    flash('Password Incorrect, Please try again!', 'error')
            else:
                flash("The account with that username doesn't exist, Please try again!", 'error')

    return render_template("login.html", logged_in=current_user.is_authenticated, user=current_user)


@app.route('/send', methods=['POST'])
@login_required
@student_only
def send():
    course_id = request.args.get('course_id')
    teacher_id = request.args.get('teacher_id')
    teacher = db.session.execute(db.select(Teacher).where(Teacher.user_id == teacher_id)).scalar()
    users_name = current_user.fullname
    description = request.form.get('description')
    summary = request.form.get('summary')
    start_date = request.form.get('start_dates') + ':00-06:00'
    end_date = request.form.get('end_dates') + ':00-06:00'
    # Generate Google Calendar invite
    calendar_invite_list = send_calendar_invite(summary=summary, description=description,
                                                start_date=start_date, end_date=end_date,
                                                student_mail=current_user.email, teacher_mail=teacher.user.email)
    calendar_invite = calendar_invite_list[0]
    calendar_id = calendar_invite_list[1]
    #
    # Attach the Google Calendar invite to the email

    to_email = os.getenv('FIRST_EMAIL')
    password = os.getenv('SECRET_KEY')
    message = f'Student {current_user.fullname} has requested to have an appointment with you'
    appoint_mail.contact_message(name=users_name, sender=to_email, user=current_user.email,
                                 message=message, email_password=password, email=teacher.user.email,
                                 calendar_invite=calendar_invite)

    new_notifications = Notifications()
    new_notifications.user_id = current_user.id
    new_notifications.teacher_id = teacher.id
    new_notifications.date = request.form.get('start_dates').split('T')[0]
    new_notifications.start_time = request.form.get('start_dates').split('T')[1]
    new_notifications.end_time = request.form.get('end_dates').split('T')[1]
    new_notifications.summary = summary
    new_notifications.description = description
    new_notifications.completed = 0
    new_notifications.appointment_id = calendar_id
    db.session.add(new_notifications)
    db.session.commit()

    return redirect(url_for('contacts', course_id=course_id, show_toast='true'))


@app.route('/dashboard')
@login_required
@student_only
def dashboard():
    course_item = db.session.execute(db.select(Dashboard).where(Dashboard.user_id == current_user.id)).scalars().all()
    current_user_username = db.session.execute(
        db.select(Dashboard).where(Dashboard.user_id == current_user.id)).scalar()
    notifications = db.session.execute(
        db.select(Notifications).where(Notifications.user_id == current_user.id)).scalars().all()
    return render_template('dashboard.html', notifications=notifications, current_user_username=current_user_username,
                           course_item=course_item,
                           logged_in=current_user.is_authenticated,
                           user=current_user)


@app.route('/appointments', methods=['GET', 'POST'])
@student_only
@login_required
def appointments_students():
    appointments_id = request.args.get('appointment_id')
    notifications = db.session.execute(
        db.select(Notifications).where(Notifications.user_id == current_user.id)).scalars().all()
    if request.method == 'POST':
        if request.form.get('start_dates') == '' or request.form.get('end_dates'):
            start_date = ''
            end_date = ''
            summary = request.form.get('summary')
            description = request.form.get('description')

            new_notifications = db.session.execute(
                db.select(Notifications).where(Notifications.id == appointments_id)).scalar()
            update_event(event_id=new_notifications.appointment_id, description=description, summary=summary,
                         start_date=start_date, end_date=end_date)
            new_notifications.summary = summary
            new_notifications.description = description
            db.session.commit()
        else:
            start_date = request.form.get('start_dates') + ':00-06:00'
            end_date = request.form.get('end_dates') + ':00-06:00'
            summary = request.form.get('summary')
            description = request.form.get('description')

            new_notifications = db.session.execute(
                db.select(Notifications).where(Notifications.id == appointments_id)).scalar()
            update_event(event_id=new_notifications.appointment_id, description=description, summary=summary,
                         start_date=start_date, end_date=end_date)
            new_notifications.summary = summary
            new_notifications.description = description
            new_notifications.date = request.form.get('start_dates').split('T')[0]
            new_notifications.start_time = request.form.get('start_dates').split('T')[1]
            new_notifications.end_time = request.form.get('end_dates').split('T')[1]
            db.session.commit()
    return render_template('appointments-students.html', notifications=notifications,
                           logged_in=current_user.is_authenticated,
                           user=current_user)


@app.route("/completed")
@login_required
@student_only
def completed():
    appointments_id = request.args.get('appointment_id')
    if current_user.is_authenticated:
        appointment_to_update = Notifications.query.get(appointments_id)
        appointment_to_update.completed = 1
        db.session.commit()
    return redirect(url_for('appointments_students'))


@app.route("/cancel")
@login_required
@student_only
def cancel():
    appointments_id = request.args.get('appointment_id')
    if current_user.is_authenticated:

        appointment_to_update = Notifications.query.get(appointments_id)
        delete_event(appointment_to_update.appointment_id)
        db.session.delete(appointment_to_update)
        db.session.commit()

        with app.app_context():
            appointment_personnel = db.session.execute(
                db.select(Notifications).where(Notifications.id == appointments_id)).scalars().all()
            to_email = os.getenv('FIRST_EMAIL')
            password = os.getenv('SECRET_KEY')
            for people in appointment_personnel:
                message = f'Your appointment with the student {people.user.fullname} has been cancelled!'

                appoint_mail.cancel_message(name=people.teacher.name, sender=to_email, message=message,
                                            email_password=password, email=people.teacher.user.email)

                message = f'Your appointment with the teacher {people.teacher.name} has been cancelled!'
                appoint_mail.cancel_message(name=current_user.fullname, sender=to_email, message=message,
                                            email_password=password, email=current_user.email)


    return redirect(url_for('appointments_students'))


@app.route('/add', methods=['GET', 'POST'])
@login_required
@student_only
def add_courses():
    courses = Courses.query.all()
    number_of_courses = []

    for item in courses:
        number_of_courses.append(f'checkbox{item.id}')

    if request.method == 'POST':
        selected_checkboxes = []

        # Loop through checkboxes and check if they are selected

        for checkbox_name in number_of_courses:
            if checkbox_name in request.form:
                selected_value = request.form[checkbox_name]
                selected_checkboxes.append(selected_value)

                # Add code here to insert selected_value into your database

        # Print selected values (for demonstration purposes)
        for checkbox in selected_checkboxes:
            check = db.session.query(Dashboard).filter(
                and_(Dashboard.user_id == current_user.id, Dashboard.course_id == int(checkbox))
            ).scalar()
            if not check:
                new_course = Dashboard()
                new_course.user_id = current_user.id  # Assuming current_user.id is the user_id
                new_course.course_id = int(checkbox)
                db.session.add(new_course)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add-courses.html', courses=courses)


@app.route("/delete_course/<int:course_id>")
@login_required
@student_only
def delete_course(course_id):
    if current_user.is_authenticated:
        post_to_delete = Dashboard.query.get(course_id)
        db.session.delete(post_to_delete)
        db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
@student_only
def settings():
    notifications = db.session.execute(
        db.select(Notifications).where(Notifications.user_id == current_user.id)).scalars().all()
    if request.method == 'POST':
        password = request.form.get('current')
        new_password = request.form.get('new')
        repeated = request.form.get('new_again')
        if check_password_hash(pwhash=current_user.password, password=password):
            if new_password == repeated:
                hashed_password = generate_password_hash(password=new_password, method="pbkdf2:sha256", salt_length=8)
                user = db.session.execute(db.select(Users).where(Users.password == current_user.password)).scalar()
                user.password = hashed_password
                db.session.commit()
                flash("Password successfully changed!", 'success')
            else:
                flash("New password doesn't match the repeated password, Please try again!", 'error')
        else:
            flash("Password doesn't match your current password, Please try again!", 'error')

    return render_template('settings.html', notifications=notifications, logged_in=current_user.is_authenticated,
                           user=current_user)


@app.route('/contacts')
@login_required
@student_only
def contacts():
    course_id = request.args.get('course_id')
    show_toast = request.args.get('show_toast')
    if show_toast == 'true':
        # Set a session or temporary flag to indicate that the toast should be shown
        session['show_toast'] = True
    teachers = db.session.execute(
        db.select(Teacher).where(Teacher.course_id == course_id)).scalars()
    teacher_sum = db.session.execute(
        db.select(Teacher).where(Teacher.course_id == course_id)).scalars().all()
    notifications = db.session.execute(
        db.select(Notifications).where(Notifications.user_id == current_user.id)).scalars().all()
    course_name = db.session.execute(
        db.select(Courses).where(Courses.id == course_id)).scalar()
    return render_template('contacts.html', teacher_sum=teacher_sum, course_name=course_name,
                           notifications=notifications, teachers=teachers, user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home_sign_up'))


if __name__ == '__main__':
    app.run(debug=True)
