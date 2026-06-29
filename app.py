from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "abc12345"


def get_db_connection():
    """
    Create and return a new MySQL connection.
    Edit host/user/password/database if yours are different.
    """
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Chinni@421",
        database="notes_management"
    )
    return conn


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def home():
    return render_template("about.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Your message has been submitted successfully.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s OR username=%s", (email, username))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username or email already exists.", "warning")
            cursor.close()
            conn.close()
            return redirect(url_for("register"))

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful.", "success")
            return redirect(url_for("viewnotes"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/forgot-password")
def forgot_password():
    return redirect(url_for("set_new_password"))


@app.route("/set-new-password", methods=["GET", "POST"])
def set_new_password():
    if request.method == "POST":
        email = request.form["email"].strip()
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("set_new_password"))

        hashed_password = generate_password_hash(new_password)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            flash("Email not found.", "warning")
            cursor.close()
            conn.close()
            return redirect(url_for("set_new_password"))

        cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_password, email))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Password updated successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("setnewpassword.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/addnote", methods=["GET", "POST"])
@login_required
def addnote():
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO notes (title, content, user_id) VALUES (%s, %s, %s)",
            (title, content, session["user_id"])
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Note added successfully.", "success")
        return redirect(url_for("viewnotes"))

    return render_template("addnote.html")                   


@app.route("/viewnotes")
@login_required
def viewnotes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM notes WHERE user_id=%s ORDER BY created_at DESC",
        (session["user_id"],)
    )
    notes = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template("viewnotes.html", notes=notes)


@app.route("/viewnotes/<int:note_id>")
@login_required
def singlenote(note_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM notes WHERE id=%s AND user_id=%s",
        (note_id, session["user_id"])
    )
    note = cursor.fetchone()

    cursor.close()
    conn.close()

    if not note:
        flash("Note not found.", "warning")
        return redirect(url_for("viewnotes"))

    return render_template("singlenote.html", note=note)


@app.route("/updatenote/<int:note_id>", methods=["GET", "POST"])
@login_required
def updatenote(note_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM notes WHERE id=%s AND user_id=%s",
        (note_id, session["user_id"])
    )
    note = cursor.fetchone()

    if not note:
        cursor.close()
        conn.close()
        flash("Note not found.", "warning")
        return redirect(url_for("viewnotes"))

    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()

        update_cursor = conn.cursor()
        update_cursor.execute(
            "UPDATE notes SET title=%s, content=%s WHERE id=%s AND user_id=%s",
            (title, content, note_id, session["user_id"])
        )
        conn.commit()
        update_cursor.close()
        cursor.close()
        conn.close()

        flash("Note updated successfully.", "success")
        return redirect(url_for("viewnotes"))

    cursor.close()
    conn.close()
    return render_template("updatenote.html", note=note)


@app.route("/deletenote/<int:note_id>")
@login_required
def deletenote(note_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM notes WHERE id=%s AND user_id=%s",
        (note_id, session["user_id"])
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash("Note deleted successfully.", "info")
    return render_template("deletenote.html")


if __name__ == "__main__":
    app.run(debug=True)