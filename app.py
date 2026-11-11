
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

import sqlite3
import os
import subprocess
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY", "change-this-secret-key-before-deployment"
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "hostel.db"
C_FILE = BASE_DIR / "priority.c"
C_PROGRAM = BASE_DIR / "priority.exe" if os.name == "nt" else BASE_DIR / "priority"


# ---------------- DATABASE CONNECTION ----------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------- DATABASE INITIALIZATION ----------------

def init_db():

    DB_PATH.parent.mkdir(exist_ok=True)

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            room TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            urgency TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Create default admin account
    admin = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:
        conn.execute("""
            INSERT INTO users
            (name, username, password, room, role)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Administrator",
            "admin",
            generate_password_hash("admin123"),
            "Office",
            "admin"
        ))

    conn.commit()
    conn.close()


# ---------------- C PROGRAM EXECUTION ----------------

def calculate_priority(category, urgency):

    try:
        if not C_PROGRAM.exists():

            subprocess.run(
                ["gcc", str(C_FILE), "-o", str(C_PROGRAM)],
                check=True,
                capture_output=True,
                text=True
            )

        result = subprocess.run(
            [str(C_PROGRAM), category, urgency],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )

        return result.stdout.strip()

    except (subprocess.SubprocessError, OSError) as error:
        print("C program error:", error)
        return "Medium"


# ---------------- HOME / DASHBOARD ----------------

@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] == "admin":
        return redirect(url_for("admin_dashboard"))

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    conn = get_db()

    total = conn.execute(
        "SELECT COUNT(*) FROM complaints WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()[0]

    pending = conn.execute(
        """SELECT COUNT(*) FROM complaints
        WHERE user_id = ? AND status = 'Pending'""",
        (session["user_id"],)
    ).fetchone()[0]

    resolved = conn.execute(
        """SELECT COUNT(*) FROM complaints
        WHERE user_id = ? AND status = 'Resolved'""",
        (session["user_id"],)
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        pending=pending,
        resolved=resolved
    )


# ---------------- STUDENT REGISTRATION ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]
        room = request.form["room"].strip()

        if not all([name, username, password, room]):
            flash("Please fill in all fields.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
            return redirect(url_for("register"))

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO users
                (name, username, password, room, role)
                VALUES (?, ?, ?, ?, 'student')
            """, (
                name,
                username,
                generate_password_hash(password),
                room
            ))

            conn.commit()
            flash("Registration successful! Please login.", "success")

        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")

        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            return redirect(url_for("home"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ---------------- SUBMIT COMPLAINT ----------------

@app.route("/submit", methods=["GET", "POST"])
def submit_complaint():

    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    if request.method == "POST":

        category = request.form["category"]
        description = request.form["description"].strip()
        urgency = request.form["urgency"]

        categories = [
            "Electricity", "Water", "Wi-Fi",
            "Cleaning", "Other"
        ]

        urgencies = ["Low", "Medium", "High"]

        if category not in categories or urgency not in urgencies:
            flash("Invalid category or urgency.", "error")
            return redirect(url_for("submit_complaint"))

        if not description:
            flash("Please enter a complaint description.", "error")
            return redirect(url_for("submit_complaint"))

        priority = calculate_priority(category, urgency)

        conn = get_db()

        conn.execute("""
            INSERT INTO complaints
            (user_id, category, description, urgency, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            category,
            description,
            urgency,
            priority
        ))

        conn.commit()
        conn.close()

        flash("Complaint submitted successfully!", "success")

        return redirect(url_for("my_complaints"))

    return render_template("submit_complaint.html")


# ---------------- STUDENT COMPLAINT TRACKING ----------------

@app.route("/my-complaints")
def my_complaints():

    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    conn = get_db()

    complaints = conn.execute("""
        SELECT * FROM complaints
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "my_complaints.html",
        complaints=complaints
    )


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    complaints = conn.execute("""
        SELECT complaints.*, users.name, users.room
        FROM complaints
        JOIN users ON complaints.user_id = users.id
        ORDER BY complaints.created_at DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        complaints=complaints
    )


# ---------------- UPDATE COMPLAINT STATUS ----------------

@app.route("/update-status/<int:complaint_id>", methods=["POST"])
def update_status(complaint_id):

    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    status = request.form["status"]

    valid_statuses = [
        "Pending", "In Progress", "Resolved"
    ]

    if status not in valid_statuses:
        flash("Invalid complaint status.", "error")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()

    conn.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ?
    """, (status, complaint_id))

    conn.commit()
    conn.close()

    flash("Complaint status updated.", "success")

    return redirect(url_for("admin_dashboard"))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":

    init_db()

    app.run(debug=True)
