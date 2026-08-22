from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='dayflow_user',
        password='dayflow123',
        database='dayflow',
        cursorclass=pymysql.cursors.Cursor
    )

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "employee")

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO employees (name, email, password, role) VALUES (%s, %s, %s, %s)",
        (name, email, password, role)
    )
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return jsonify({"id": new_id, "name": name, "email": email, "role": role}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role FROM employees WHERE email=%s AND password=%s", (email, password))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return jsonify({"id": user[0], "name": user[1], "email": user[2], "role": user[3]})
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route('/leaves', methods=['POST'])
def apply_leave():
    data = request.get_json()
    employee_id = data.get("employee_id")
    leave_type = data.get("leave_type")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    remarks = data.get("remarks", "")

    if not employee_id or not leave_type or not start_date or not end_date:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, remarks, status) VALUES (%s,%s,%s,%s,%s,%s)",
        (employee_id, leave_type, start_date, end_date, remarks, "pending")
    )
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return jsonify({"id": new_id, "status": "pending"}), 201

@app.route('/leaves', methods=['GET'])
def get_leaves():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT l.id, e.name, l.leave_type, l.start_date, l.end_date, l.remarks, l.status
        FROM leave_requests l
        JOIN employees e ON l.employee_id = e.id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    leaves = []
    for row in rows:
        leaves.append({
            "id": row[0], "employee_name": row[1], "leave_type": row[2],
            "start_date": str(row[3]), "end_date": str(row[4]),
            "remarks": row[5], "status": row[6]
        })
    return jsonify(leaves)

@app.route('/leaves/employee/<int:employee_id>', methods=['GET'])
def get_employee_leaves(employee_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, leave_type, start_date, end_date, remarks, status FROM leave_requests WHERE employee_id=%s", (employee_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    leaves = []
    for row in rows:
        leaves.append({
            "id": row[0], "leave_type": row[1], "start_date": str(row[2]),
            "end_date": str(row[3]), "remarks": row[4], "status": row[5]
        })
    return jsonify(leaves)

@app.route('/leaves/<int:leave_id>', methods=['PUT'])
def update_leave_status(leave_id):
    data = request.get_json()
    new_status = data.get("status")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE leave_requests SET status=%s WHERE id=%s", (new_status, leave_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": leave_id, "status": new_status})

@app.route('/employees', methods=['GET'])
def get_employees():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role FROM employees")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    employees = [{"id": r[0], "name": r[1], "email": r[2], "role": r[3]} for r in rows]
    return jsonify(employees)

@app.route('/leaves/pending', methods=['GET'])
def get_pending_leaves():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT l.id, e.name, l.leave_type, l.start_date, l.end_date, l.remarks, l.status
        FROM leave_requests l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'pending'
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    leaves = [{
        "id": r[0], "employee_name": r[1], "leave_type": r[2],
        "start_date": str(r[3]), "end_date": str(r[4]),
        "remarks": r[5], "status": r[6]
    } for r in rows]
    return jsonify(leaves)
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Dayflow backend is running"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)