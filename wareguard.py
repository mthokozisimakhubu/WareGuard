from flask import Flask, request, render_template, jsonify, session, redirect
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import cv2
import threading
import os
import time

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
VIDEO_FOLDER = "recordings"

if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)


app.secret_key = os.getenv("SECRET_KEY")

# ---------------- DATABASE ----------------
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# ---------------- INIT DATABASE ----------------
def init_db():

    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    cur = conn.cursor()

    # Create Database
    cur.execute("CREATE DATABASE IF NOT EXISTS WareGuard")

    cur.execute("USE WareGuard")

    # Users Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Users(
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) UNIQUE,
        password VARCHAR(255),
        role VARCHAR(50),
        sensor_type VARCHAR(50)
    )
    """)

    # Sensor Tables
    sensors = ["LDR", "PIR", "Ultrasonic", "Temperature", "Humidity"]

    for sensor in sensors:

        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{sensor}`(
            id INT AUTO_INCREMENT PRIMARY KEY,
            value FLOAT,
            timestamp VARCHAR(255)
        )
        """)

    # Camera Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Camera(
        id INT AUTO_INCREMENT PRIMARY KEY,
        image_path VARCHAR(255),
        timestamp VARCHAR(255)
    )
    """)

    conn.commit()
    conn.close()

init_db()


def record_esp32():

    global recording

    stream_url = "http://192.168.43.251:81/stream"

    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print("Camera stream failed")
        recording=False
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width <= 0:
        width = 640

    if height <= 0:
        height = 480

    filename = os.path.join(
        VIDEO_FOLDER,
        f"video_{int(time.time())}.avi"
    )

    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    out = cv2.VideoWriter(
        filename,
        fourcc,
        20,
        (width,height)
    )

    start = time.time()

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        out.write(frame)

        if time.time()-start > 60:
            break

    cap.release()
    out.release()

    recording=False

    print("Saved:",filename)

# ---------------- HOME ----------------
@app.route('/')
def index():
    return redirect('/home')


@app.route('/home')
def home():
    return render_template("home.html")
    
# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form['username']

        password = generate_password_hash(
            request.form['password']
        )

        role = request.form['role']

        sensor = request.form['sensor_type']

        try:

            conn = get_db()

            cur = conn.cursor()

            # Check if user exists
            cur.execute(
                "SELECT * FROM Users WHERE username=%s",
                (username,)
            )

            existing_user = cur.fetchone()

            if existing_user:
                return "Username already exists"

            # Insert new user
            cur.execute("""
            INSERT INTO Users(username, password, role, sensor_type)
            VALUES(%s, %s, %s, %s)
            """, (username, password, role, sensor))

            conn.commit()

            return redirect('/login')

        except Error as e:
            return f"Database Error: {e}"

        finally:
            conn.close()

    return render_template("signup.html")

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM Users WHERE username=%s",
            (username,)
        )

        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):

            session['user'] = user[1]
            session['role'] = user[3]
            session['sensor'] = user[4]

            if user[3] == "admin":
                return redirect('/admin')

            return redirect(f"/{user[4].lower()}")

        return "Invalid Username or Password"

    return render_template("login.html")

# ---------------- DASHBOARDS ----------------
@app.route('/ldr')
def ldr():
    return render_template("ldr.html")

@app.route('/pir')
def pir():
    return render_template("pir.html")

@app.route('/ultrasonic')
def ultrasonic():
    return render_template("ultrasonic.html")

@app.route('/dht22')
def dht22():
    return render_template("dht22.html")

recording = False

@app.route('/camera')
def camera():

    global recording

    if not recording:

        recording = True

        thread = threading.Thread(
            target=record_esp32
        )

        thread.daemon = True
        thread.start()

    return render_template(
        "camera.html",
        cam_ip="192.168.43.251"
    )

@app.route('/admin')
def admin():
    global recording

    if not recording:

        recording = True

        thread = threading.Thread(
            target=record_esp32
        )

        thread.daemon = True
        thread.start()
    return render_template("admin.html",cam_ip="192.168.43.251")



# ---------------- LIVE SENSOR DATA ----------------
@app.route('/api/live/<sensor>')
def live(sensor):

    allowed = [
        "LDR",
        "PIR",
        "Ultrasonic",
        "Temperature",
        "Humidity"
    ]

    if sensor not in allowed:
        return jsonify({"error": "Invalid Sensor"})

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        f"SELECT value, timestamp FROM `{sensor}` ORDER BY id DESC LIMIT 20"
    )

    data = cur.fetchall()[::-1]

    conn.close()

    return jsonify(data)

# ---------------- PIR API ----------------
@app.route('/api/pir', methods=['POST'])
def receive_pir():

    data = request.get_json()

    if not data or 'value' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        "INSERT INTO PIR(value, timestamp) VALUES(%s, %s)",
        (float(data['value']), timestamp)
    )

    conn.commit()

    conn.close()

    return jsonify({'message': 'PIR saved'}), 201

# ---------------- LDR API ----------------
@app.route('/api/ldr', methods=['POST'])
def receive_ldr():

    data = request.get_json()

    if not data or 'value' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        "INSERT INTO LDR(value, timestamp) VALUES(%s, %s)",
        (float(data['value']), timestamp)
    )

    conn.commit()

    conn.close()

    return jsonify({'message': 'LDR saved'}), 201

# ---------------- DHT22 API ----------------
@app.route('/data')
def receive_dht():

    temp = request.args.get('temp')

    hum = request.args.get('hum')

    if temp is None or hum is None:
        return "Missing Data", 400

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db()

    cur = conn.cursor()

    cur.execute(
        "INSERT INTO Temperature(value, timestamp) VALUES(%s, %s)",
        (float(temp), timestamp)
    )

    cur.execute(
        "INSERT INTO Humidity(value, timestamp) VALUES(%s, %s)",
        (float(hum), timestamp)
    )

    conn.commit()

    conn.close()

    return "OK"

@app.route('/api/ultrasonic')
def ultrasonic_data():

    distance = request.args.get('distance')
    level = request.args.get('level')
    status = request.args.get('status')

    if distance is None:
        return "Missing Data",400

    timestamp = datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S'
    )

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO Ultrasonic
        (value,timestamp)
        VALUES(%s,%s)
        """,
        (float(distance),timestamp)
    )

    conn.commit()
    conn.close()

    print(
      f"Distance:{distance} "
      f"Level:{level}% "
      f"Status:{status}"
    )

    return "OK"

# ---------------- RUN ----------------
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )