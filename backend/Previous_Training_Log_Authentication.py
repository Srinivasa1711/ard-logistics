from wsgiref import headers
from apscheduler.util import ZoneInfo
from flask import Flask, request, redirect, url_for, render_template, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import uuid
import json
from sqlalchemy.exc import IntegrityError as SQLAlchemyIntegrityError
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from sqlalchemy.dialects.mssql import NVARCHAR # For Unicode support

# --- SMTP Configuration ---
SMTP_SERVER = 'smtp.office365.com'  # Use your mail server
SMTP_PORT = 587  # Standard port for TLS
SMTP_USERNAME = 'engineer.intern1@ardlogistics.com'  # Replace with admin email
SMTP_PASSWORD = 'Ard0610!'          # Replace with email password

def send_reset_email(to_email, reset_link):
    subject = "ARD Logistics Admin Password Reset"
    body = f"Click the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, please ignore."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
        print(f"Password reset email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

app = Flask(__name__)

server_name = 'ARD7620-PC07\\BARTENDER'
database_name = 'Training_tracker'
driver = '{ODBC Driver 17 for SQL Server}'
connection_string = f"DRIVER={driver};SERVER={server_name};DATABASE={database_name};Trusted_Connection=yes"
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={connection_string}"
db = SQLAlchemy(app)
# --- ODBC Connection Test (with app context) ---
import pyodbc
from sqlalchemy import text
print("Available ODBC drivers:", pyodbc.drivers())
with app.app_context():
    try:
        with db.engine.connect() as connection:
            print("ODBC connection successful:", connection.execute(text("SELECT 1")).scalar())
    except Exception as e:
        print("ODBC connection failed:", e)


import pyodbc
try:
    conn = pyodbc.connect(connection_string)
    print("pyodbc connection successful!")
    conn.close()
except Exception as e:
    print("pyodbc connection failed:", e)
# --- External Company API Configuration ---
# TOKEN_ENDPOINT = 'https://gaamanufacturing.prd.mykronos.com/api/authentication/access_token'
# TEAMS_API_EMPLOYEES_ENDPOINT = "https://gaamanufacturing.prd.mykronos.com/api/authentication/access_token"
# TOKEN_CLIENT_ID = 'KPijaUKjvBfBDNuSiX8hKTVN3g9xC3XA'
# TOKEN_CLIENT_SECRET = '0uDmCz7TpWAPPit6'
# TEAMS_API_BASE_URL = "https://gaamanufacturing.prd.mykronos.com"
# TOKEN_ENDPOINT = f"{TEAMS_API_BASE_URL}/api/v1/commons/persons/apply_read"

TEAMS_API_BASE_URL = "https://gaamanufacturing.prd.mykronos.com/"

# Endpoint to get the access token
TOKEN_ENDPOINT = f"{TEAMS_API_BASE_URL}api/authentication/access_token"

# Endpoint to fetch employee data
TEAMS_API_EMPLOYEES_ENDPOINT = f"{TEAMS_API_BASE_URL}api/v1/commons/persons/apply_read"

TOKEN_CLIENT_ID = 'KPijaUKjvBfBDNuSiX8hKTVN3g9xC3XA'
TOKEN_CLIENT_SECRET = '0uDmCz7TpWAPPit6'

API_USERNAME = 'HR1API'  # <-- REPLACE THIS
API_PASSWORD = 'API1234@ARD' 

# API_KEY_FULL_NAME = 'EMP_COMMON_FULL_NAME_AND_PERSON_NUMBER'  # Updated to match API payload
API_KEY_PERSON_NUMBER = "personNumber"
API_KEY_FIRST_NAME = "firstName"
API_KEY_LAST_NAME = "lastName"

TEAMS_API_AUTH_TOKEN = None

def refresh_api_token():
    """Obtains a new access token from the external API."""
    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            data={
                'grant_type': 'password',
                'username': API_USERNAME,
                'password': API_PASSWORD,
                'client_id': TOKEN_CLIENT_ID,
                'client_secret': TOKEN_CLIENT_SECRET,
                'auth_chain': 'OAuthLdapService'
            }
        )
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data['access_token']
        print("Access token obtained successfully.")
        return access_token
    except Exception as e:
        print(f"Error refreshing API token: {e}")
        return None

def fetch_employee_data_from_api(access_token):
    """Fetches employee data from the external API."""
    url = TEAMS_API_EMPLOYEES_ENDPOINT
    from datetime import datetime, timedelta

    # Define the date range for the current day
    now = datetime.now(ZoneInfo("America/Chicago"))
    end_date = now
    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Try multiple date formats
    date_formats = [
        ("%Y-%m-%dT%H:%M:%S.000Z", "with milliseconds and Z"),
        ("%Y-%m-%dT%H:%M:%SZ", "with Z"),
        ("%Y-%m-%dT%H:%M:%S+00:00", "with timezone offset"),
        ("%Y-%m-%dT%H:%M:%S", "no timezone"),
        ("%Y-%m-%d", "date only")
    ]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    for fmt, desc in date_formats:
        start_date_str = start_date.strftime(fmt)
        end_date_str = end_date.strftime(fmt)
        payload = {
            "where": {
                "dateRange": {
                    "startDateTime": start_date_str,
                    "endDateTime": end_date_str
                }
            }
        }
        print(f"\nTrying date format: {desc} -> {start_date_str} to {end_date_str}")
        print("POST URL:", url)
        print("Headers:", headers)
        print("Payload:", json.dumps(payload))
        response = requests.post(url, json=payload, headers=headers)
        print("Response status:", response.status_code)
        print("Response content-type:", response.headers.get('Content-Type'))
        print("Response text:", response.text)
        if response.status_code == 200:
            try:
                data = response.json()
                print("[DEBUG] Parsed JSON response:", data)
                if isinstance(data, dict) and "employees" in data:
                    return data["employees"]
                return data
            except Exception as e:
                print("[ERROR] Response is not JSON!", e)
                return None
        else:
            print(f"[DEBUG] Format '{desc}' failed with status {response.status_code}")
    print("[ERROR] All date formats failed.")
    return None

def sync_employees_from_api(access_token):
    print("[DEBUG] Entered sync_employees_from_api - CODE VERSION 2025-08-12")
    print("Starting employee sync from API...")
    try:
        api_response = fetch_employee_data_from_api(access_token)
        print(f"[DEBUG] api_response type: {type(api_response)}, length: {len(api_response) if hasattr(api_response, '__len__') else 'N/A'}")
        if isinstance(api_response, list):
            employees = api_response
        else:
            employees = []
        print(f"[DEBUG] Employees list length: {len(employees)}")
        print(f"API returned {len(employees)} employees.")
        print("Raw API response:", api_response)
        print(f"Database connection string: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"[DEBUG] Total employees in API response: {len(employees)}")
        if len(employees) == 0:
            print("[DEBUG] No employees fetched from API! Check API response and payload.")


        added_count = 0
        updated_count = 0
        active_count = 0
        active_status_count = 0
        print("[DEBUG] Listing all userAccountStatus values:")
        for emp_data in employees:
            employee_id = str(emp_data.get("personNumber", "")).strip()
            first_name = str(emp_data.get("firstName", "")).strip()
            last_name = str(emp_data.get("lastName", "")).strip()
            full_name = f"{first_name} {last_name}".strip()
            employment_status = str(emp_data.get("employmentStatus", "")).strip().lower()
            print(f"[DEBUG] Considering employee_id: {employee_id}, employmentStatus: {employment_status}")
            print(f"[DEBUG] Raw employee data: {emp_data}")

            if not employee_id:
                print(f"[DEBUG] Skipping employee with missing ID. Data: {emp_data}")
                continue


            # Removed employmentStatus == 'active' filter; process all employees
            print(f"[DEBUG] Processing employee: {employee_id} - {full_name} (employmentStatus: {employment_status})")
            active_count += 1

            emp_info = EmployeeInfo.query.filter_by(employee_id=employee_id).first()
            print(f"[DEBUG] Query result for employee_id {employee_id}: {emp_info}")
            if not emp_info:
                print(f"[DEBUG] No existing employee found for {employee_id}. Attempting to add.")
                try:
                    new_emp_info = EmployeeInfo(
                        employee_id=employee_id,
                        first_name=first_name,
                        last_name=last_name,
                        full_name=full_name
                    )
                    print(f"[DEBUG] About to add employee to session: {employee_id}, {first_name}, {last_name}, {full_name}")
                    db.session.add(new_emp_info)
                    print(f"[DEBUG] db.session.add called for {employee_id}")
                    added_count += 1
                    print(f"[DEBUG] Added new employee: {employee_id} - {full_name}")
                except Exception as add_err:
                    print(f"[ERROR] Error adding employee {employee_id}: {add_err}")
            else:
                print(f"[DEBUG] Existing employee found for {employee_id}. Attempting to update.")
                try:
                    emp_info.first_name = first_name
                    emp_info.last_name = last_name
                    emp_name = f"{emp_info.first_name} {emp_info.last_name}".strip()
                    emp_info.full_name = emp_name
                    updated_count += 1
                    print(f"[DEBUG] Updated ACTIVE employee: {employee_id} - {emp_name}")
                except Exception as upd_err:
                    print(f"[ERROR] Error updating employee {employee_id}: {upd_err}")
        print(f"[DEBUG] Total ACTIVE employees found: {active_count}")
        print(f"[DEBUG] Total employees with userAccountStatus == 'Active': {active_status_count}")
        print(f"[DEBUG] About to commit. Session new: {db.session.new}, dirty: {db.session.dirty}, deleted: {db.session.deleted}")
        db.session.commit()
        print(f"Successfully synced {len(employees)} employees to EmployeeInfo table.")
        print(f"Added: {added_count}, Updated: {updated_count}")
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Error syncing employees: {e}")

def scheduled_refresh_and_sync():
    """Scheduled job to refresh API token and sync employees."""
    print("[DEBUG] scheduled_refresh_and_sync called - CODE VERSION 2025-08-12")
    with app.app_context():
        global TEAMS_API_AUTH_TOKEN
        TEAMS_API_AUTH_TOKEN = refresh_api_token()
        if TEAMS_API_AUTH_TOKEN:
            sync_employees_from_api(TEAMS_API_AUTH_TOKEN)
        else:
            print("Token refresh failed. Employee sync skipped.")

def start_scheduler():
    """Starts the background scheduler for periodic sync."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_refresh_and_sync, 'interval', minutes=1)
    scheduler.start()
    print("Scheduler started successfully.")

# --- Database Models ---
class LoginLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    login_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(NVARCHAR(100), unique=True, nullable=False) # Updated to NVARCHAR
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False) # Updated to 256
    role = db.Column(db.String(50), nullable=False, default='trainee')
    reset_token = db.Column(db.String(36), unique=True, nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

class EmployeeInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    full_name = db.Column(NVARCHAR(200), nullable=False) # Updated to NVARCHAR

class TraineeFeedbackSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    logged_in_username = db.Column(NVARCHAR(80), nullable=False) # Updated to NVARCHAR
    submission_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    q1_understanding = db.Column(db.String(50), nullable=True)
    q2_clarity = db.Column(db.String(50), nullable=True)
    q3_communication = db.Column(db.String(50), nullable=True)
    q4_time_management = db.Column(db.String(50), nullable=True)
    q5_info_amount = db.Column(db.String(50), nullable=True)
    overall_feedback_text = db.Column(db.Text, nullable=False)

class TrainerFormSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    logged_in_username = db.Column(NVARCHAR(80), nullable=False) # Updated to NVARCHAR
    submission_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    trainer_name = db.Column(NVARCHAR(100), nullable=False) # Updated to NVARCHAR
    trainer_employee_id = db.Column(db.String(50), nullable=False)
    shift = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    process_name = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(100), nullable=False)
    give_feedback = db.Column(db.String(10), nullable=False)
    trainee_name = db.Column(NVARCHAR(100), nullable=False) # Updated to NVARCHAR
    trainee_employee_id = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.String(50), nullable=False)
    end_date = db.Column(db.String(50), nullable=False)

class FeedbackSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trainer_submission_uuid = db.Column(db.String(36), db.ForeignKey('trainer_form_submission.uuid'), nullable=False, unique=True)
    submission_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    skill_level = db.Column(db.Integer, nullable=False)
    struggle_areas = db.Column(db.String(500), nullable=True)
    skill_gap_reasons = db.Column(db.String(500), nullable=True)
    overall_feedback_text = db.Column(db.Text, nullable=False)
    trainer_form = db.relationship('TrainerFormSubmission', backref=db.backref('feedback', uselist=False))

with app.app_context():
    db.create_all()
    start_scheduler()

# --- Routes ---
@app.route('/create_admin', methods=['POST'])
def create_admin():
    email = request.form.get('email', '').strip().lower()
    if not email.endswith('@ardlogistics.com'):
        return jsonify({'success': False, 'message': 'Only @ardlogistics.com emails allowed'}), 400
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    new_user = User(
        full_name=email.split('@')[0],
        employee_id=str(uuid.uuid4()),
        email=email,
        role='admin',
        password_hash=''
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Admin created. Request a password reset.'})

@app.route('/debug/users')
def debug_users():
    users = User.query.all()
    return "<br>".join([
        f"Full Name: {u.full_name}, Employee ID: {u.employee_id}, Role: {u.role}, Email: {u.email}"
        for u in users
    ])

@app.route('/')
def dashboard():
    return render_template('Training_Home_Page.html')

@app.route('/login_page')
def login_page():
    return render_template('Training_Form_Security.html')

@app.route('/login_page_trainer')
def login_page_trainer():
    return render_template('Trainer_Form_Security.html')

@app.route('/admin_login')
def admin_login():
    return render_template('Admin_Form_Security.html')

@app.route('/trainer_login')
def trainer_login():
    return render_template('Training_Form_Security.html')

@app.route('/Training_log_Admin_Dashboard')
def Training_log_Admin_Dashboard():
    if 'logged_in_user_role' not in session or session['logged_in_user_role'] != 'admin':
        return "Access Denied: Admins only.", 403
    return render_template('Training_log_Admin_Dashboard.html')

@app.route('/trainee_feedback_page')
def trainee_feedback_page():
    if 'logged_in_user_role' not in session or session['logged_in_user_role'] != 'trainee':
        return "Access Denied: Trainees only.", 403
    return render_template('Trainee_feedback_page.html')

@app.route('/Trainer_Form')
def Trainer_Form():
    employees = EmployeeInfo.query.with_entities(EmployeeInfo.full_name, EmployeeInfo.employee_id).all()
    return render_template('Trainer_Form.html', employees=employees)

@app.route('/feedback_page/<submission_uuid>')
def feedback_page(submission_uuid):
    if 'logged_in_user_role' not in session or session['logged_in_user_role'] != 'trainer':
        return "Access Denied.", 403
    return render_template('feedback_page.html', submission_uuid=submission_uuid)

@app.route('/training_congrats')
def Training_Congrats():
    return render_template('Training_Congrats.html')

# --- Login Endpoints ---
@app.route('/login', methods=['POST'])
def login():
    """
    Handles Trainee login.
    Checks EmployeeInfo first, then creates a User record on first successful login.
    """
    username_input = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    # 1. Look for a matching employee in the EmployeeInfo table
    emp_info = EmployeeInfo.query.filter_by(full_name=username_input, employee_id=password).first()
    
    if emp_info:
        # 2. Check if a User record already exists for this employee_id
        user = User.query.filter_by(employee_id=emp_info.employee_id).first()
        
        if not user:
            # 3. If it's a first-time login, create a new User record
            try:
                new_user = User(
                    full_name=emp_info.full_name,
                    employee_id=emp_info.employee_id,
                    password_hash=generate_password_hash(emp_info.employee_id),
                    role='trainee'
                )
                db.session.add(new_user)
                db.session.commit()
                user = new_user
                print(f"First-time login: Created new trainee user for {user.full_name}")
            except SQLAlchemyIntegrityError:
                db.session.rollback()
                print(f"Error creating user for {emp_info.full_name}. Trying to fetch existing.")
                user = User.query.filter_by(employee_id=emp_info.employee_id).first()
        
        # 4. Log the user in
        session['logged_in_username'] = user.full_name
        session['logged_in_employee_id'] = user.employee_id
        session['logged_in_user_role'] = user.role
        print(f"Login successful for trainee {user.full_name}")
        return redirect(url_for('trainee_feedback_page'))
    
    print(f"Login failed for username: {username_input}")
    return render_template('Training_Form_Security.html', message="Invalid username or password.")

@app.route('/Trainerlogin', methods=['POST'])
def Trainerlogin():
    """
    Handles Trainer login.
    Checks EmployeeInfo first, then creates a User record on first successful login.
    """
    username_input = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    # 1. Look for a matching employee in the EmployeeInfo table
    emp_info = EmployeeInfo.query.filter_by(full_name=username_input, employee_id=password).first()
    
    if emp_info:
        # 2. Check if a User record already exists for this employee_id
        user = User.query.filter_by(employee_id=emp_info.employee_id).first()
        
        if not user:
            # 3. If it's a first-time login, create a new User record
            try:
                new_user = User(
                    full_name=emp_info.full_name,
                    employee_id=emp_info.employee_id,
                    password_hash=generate_password_hash(emp_info.employee_id),
                    role='trainer' # Set role to trainer for this route
                )
                db.session.add(new_user)
                db.session.commit()
                user = new_user
                print(f"First-time login: Created new trainer user for {user.full_name}")
            except SQLAlchemyIntegrityError:
                db.session.rollback()
                print(f"Error creating user for {emp_info.full_name}. Trying to fetch existing.")
                user = User.query.filter_by(employee_id=emp_info.employee_id).first()
                
        # 4. Log the user in
        session['logged_in_username'] = user.full_name
        session['logged_in_employee_id'] = user.employee_id
        session['logged_in_user_role'] = user.role
        print(f"Login successful for trainer {user.full_name}")
        return redirect(url_for('Trainer_Form'))
    
    print(f"Login failed for username: {username_input}")
    return render_template('Trainer_Form_Security.html', message="Invalid username or password.")

@app.route('/Adminlogin', methods=['POST'])
def Adminlogin():
    email_input = request.form.get('email', '').strip().lower()
    password_input = request.form.get('password', '').strip()
    if not email_input.endswith('@ardlogistics.com'):
        return render_template('Admin_Form_Security.html', message="Only @ardlogistics.com emails are allowed for admin accounts.")
    user = User.query.filter_by(email=email_input, role='admin').first()
    if user and check_password_hash(user.password_hash, password_input):
        session['logged_in_username'] = user.full_name
        session['logged_in_employee_id'] = user.employee_id
        session['logged_in_user_role'] = user.role
        return redirect(url_for('Training_log_Admin_Dashboard'))
    return render_template('Admin_Form_Security.html', message="Invalid email or password.")

def get_user_role():
    if 'logged_in_user_role' in session:
        return session['logged_in_user_role']
    return None

@app.route('/debug/sync_employees', methods=['GET'])
def debug_sync_employees():
    # Refresh the token and sync employees, print results to console
    access_token = refresh_api_token()
    if not access_token:
        return "Failed to get access token", 500
    try:
        sync_employees_from_api(access_token)
        return "Employee sync completed. Check server logs for details.", 200
    except Exception as e:
        return f"Error during sync: {e}", 500    
    
# --- Password Reset Endpoints ---
@app.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():
    message = None
    reset_link_display = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email, role='admin').first()
        if user:
            reset_token = str(uuid.uuid4())
            user.reset_token = reset_token
            user.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            reset_link = url_for('reset_password', token=reset_token, _external=True)
            send_reset_email(email, reset_link)
            message = "If an account with that email exists, a password reset link has been sent to your inbox."
        else:
            message = "If an account with that email exists, a password reset link has been sent to your inbox."
    return render_template('request_password_reset.html', message=message, reset_link=reset_link_display)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    message = None
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiration < datetime.utcnow():
        return render_template('reset_password.html', message="Invalid or expired reset token. Please request a new one.", token=None)
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_new_password = request.form.get('confirm_new_password', '')
        if new_password != confirm_new_password:
            message = "New passwords do not match."
        elif len(new_password) < 8 or not any(char.isdigit() for char in new_password) or not any(char.isalpha() for char in new_password):
            message = "Password must be at least 8 characters long and contain both letters and numbers."
        else:
            user.password_hash = generate_password_hash(new_password)
            user.reset_token = None
            user.reset_token_expiration = None
            db.session.commit()
            return render_template('reset_password.html', message="Password setup is done. You can now go to the login page and enter with your new password.", success=True)
    return render_template('reset_password.html', token=token, message=message)

# --- Form Submission Endpoints ---
@app.route('/submit_trainee_feedback', methods=['POST'])
def submit_trainee_feedback():
    if 'logged_in_username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    try:
        data = request.get_json()
        new_submission = TraineeFeedbackSubmission(
            logged_in_username=session['logged_in_username'],
            q1_understanding=data.get('q1_understanding'),
            q2_clarity=data.get('q2_clarity'),
            q3_communication=data.get('q3_communication'),
            q4_time_management=data.get('q4_time_management'),
            q5_info_amount=data.get('q5_info_amount'),
            overall_feedback_text=data['overall_feedback_text']
        )
        db.session.add(new_submission)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Trainee feedback submitted successfully!'})
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting trainee feedback: {e}")
        return jsonify({'success': False, 'message': f'Error submitting feedback: {str(e)}'}), 500

@app.route('/submit_trainer_form', methods=['POST'])
def submit_trainer_form():
    if 'logged_in_username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    try:
        data = request.get_json()
        new_submission = TrainerFormSubmission(
            logged_in_username=session['logged_in_username'],
            trainer_name=data['trainerName'],
            trainer_employee_id=data['trainerEmployeeId'],
            shift=data['shift'],
            customer_name=data['customerName'],
            process_name=data['processName'],
            zone=data['zone'],
            give_feedback=data['giveFeedback'],
            trainee_name=data['traineeName'],
            trainee_employee_id=data['traineeEmployeeId'],
            start_date=data['startTime'],
            end_date=data['endTime']
        )
        db.session.add(new_submission)
        db.session.commit()
        if data['giveFeedback'] == 'yes':
            return jsonify({
                'success': True,
                'message': 'Trainer form submitted. Redirecting to feedback.',
                'redirect_url': url_for('feedback_page', submission_uuid=new_submission.uuid)
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Trainer form submitted successfully!',
                'redirect_url': url_for('Training_Congrats')
            })
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting trainer form: {e}")
        return jsonify({'success': False, 'message': f'Error submitting form: {str(e)}'}), 500

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'logged_in_username' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    try:
        data = request.get_json()
        trainer_submission_uuid = data.get('trainerFormUuid')
        trainer_form_entry = TrainerFormSubmission.query.filter_by(uuid=trainer_submission_uuid).first()
        if not trainer_form_entry:
            return jsonify({'success': False, 'message': 'Associated trainer form not found.'}), 404
        if trainer_form_entry.feedback:
            return jsonify({'success': False, 'message': 'Feedback for this form already exists.'}), 409
        new_feedback = FeedbackSubmission(
            trainer_submission_uuid=trainer_submission_uuid,
            skill_level=data['skillLevel'],
            struggle_areas=json.dumps(data.get('struggleAreas', [])),
            skill_gap_reasons=json.dumps(data.get('skillGapReason', [])),
            overall_feedback_text=data['overall_feedback_text']
        )
        db.session.add(new_feedback)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Feedback submitted successfully!'})
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting feedback: {e}")
        return jsonify({'success': False, 'message': f'Error submitting feedback: {str(e)}'}), 500

# --- Chart/Analytics Endpoints ---
@app.route('/api/trainee_feedback_trends')
def api_trainee_feedback_trends():
    submissions = TraineeFeedbackSubmission.query.order_by(TraineeFeedbackSubmission.submission_time).all()
    feedback_score_map = {
        'Strongly Agree': 5, 'Agree': 4, 'Neutral': 3, 'Disagree': 2, 'Strongly Disagree': 1,
        'Excellent': 5, 'Good': 4, 'Average': 3, 'Fair': 2, 'Poor': 1,
        'Always': 5, 'Often': 4, 'Sometimes': 3, 'Rarely': 2, 'Never': 1,
        'Just right / Good Balance': 5, 'A bit too much information': 4, 'A bit too little information': 2,
        'Far too much information': 1, 'Far too little information': 1
    }
    daily_averages = {}
    for sub in submissions:
        submission_date = sub.submission_time.strftime('%Y-%m-%d')
        if submission_date not in daily_averages:
            daily_averages[submission_date] = {
                'q1_total': 0, 'q1_count': 0,
                'q2_total': 0, 'q2_count': 0,
                'q3_total': 0, 'q3_count': 0,
                'q4_total': 0, 'q4_count': 0,
                'q5_total': 0, 'q5_count': 0,
            }
        if sub.q1_understanding in feedback_score_map:
            daily_averages[submission_date]['q1_total'] += feedback_score_map[sub.q1_understanding]
            daily_averages[submission_date]['q1_count'] += 1
        if sub.q2_clarity in feedback_score_map:
            daily_averages[submission_date]['q2_total'] += feedback_score_map[sub.q2_clarity]
            daily_averages[submission_date]['q2_count'] += 1
        if sub.q3_communication in feedback_score_map:
            daily_averages[submission_date]['q3_total'] += feedback_score_map[sub.q3_communication]
            daily_averages[submission_date]['q3_count'] += 1
        if sub.q4_time_management in feedback_score_map:
            daily_averages[submission_date]['q4_total'] += feedback_score_map[sub.q4_time_management]
            daily_averages[submission_date]['q4_count'] += 1
        if sub.q5_info_amount in feedback_score_map:
            daily_averages[submission_date]['q5_total'] += feedback_score_map[sub.q5_info_amount]
            daily_averages[submission_date]['q5_count'] += 1
    dates = sorted(daily_averages.keys())
    q_data = {f'Q{i}': [] for i in range(1, 6)}
    for date in dates:
        for i in range(1, 6):
            total = daily_averages[date][f'q{i}_total']
            count = daily_averages[date][f'q{i}_count']
            q_data[f'Q{i}'].append(round(total / count, 2) if count > 0 else 0)
    return jsonify({
        'dates': dates,
        'data': q_data
    })

@app.route('/api/trainer_performance_data')
def api_trainer_performance_data():
    trainer_submissions = TrainerFormSubmission.query.all()
    trainer_skill_levels = {}
    trainer_trainee_skill_details = {}
    for trainer_sub in trainer_submissions:
        trainer_name = trainer_sub.trainer_name
        if trainer_sub.feedback:
            if trainer_name not in trainer_skill_levels:
                trainer_skill_levels[trainer_name] = {'total': 0, 'count': 0}
            trainer_skill_levels[trainer_name]['total'] += trainer_sub.feedback.skill_level
            trainer_skill_levels[trainer_name]['count'] += 1
            if trainer_name not in trainer_trainee_skill_details:
                trainer_trainee_skill_details[trainer_name] = []
            trainer_trainee_skill_details[trainer_name].append({
                'trainee_name': trainer_sub.trainee_name,
                'skill_level': trainer_sub.feedback.skill_level
            })
    final_trainer_skill_level_data = []
    for trainer, data in trainer_skill_levels.items():
        final_trainer_skill_level_data.append({
            'trainer_name': trainer,
            'avg_skill_level': round(data['total'] / data['count'], 2) if data['count'] > 0 else 0,
            'trainee_details': trainer_trainee_skill_details.get(trainer, [])
        })
    return jsonify({
        'avg_skill_level_by_trainer': final_trainer_skill_level_data
    })

@app.route('/api/training_volume_data')
def api_training_volume_data():
    submissions = TrainerFormSubmission.query.all()
    volume_by_shift = {}
    volume_by_zone = {}
    volume_by_process = {}
    volume_by_customer = {}
    for sub in submissions:
        shift = sub.shift
        volume_by_shift[shift] = volume_by_shift.get(shift, 0) + 1
        zone = sub.zone
        if zone:
            volume_by_zone[zone] = volume_by_zone.get(zone, 0) + 1
        process_name = sub.process_name
        if process_name:
            volume_by_process[process_name] = volume_by_process.get(process_name, 0) + 1
        customer_name = sub.customer_name
        if customer_name:
            volume_by_customer[customer_name] = volume_by_customer.get(customer_name, 0) + 1
    return jsonify({
        'volume_by_shift': volume_by_shift,
        'volume_by_zone': volume_by_zone,
        'volume_by_process': volume_by_process,
        'volume_by_customer': volume_by_customer
    })

app.secret_key = os.urandom(24).hex()

if __name__ == '__main__':
    print("[DEBUG] __main__ block entered - CODE VERSION 2025-08-12")
    with app.app_context():
        db.create_all()
        start_scheduler()
    print("[DEBUG] Attempting to start Flask server...")
    app.run(debug=True, use_reloader=False)
    print("[DEBUG] Flask server finished")
