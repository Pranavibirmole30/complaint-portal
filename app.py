from flask import Flask, render_template, request, redirect, session
import sqlite3, os

app = Flask(__name__)
from flask import send_from_directory

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

app.secret_key = "secret"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database connection
def get_db():
    return sqlite3.connect("database.db")

# Create tables
with get_db() as db:
    db.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT
    )
    """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS complaints(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        description TEXT,
        location TEXT,
        status TEXT,
        image TEXT
    )
    """)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        db.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                   (name,email,password))
        db.commit()
        return redirect('/login')
    return render_template("register.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=? AND password=?",
                          (email,password)).fetchone()

        if user:
            session['user'] = email
            return redirect('/dashboard')
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template("dashboard.html")

@app.route('/submit', methods=['GET','POST'])
def submit():
    if request.method == 'POST':
        category = request.form['category']
        description = request.form['description']
        location = request.form['location']
        image = request.files['image']

        image_name = image.filename
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

        db = get_db()
        db.execute("""
        INSERT INTO complaints VALUES (NULL,?,?,?,?,?)
        """,(category,description,location,'Pending',image_name))
        db.commit()
        return redirect('/view')
    return render_template("submit.html")

@app.route('/view')
def view():
    db = get_db()
    data = db.execute("SELECT * FROM complaints").fetchall()
    return render_template("view.html", complaints=data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# --- ADD ADMIN LOGIC HERE ---

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Simple check for admin credentials
        if (email == "piyush123@gmail.com" and password == "piyush123") or \
            (email == "pranavi123@gmail.com" and password == "pranavi123"):
            session['admin'] = email
            return redirect('/admin_dashboard')
    return render_template("admin_login.html")

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')

    db = get_db()

    complaints = db.execute("SELECT * FROM complaints").fetchall()

    total = db.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'").fetchone()[0]
    resolved = db.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'").fetchone()[0]

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        total=total,
        pending=pending,
        resolved=resolved
    )
@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    if 'admin' not in session:
        return redirect('/admin')
    new_status = request.form['status']
    db = get_db()
    db.execute("UPDATE complaints SET status=? WHERE id=?", (new_status, id))
    db.commit()
    return redirect('/admin_dashboard')
@app.route('/delete_complaint/<int:id>', methods=['POST'])
def delete_complaint(id):

    if 'admin' not in session:
        return redirect('/admin')

    db = get_db()

    db.execute("DELETE FROM complaints WHERE id=?", (id,))
    db.commit()

    return redirect('/admin_dashboard')

# --- END OF ADMIN LOGIC ---

#if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
