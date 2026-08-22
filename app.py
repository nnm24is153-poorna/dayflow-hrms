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

    cur.execute("""
        SELECT id, name, email, role, phone, address, department, joining_date
        FROM employees
        WHERE email=%s AND password=%s
    """, (email, password))

    user = cur.fetchone()

    cur.close()
    conn.close()

    if user:
        return jsonify({
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "role": user[3],
            "phone": user[4],
            "address": user[5],
            "department": user[6],
            "joining_date": str(user[7]) if user[7] else None
        })
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

@app.route('/profile/<int:employee_id>', methods=['PUT'])
def update_profile(employee_id):
    data = request.get_json()
    phone = data.get("phone")
    address = data.get("address")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE employees SET phone=%s, address=%s WHERE id=%s",
        (phone, address, employee_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": employee_id, "phone": phone, "address": address})
    # GET all employees with today's status
@app.route('/employees', methods=['GET'])
def get_employees():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role FROM employees")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    employees = []
    for row in rows:
        employees.append({"id": row[0], "name": row[1], "email": row[2], "role": row[3]})
    return jsonify(employees)

# CHECK IN
@app.route('/attendance/checkin', methods=['POST'])
def check_in():
    data = request.get_json()
    employee_id = data.get("employee_id")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO attendance (employee_id, date, check_in, status) VALUES (%s, CURDATE(), CURTIME(), 'present')",
        (employee_id,)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Checked in"}), 201

# CHECK OUT
@app.route('/attendance/checkout', methods=['PUT'])
def check_out():
    data = request.get_json()
    employee_id = data.get("employee_id")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE attendance SET check_out=CURTIME() WHERE employee_id=%s AND date=CURDATE()",
        (employee_id,)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Checked out"})

# GET today's attendance status for all employees (for status dots)
@app.route('/attendance/today', methods=['GET'])
def attendance_today():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT employee_id, status FROM attendance WHERE date=CURDATE()")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    status_map = {row[0]: row[1] for row in rows}
    return jsonify(status_map)

    # GET all attendance for a specific date (Admin view)
@app.route('/attendance/date/<date>', methods=['GET'])
def attendance_by_date(date):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.name, a.check_in, a.check_out, a.status
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.date = %s
    """, (date,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    records = []
    for row in rows:
        records.append({
            "name": row[0],
            "check_in": str(row[1]) if row[1] else None,
            "check_out": str(row[2]) if row[2] else None,
            "status": row[3]
        })
    return jsonify(records)

# GET one employee's attendance history (Employee view)
@app.route('/attendance/employee/<int:employee_id>', methods=['GET'])
def attendance_by_employee(employee_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT date, check_in, check_out, status
        FROM attendance WHERE employee_id = %s ORDER BY date DESC
    """, (employee_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    records = []
    for row in rows:
        records.append({
            "date": str(row[0]),
            "check_in": str(row[1]) if row[1] else None,
            "check_out": str(row[2]) if row[2] else None,
            "status": row[3]
        })
    return jsonify(records)

    # GET payroll for one employee (Employee view - read only)
@app.route('/payroll/<int:employee_id>', methods=['GET'])
def get_payroll(employee_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT basic_salary, allowances, deductions, net_salary, month, year FROM payroll WHERE employee_id=%s ORDER BY year DESC, month DESC LIMIT 1", (employee_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return jsonify({
            "basic_salary": float(row[0]) if row[0] else 0,
            "allowances": float(row[1]) if row[1] else 0,
            "deductions": float(row[2]) if row[2] else 0,
            "net_salary": float(row[3]) if row[3] else 0,
            "month": row[4], "year": row[5]
        })
    return jsonify({"basic_salary": 0, "allowances": 0, "deductions": 0, "net_salary": 0, "month": None, "year": None})

# GET all employees' payroll (Admin view)
@app.route('/payroll', methods=['GET'])
def get_all_payroll():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.employee_id, e.name, p.basic_salary, p.allowances, p.deductions, p.net_salary, p.month, p.year
        FROM payroll p JOIN employees e ON p.employee_id = e.id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "employee_id": row[0], "name": row[1],
            "basic_salary": float(row[2]) if row[2] else 0,
            "allowances": float(row[3]) if row[3] else 0,
            "deductions": float(row[4]) if row[4] else 0,
            "net_salary": float(row[5]) if row[5] else 0,
            "month": row[6], "year": row[7]
        })
    return jsonify(result)

# Admin: Add/Update payroll for an employee
@app.route('/payroll/<int:employee_id>', methods=['POST'])
def set_payroll(employee_id):
    data = request.get_json()
    basic = float(data.get("basic_salary", 0))
    allowances = float(data.get("allowances", 0))
    deductions = float(data.get("deductions", 0))
    month = data.get("month")
    year = data.get("year")

    net_salary = basic + allowances - deductions

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO payroll (employee_id, basic_salary, allowances, deductions, net_salary, month, year) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (employee_id, basic, allowances, deductions, net_salary, month, year)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"employee_id": employee_id, "net_salary": net_salary}), 201

    # GET all departments (with employee count)
@app.route('/departments', methods=['GET'])
def get_departments():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.id, d.name, d.description, COUNT(e.id) as employee_count
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.id
        GROUP BY d.id, d.name, d.description
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    departments = []
    for row in rows:
        departments.append({
            "id": row[0], "name": row[1], "description": row[2], "employee_count": row[3]
        })
    return jsonify(departments)

# GET employees in one department
@app.route('/departments/<int:dept_id>/employees', methods=['GET'])
def get_department_employees(dept_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role FROM employees WHERE department_id=%s", (dept_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    employees = []
    for row in rows:
        employees.append({"id": row[0], "name": row[1], "email": row[2], "role": row[3]})
    return jsonify(employees)

# Admin: Add a new department
@app.route('/departments', methods=['POST'])
def add_department():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description", "")

    if not name:
        return jsonify({"error": "Department name required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO departments (name, description) VALUES (%s, %s)", (name, description))
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return jsonify({"id": new_id, "name": name, "description": description}), 201

# Admin: Edit a department
@app.route('/departments/<int:dept_id>', methods=['PUT'])
def update_department(dept_id):
    data = request.get_json()
    name = data.get("name")
    description = data.get("description", "")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE departments SET name=%s, description=%s WHERE id=%s", (name, description, dept_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"id": dept_id, "name": name, "description": description})

# Admin: Assign an employee to a department
@app.route('/employees/<int:employee_id>/department', methods=['PUT'])
def assign_department(employee_id):
    data = request.get_json()
    department_id = data.get("department_id")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE employees SET department_id=%s WHERE id=%s", (department_id, employee_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"employee_id": employee_id, "department_id": department_id})

if __name__ == '__main__':
    app.run(debug=True, port=5000)