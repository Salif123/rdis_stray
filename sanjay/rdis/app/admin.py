from flask import Flask, render_template, jsonify, request
import mysql.connector

app = Flask(__name__)

# MySQL Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="yourusername",
        password="yourpassword",
        database="yourdatabase"
    )

# Display data
@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT patient_id, full_name, date_of_birth, contact_number, address, email, patient_status, registration_date FROM rch_patients")
    data = cursor.fetchall()
    conn.close()
    return render_template('admin.html', data=data)

# Update patient data
@app.route('/update_patient', methods=['POST'])
def update_patient():
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

if __name__ == '__main__':
    app.run(debug=True)
