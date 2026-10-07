# =================================================================
# DEV NIG LIMITED - DRILL BITS INVENTORY MANAGEMENT SYSTEM
# Standard Version - Part 1 to Part 3 Complete
# Developer: IT Department
# Date: 2026
# =================================================================

import sqlite3
import os
import io
import csv
from flask import Flask, render_template_string, request, redirect, url_for, session, Response
from functools import wraps

# Flask App Setup
app = Flask(__name__)
app.secret_key = 'dev_nig_2026_secret_key_standard'

# --- PART 1: DATABASE SETUP ---

def get_db_connection():
    conn = sqlite3.connect('dev_nig.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Users table for login
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Bits inventory table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS bits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_no TEXT NOT NULL,
            bit_type TEXT NOT NULL,
            size TEXT,
            manufacturer TEXT,
            cost REAL,
            purchase_date TEXT,
            location TEXT,
            status TEXT,
            client_name TEXT,
            rig_name TEXT,
            hours_run INTEGER
        )
    ''')
    # Default admin user
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?,?)", ('admin', 'admin123'))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- PART 2 & 3: UI TEMPLATE (STANDARD DESIGN) ---

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DEV NIG LTD - Bit Inventory System</title>
    <style>
        *{margin:0; padding:0; box-sizing:border-box;}
        body{font-family:'Segoe UI', Arial, sans-serif; background:#f4f6f9; color:#333;}
       .header{background:#0f2c52; color:white; padding:18px; text-align:center; border-bottom:4px solid #ffcc00;}
       .header h2{letter-spacing:0.5px;}
       .container{max-width:1150px; margin:auto; padding:10px;}
       .card{background:white; margin:20px 0; padding:25px; border-radius:10px; box-shadow:0 3px 10px rgba(0,0,0,0.08);}
       .btn{padding:10px 18px; border:none; border-radius:6px; cursor:pointer; color:white; text-decoration:none; display:inline-block; font-weight:600; font-size:14px;}
       .btn-blue{background:#0f2c52;}.btn-blue:hover{background:#143a6b;}
       .btn-red{background:#c0392b;}.btn-dark{background:#2c3e50;}
        input, select{padding:11px; border:1px solid #ddd; border-radius:6px; width:100%; background:#fcfcfc;}
        input:focus, select:focus{outline:none; border-color:#0f2c52; background:white;}
        label{font-size:13px; font-weight:600; color:#0f2c52; margin-bottom:4px; display:block;}
        table{width:100%; border-collapse:collapse; margin-top:15px;}
        th{background:#0f2c52; color:white; padding:12px 10px; text-align:left; font-size:13px; text-transform:uppercase;}
        td{padding:10px; font-size:14px; border-bottom:1px solid #eee;}
        tr:hover{background:#f8f9fa;}
       .badge{padding:4px 10px; border-radius:15px; font-size:12px; font-weight:600;}
       .badge-store{background:#e3f2fd; color:#1565c0;}
    </style>
</head>
<body>
    <div class="header">
        <h2>DEV NIG LIMITED</h2>
        <p style="font-size:14px; letter-spacing:1px; opacity:0.9;">DRILL BITS INVENTORY MANAGEMENT SYSTEM</p>
    </div>

    <div class="container">
        {% if page == 'login' %}
        <div class="card" style="max-width:420px; margin:60px auto; border-top:5px solid #ffcc00;">
            <h3 style="text-align:center; color:#0f2c52; margin-bottom:5px;">STAFF LOGIN</h3>
            <p style="text-align:center; font-size:13px; color:#777; margin-bottom:20px;">Authorized Personnel Only</p>
            <form method="POST">
                <div style="margin-bottom:15px;"><label>Username</label><input name="username" placeholder="Enter username" required></div>
                <div style="margin-bottom:20px;"><label>Password</label><input name="password" type="password" placeholder="Enter password" required></div>
                <button class="btn btn-blue" style="width:100%; padding:13px; font-size:15px;">LOGIN TO SYSTEM</button>
            </form>
            {% if error %}<p style="color:#c0392b; text-align:center; margin-top:15px; font-weight:600; background:#fdecea; padding:10px; border-radius:5px;">{{ error }}</p>{% endif %}
            <div style="text-align:center; margin-top:20px; padding:12px; background:#f4f6f9; border-radius:6px; font-size:13px;">
                Default Login<br><b>Username:</b> admin | <b>Password:</b> admin123
            </div>
        </div>

        {% elif page == 'dashboard' %}
        <div style="display:flex; justify-content:space-between; align-items:center; margin:20px 5px;">
            <div style="font-size:14px;">Welcome, <b>{{ session.username }}</b> |
                <a href="/export" class="btn btn-dark" style="font-size:12px; padding:6px 12px;">📥 Export CSV</a>
            </div>
            <a href="/logout" class="btn btn-red" style="font-size:13px;">Logout</a>
        </div>

        <div class="card">
            <h3 style="color:#0f2c52; margin-bottom:15px; border-left:4px solid #ffcc00; padding-left:12px;">Add New Drill Bit
                <span style="float:right;"><input type="text" id="search" placeholder="🔍 Search inventory..." onkeyup="searchTable()" style="width:220px; padding:8px;"></span>
            </h3>
            <form method="POST" action="/add" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; margin-top:15px;">
                <div><label>Serial No *</label><input name="serial_no" placeholder="e.g. PDC-001" required></div>
                <div><label>Bit Type *</label><select name="bit_type" required><option value="">-- Select Type --</option><option>PDC</option><option>Roller Cone</option><option>Tricone</option><option>Diamond</option><option>Bi-Center</option></select></div>
                <div><label>Size</label><input name="size" placeholder='e.g. 12 1/4"'></div>
                <div><label>Manufacturer</label><input name="manufacturer" placeholder="e.g. Smith, Baker"></div>
                <div><label>Cost (NGN)</label><input name="cost" type="number" step="0.01" placeholder="0.00"></div>
                <div><label>Purchase Date</label><input name="purchase_date" type="date"></div>
                <div><label>Location</label><select name="location"><option>Store</option><option>Rig Site</option><option>Workshop</option><option>In Transit</option><option>Damaged Store</option></select></div>
                <div><label>Status</label><select name="status"><option>New</option><option>Used</option><option>Damaged</option><option>Under Repair</option><option>Deployed</option></select></div>
                <div><label>Hours Run</label><input name="hours_run" type="number" placeholder="0"></div>
                <div><label>Client Name</label><input name="client_name" placeholder="client Name"></div>
                <div><label>Rig Name</label><input name="rig_name" placeholder="Rig Name"></div>
                <div style="grid-column:span 1; display:flex; align-items:end;"><button class="btn btn-blue" style="width:100%; padding:12px;">+ ADD BIT TO INVENTORY</button></div>
            </form>
        </div>

        <div class="card">
            <h3 style="color:#0f2c52; margin-bottom:5px; border-left:4px solid #ffcc00; padding-left:12px;">Current Inventory</h3>
            <p style="font-size:13px; color:#666; margin-bottom:15px; padding-left:16px;">Total Bits: <b>{{ bits|length }}</b> | Company Standard Tracking</p>
            <div style="overflow-x:auto;">
                <table id="bitTable">
                    <tr><th>Serial No</th><th>Type</th><th>Size</th><th>Location</th><th>Status</th><th>client / Rig</th><th>Action</th></tr>
                    {% for bit in bits %}
                    <tr>
                        <td style="font-weight:700; color:#0f2c52;">{{ bit.serial_no }}</td>
                        <td>{{ bit.bit_type }}</td>
                        <td>{{ bit.size }}</td>
                        <td><span class="badge badge-store">{{ bit.location }}</span></td>
                        <td>{{ bit.status }}</td>
                        <td style="font-size:12px;">{{ bit.client_name }}<br><span style="color:#777;">{{ bit.rig_name }}</span></td>
                        <td><a href="/delete/{{ bit.id }}" style="color:#c0392b; font-weight:700; text-decoration:none;" onclick="return confirm('Are you sure you want to delete {{ bit.serial_no }}?')">Delete</a></td>
                    </tr>
                    {% else %}
                    <tr><td colspan="7" style="text-align:center; padding:30px; color:#888;">No bits in inventory yet. Add your first bit above.</td></tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <script>
        function searchTable(){
            var input=document.getElementById("search"), filter=input.value.toUpperCase();
            var table=document.getElementById("bitTable"), tr=table.getElementsByTagName("tr");
            for(var i=1;i<tr.length;i++){
                var txt=tr[i].textContent||tr[i].innerText;
                tr[i].style.display=txt.toUpperCase().indexOf(filter)>-1?"":"none";
            }
        }
        </script>
        {% endif %}
    </div>
    <div style="text-align:center; padding:20px; font-size:12px; color:#888;">
        © 2026 DEV NIG LIMITED | Standard Inventory System v3.0
    </div>
</body>
</html>
"""

# --- PART 3: ROUTES (FUNCTIONALITY) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid Username or Password'
    return render_template_string(TEMPLATE, page='login', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    conn = get_db_connection()
    bits = conn.execute('SELECT * FROM bits ORDER BY id DESC').fetchall()
    conn.close()
    return render_template_string(TEMPLATE, page='dashboard', bits=bits)

@app.route('/add', methods=['POST'])
@login_required
def add_bit():
    d = request.form
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO bits (serial_no, bit_type, size, manufacturer, cost, purchase_date, location, status, client_name, rig_name, hours_run)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    ''', (d['serial_no'], d['bit_type'], d['size'], d['manufacturer'], d['cost'] or 0, d['purchase_date'], d['location'], d['status'], d['client_name'], d['rig_name'], d['hours_run'] or 0))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:id>')
@login_required
def delete_bit(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM bits WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/export')
@login_required
def export():
    conn = get_db_connection()
    bits = conn.execute('SELECT * FROM bits ORDER BY id DESC').fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Serial_No', 'Bit_Type', 'Size', 'Manufacturer', 'Cost', 'Purchase_Date', 'Location', 'Status', 'client_Name', 'Rig_Name', 'Hours_Run'])
    for b in bits:
        writer.writerow([b['id'], b['serial_no'], b['bit_type'], b['size'], b['manufacturer'], b['cost'], b['purchase_date'], b['location'], b['status'], b['client_name'], b['rig_name'], b['hours_run']])
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=DEV_NIG_STANDARD_INVENTORY.csv'})

# --- RUN APP ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)