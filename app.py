from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import smtplib
from email.mime.text import MIMEText
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        email TEXT,
        contact1 TEXT,
        contact2 TEXT,
        contact3 TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                  (username, password, email))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')

# ---------------- LOGIN ----------------
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

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# ---------------- HOME ----------------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')

# ---------------- PROFILE ----------------
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT username, email, contact1, contact2, contact3 FROM users WHERE username=?", (username,))
    user = c.fetchone()

    conn.close()

    return render_template('profile.html', user=user)

# ---------------- UPDATE PROFILE ----------------
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return redirect('/login')

    username = session['user']

    c1 = request.form.get('c1')
    c2 = request.form.get('c2')
    c3 = request.form.get('c3')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET contact1=?, contact2=?, contact3=?
        WHERE username=?
    """, (c1, c2, c3, username))

    conn.commit()
    conn.close()

    return redirect('/profile')

# ---------------- EMAIL FUNCTION ----------------
def send_email(receiver, subject, body):
    sender_email = "emergencyehelp123@gmail.com"
    password = "hdzphcmarvvtcker"   # your app password

    msg = MIMEText(body, "plain", "utf-8")
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    server.send_message(msg)
    server.quit()

# ---------------- SOS ALERT ----------------
@app.route('/send_alert', methods=['POST'])
def send_alert():
    if 'user' not in session:
        return "Unauthorized"

    username = session['user']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT contact1, contact2, contact3 FROM users WHERE username=?", (username,))
    contacts = c.fetchone()

    conn.close()

    for contact in contacts:
        if contact:
            send_email(contact, "SOS Alert 🚨", "EMERGENCY! I need help!")

    return "Alert Sent to all contacts!"

# ---------------- LOCATION ----------------
@app.route('/send_location', methods=['POST'])
def send_location():
    if 'user' not in session:
        return "Unauthorized"

    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')

    link = f"https://maps.google.com/?q={lat},{lon}"

    username = session['user']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT contact1, contact2, contact3 FROM users WHERE username=?", (username,))
    contacts = c.fetchone()

    conn.close()

    for contact in contacts:
        if contact:
            send_email(contact, "Live Location 🚨", f"My location:\n{link}")

    return "Location sent to all contacts"

# ---------------- DISTANCE FUNCTION ----------------
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    return round(R * c, 2)

# ---------------- POLICE DATA ----------------
police_data = [
    {"name": "Bangalore Women Police Station", "lat": 12.9716, "lon": 77.5946},
    {"name": "Mysore Women Police Station", "lat": 12.2958, "lon": 76.6394},
    {"name": "Hubli Police Station", "lat": 15.3647, "lon": 75.1240},
    {"name": "Mangalore Police Station", "lat": 12.9141, "lon": 74.8560},
    {"name": "Belgaum Police Station", "lat": 15.8497, "lon": 74.4977}
]

# ---------------- POLICE PAGE ----------------
@app.route('/police')
def police():
    if 'user' not in session:
        return redirect('/login')
    return render_template('police.html')

# ---------------- GET POLICE ----------------
@app.route('/get_police')
def get_police():
    user_lat = float(request.args.get('lat'))
    user_lon = float(request.args.get('lon'))

    results = []

    for p in police_data:
        dist = calculate_distance(user_lat, user_lon, p['lat'], p['lon'])

        results.append({
            "name": p['name'],
            "lat": p['lat'],
            "lon": p['lon'],
            "distance": dist
        })

    results.sort(key=lambda x: x['distance'])

    return jsonify(results)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)