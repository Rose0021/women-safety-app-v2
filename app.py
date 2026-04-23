from flask import Flask, render_template, request, redirect, session
import sqlite3
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "secret123"


# 🔹 DATABASE INIT
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        email TEXT,
        emergency TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()


# 🔐 SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        emergency = request.form['emergency']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("INSERT INTO users (username, password, email, emergency) VALUES (?, ?, ?, ?)",
                  (username, password, email, emergency))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')


# 🔐 LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()

        conn.close()

        if user:
            session['user'] = username
            return redirect('/')
        else:
            return "Invalid Credentials"

    return render_template('login.html')


# 🔓 LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


# 🏠 HOME
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')

    return render_template('index.html')


# 👤 PROFILE VIEW
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT username, email, emergency FROM users WHERE username=?", (username,))
    user = c.fetchone()

    conn.close()

    return render_template('profile.html', user=user)


# ✏️ UPDATE PROFILE
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']
    new_emergency = request.form['emergency']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("UPDATE users SET emergency=? WHERE username=?", (new_emergency, username))

    conn.commit()
    conn.close()

    return redirect('/profile')


# 📧 GET USER CONTACT
def get_emergency_email(username):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT emergency FROM users WHERE username=?", (username,))
    result = c.fetchone()

    conn.close()

    return result[0] if result else None


# 📧 EMAIL FUNCTION
def send_email(receiver, subject, body):
    sender_email = "emergencyehelp123@gmail.com"
    password = "tykdbhpsqnywqaze"

    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    server.send_message(msg)
    server.quit()


# 🚨 SOS ALERT
@app.route('/send_alert', methods=['POST'])
def send_alert():
    if 'user' not in session:
        return "Unauthorized"

    user = session['user']
    receiver = get_emergency_email(user)

    if not receiver:
        return "No emergency contact!"

    try:
        send_email(receiver, "SOS Alert", "🚨 EMERGENCY! I need help!")
        return f"Alert sent to {receiver}"
    except Exception as e:
        return str(e)


# 📍 LOCATION ALERT
@app.route('/send_location', methods=['POST'])
def send_location():
    if 'user' not in session:
        return "Unauthorized"

    data = request.get_json()

    if not data:
        return "No data received"

    lat = data.get('latitude')
    lon = data.get('longitude')

    if not lat or not lon:
        return "Invalid location"

    link = f"https://maps.google.com/?q={lat},{lon}"

    user = session['user']
    receiver = get_emergency_email(user)

    if not receiver:
        return "No emergency contact!"

    try:
        send_email(receiver, "Live Location 🚨", f"My live location:\n{link}")
        return "Location sent"
    except Exception as e:
        return str(e)


# ▶️ RUN
if __name__ == "__main__":
    app.run(debug=True)