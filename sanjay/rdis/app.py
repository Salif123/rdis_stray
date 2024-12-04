from flask import Flask, request, render_template, redirect, jsonify, url_for, session
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
currentpatient = "none" 

# Configure Flask app with template and static folder paths
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'm#P52s@ap$V',
    'database': 'sanjay'
}

# Function to get database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None
    
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            logging.info("Database connection successful!")
    except Error as e:
        logging.error(f"Error: '{e}'")
    return connection

def with_db_connection(f):
    def decorated_function(*args, **kwargs):
        connection = create_connection()
        if connection:
            try:
                return f(connection, *args, **kwargs)
            finally:
                connection.close()
    decorated_function.__name__ = f.__name__  
    return decorated_function

# Add logout route
@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    global currentpatient
    currentpatient = "none"
    # Redirect to home page
    return redirect(url_for('home'))

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/patientregister')
def patientregister():
    return render_template('patient.html')

@app.route('/home')
def home():
    return render_template('home.html')

# @app.route('/doctor_dashboard')
# @with_db_connection
# def doctor_dashboard(connection):
#     logging.info("Accessing the doctor dashboard...")
#     try:
#         return render_template('doctor.html')
#     except Exception as e:
#         logging.error(f"Error in doctor_dashboard: {e}")
#         return redirect(url_for('error_page'))

@app.route('/patientlogincheck', methods=['POST'])
def patientlogincheck():
    datanew = request.get_json()
    username = datanew.get("username")
    password = datanew.get("password")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rch_patients WHERE user = %s AND pass = %s", (username, password))
    patient = cursor.fetchone()
    conn.close()
    
    if patient:
        # Add user info to session
        session['user_id'] = patient['patient_id']
        session['user_type'] = 'patient'
        global currentpatient
        currentpatient = patient['patient_id']
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail"})

@app.route("/adminloginpage")
def adminloginpage():
    return render_template("adminlogin.html")

@app.route('/adminlogincheck', methods=['POST'])
def adminlogincheck():
    try:
        datanew = request.get_json()
        username = datanew.get("username")
        password = datanew.get("password")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Use admin_id instead of id
        cursor.execute("SELECT * FROM admin WHERE user = %s AND pass = %s", (username, password))
        admin = cursor.fetchone()
        
        conn.close()
        
        if admin:
            # Use admin_id instead of id
            session['user_id'] = admin['admin_id']
            session['user_type'] = 'admin'
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "fail", "message": "Invalid credentials"})
    
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"status": "fail", "message": "Login failed"})

@app.route("/diseaseloginpage")
def diseaseloginpage():
    return render_template("diseaselogin.html")

@app.route('/diseaselogincheck', methods=['POST'])
def diseaselogincheck():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # Basic input validation
    if not username or not password:
        return jsonify({"status": "fail", "message": "Username and password are required"})

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Consider using parameterized query for security
        cursor.execute("SELECT * FROM disease WHERE user = %s AND pass = %s", (username, password))
        disease_user = cursor.fetchone()
    except Exception as e:
        # Log the error for debugging
        print(f"Database error: {e}")
        return jsonify({"status": "fail", "message": "Database error"})
    finally:
        conn.close()
    
    if disease_user:
        # Store disease user info in session
        session['user_id'] = disease_user['disease_id']
        session['user_type'] = 'disease'
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "fail", "message": "Invalid username or password"})
    
@app.route('/disease')
def disease():
    return render_template("disease.html")

@app.route('/submit_report', methods=['POST'])
def submit_report():
    try:
        patient_name = request.form['patientName']
        age = request.form['age']
        district = request.form['district']
        disease = request.form['disease']
        symptoms = request.form['symptoms']
        onset_date = request.form['onsetDate']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO disease_reports 
            (patient_name, age, district, disease, symptoms, onset_date) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (patient_name, age, district, disease, symptoms, onset_date))
        
        conn.commit()
        conn.close()

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)})


@app.route('/get_disease_reports')
def get_disease_reports():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM disease_reports ORDER BY reported_at DESC")
    reports = cursor.fetchall()
    conn.close()
    return jsonify(reports)

@app.route('/view_disease_reports')
def view_disease_reports():
    return render_template('diseasereort.html')

@app.route('/adminhome')
def adminhome():
    # Check if user is logged in as admin
    if session.get('user_type') != 'admin':
        return redirect(url_for('adminloginpage'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT patient_id, full_name, date_of_birth, contact_number, address, email, patient_status, registration_date FROM rch_patients")
    data = cursor.fetchall()
    conn.close()
    return render_template('admin.html', data=data)

@app.route('/update_patient', methods=['POST'])
def update_patient():
    # Check if user is logged in as admin
    if session.get('user_type') != 'admin':
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    patient_id = data['patient_id']
    full_name = data['full_name']
    date_of_birth = data['date_of_birth']
    contact_number = data['contact_number']
    address = data['address']
    email = data['email']
    patient_status = data['patient_status']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE rch_patients 
        SET full_name=%s, date_of_birth=%s, contact_number=%s, address=%s, email=%s, patient_status=%s 
        WHERE patient_id=%s
        """,
        (full_name, date_of_birth, contact_number, address, email, patient_status, patient_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/patientlogin")
def patientlogin():
    return render_template("patientlogin.html")

@app.route('/submit_patient', methods=['POST'])
def submit_patient():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    
    try:
        form_data = {
            'full_name': request.form['full_name'].strip(),
            'user': request.form['user'].strip(),
            'pass': request.form['pass'],
            'date_of_birth': request.form['date_of_birth'],
            'contact_number': request.form['contact_number'].strip(),
            'address': request.form['address'].strip(),
            'email': request.form['email'].strip().lower(),
            'patient_status': request.form['patient_status']
        }

        sql = """
            INSERT INTO rch_patients 
            (full_name, user, pass, date_of_birth, contact_number, address, email, patient_status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = tuple(form_data.values())
        cursor.execute(sql, values)
        connection.commit()
        
        patient_id = cursor.lastrowid
        session['patient_id'] = patient_id
        
        return redirect(url_for('patientlogin'))

    except Error as e:
        print(e)
        return jsonify({"error": "Database error occurred"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/dashboard')
def dashboard():
    # Check if user is logged in as patient
    if 'user_id' not in session or session.get('user_type') != 'patient':
        return redirect(url_for('patientlogin'))

    connection = get_db_connection()
    if not connection:
        return "Database connection failed", 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        global currentpatient
        cursor.execute("SELECT * FROM rch_patients WHERE patient_id = %s", (currentpatient,))
        patient_data = cursor.fetchone()
        return render_template('dashboard.html', patient=patient_data, datetime=datetime)
    finally:
        cursor.close()
        connection.close()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.route('/error_page')
def error_page():
    return "An error occurred. Please try again later.", 500

if __name__ == '__main__':
    app.run(debug=True)



    #disease

