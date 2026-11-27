
# WAREGUARD

## Smart Warehouse Monitoring System

WareGuard is an IoT-based Smart Warehouse Monitoring System designed to monitor warehouse conditions, track environmental data, detect movement and provide camera surveillance.

The system uses ESP32 devices, sensors, a camera and a web-based dashboard to monitor warehouse activities.

## Features

- User registration and login.
- Admin dashboard.
- Light monitoring using LDR sensor.
- Motion detection using PIR sensor.
- Distance monitoring using Ultrasonic sensor.
- Temperature and humidity monitoring using DHT22.
- ESP32-CAM live stream and video recording.
- Real-time sensor data monitoring.
- MySQL database for storing sensor readings and user information.

## Technologies Used

- Python
- Flask
- MySQL
- HTML
- CSS
- JavaScript
- OpenCV
- ESP32
- ESP32-CAM
- IoT Sensors

## Project Structure

```text
WareGuard/
│
├── env/
├── recordings/
├── static/
│   ├── PHOTOS/
│   ├── dashboard.css
│   └── style.css
│
├── templates/
│   ├── admin.html
│   ├── base.html
│   ├── camera.html
│   ├── dht22.html
│   ├── home.html
│   ├── ldr.html
│   ├── login.html
│   ├── pir.html
│   ├── signup.html
│   └── ultrasonic.html
│
├── wareguard.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Requirements

- Python 3
- MySQL Server
- ESP32 development board
- ESP32-CAM
- Required sensors
- Arduino IDE
- Web browser

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/WareGuard.git
cd WareGuard
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure MySQL

Make sure MySQL Server is running and configure the database connection in `wareguard.py`.

The application creates the WareGuard database and required tables automatically when started.

### 6. Run the application

```bash
python wareguard.py
```

### 7. Open the application

Visit:

```text
http://localhost:5000
```

## Project Description

WareGuard aims to improve warehouse monitoring through IoT technology by providing real-time environmental monitoring, motion detection and camera surveillance through a centralized web application.

---

**Project:** WareGuard  
**Type:** Final Programming Project  
**Technology:** IoT and Web Development
