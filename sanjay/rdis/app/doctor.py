import logging
from flask import Flask, render_template, redirect, url_for
import mysql.connector
from mysql.connector import Error

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Database connection details
db_config = {
    'host': 'localhost', #change to 127.0.0.1
    'user': 'root', 
    'password': '',  # Update with your DB password: m#P52s@ap$V
    'database': 'salif'  # Update with your DB name: test
}

# Database connection
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            logging.info("Database connection successful!")
    except Error as e:
        logging.error(f"Error: '{e}'")
    return connection

# Decorator to manage database connection
def with_db_connection(f):
    def decorated_function(*args, **kwargs):
        connection = create_connection()
        if connection:
            try:
                return f(connection, *args, **kwargs)
            finally:
                connection.close()
    return decorated_function


@app.route('/doctor_dashboard')
@with_db_connection
def doctor_dashboard(connection):
    logging.info("Accessing the doctor dashboard...")
    try:
        pending_appointments = AppointmentManager.get_pending_appointments(connection)
        approved_appointments = AppointmentManager.get_approved_appointments(connection)
        logging.info(f"Pending appointments: {pending_appointments}")
        logging.info(f"Approved appointments: {approved_appointments}")
        print("Entered Database and Fetched")
        return render_template('doctor.html', pending_appointments=pending_appointments,
                               approved_appointments=approved_appointments)
      
    except Exception as e:
        logging.error(f"Error in doctor_dashboard: {e}")
        return redirect(url_for('error_page'))

@app.route('/error_page')
def error_page():
    return "An error occurred. Please try again later.", 500

class AppointmentManager:

    @staticmethod
    def get_pending_appointments(connection) -> list:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                a.appointment_id,
                p.patient_id,
                p.full_name,
                p.contact_number,
                p.email,
                a.appointment_status,
                DATE_FORMAT(a.requested_date, '%Y-%m-%d') as requested_date,
                TIME_FORMAT(a.appointment_time, '%H:%i') as appointment_time,
                COALESCE(mh.recent_diagnosis, 'None') as recent_diagnosis
            FROM appointments a
            JOIN rch_patients p ON a.patient_id = p.patient_id
            LEFT JOIN (
                SELECT patient_id, condition_name as recent_diagnosis
                FROM rch_medical_history
                WHERE is_active = TRUE
                ORDER BY diagnosis_date DESC
                LIMIT 1
            ) mh ON p.patient_id = mh.patient_id
            WHERE a.appointment_status = 'pending'
            ORDER BY a.requested_date ASC, a.appointment_time ASC"""
        )
        appointments = cursor.fetchall()
        print(appointments)
        cursor.close()
        return appointments

    @staticmethod
    def get_approved_appointments(connection) -> list:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                a.appointment_id,
                p.full_name,
                p.contact_number,
                p.email,
                DATE_FORMAT(a.requested_date, '%Y-%m-%d') as appointment_date,
                TIME_FORMAT(a.appointment_time, '%H:%i') as appointment_time
            FROM appointments a
            JOIN rch_patients p ON a.patient_id = p.patient_id
            WHERE a.appointment_status = 'approved'
            ORDER BY a.requested_date DESC, a.appointment_time ASC
            LIMIT 10"""
        )
        approved_appointments = cursor.fetchall()
        print(approved_appointments)
        cursor.close()
        return approved_appointments

    @staticmethod
    def approve_appointment(connection, appointment_id):
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE appointments 
            SET 
                appointment_status = 'approved',
                updated_at = NOW()
            WHERE appointment_id = %s AND appointment_status = 'pending'"""
        , (appointment_id,))
        connection.commit()
        cursor.close()

    @staticmethod
    def reject_appointment(connection, appointment_id):
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE appointments 
            SET 
                appointment_status = 'rejected',
                updated_at = NOW()
            WHERE appointment_id = %s AND appointment_status = 'pending'
        """, (appointment_id,))
        connection.commit()
        cursor.close()
    #logout
    @app.route('/logout')
    def logout():
    # Logout logic here
        return redirect(url_for('login'))  # Redirect to login page after logout
    

if __name__ == '__main__':
    app.run(debug=True)
