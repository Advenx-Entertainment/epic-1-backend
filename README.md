# epic-1-backend
FastAPI Role-Based login Backend 
This guide ensures both (PC-PC and Pi-PC) follow the SAME workflow 
Install Required Tools
- Install Python 3.11 (recommended)
- Install VS Code (latest)

GIT COMMON RULES
Use SAME GitHub repository
Do NOT change core WebSocket logic randomly
Always pull latest code before starting:
 git pull origin main
Always push your changes:
 git add .
git commit -m "your message"
git push origin main
CLONE PROJECT 
git clone <GITHUB_REPO_LINK>
cd backend

Create venv (first time only)
Windows:
python -m venv venv
Raspberry Pi / Linux:
python3 -m venv venv
Activate venv
Windows:
venv\Scripts\activate
Linux / Pi:
source venv/bin/activate

Install Python packages:
pip install fastapi uvicorn python-jose passlib sqlalchemy
 requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
paho-mqtt==1.6.1
asyncpg==0.29.0
python-socketio==5.11.2
PyJWT==2.9.0
SQLAlchemy==2.0.32
python-jose==3.3.0
passlib[bcrypt]==1.7.4
Install using:
pip install -r requirements.txt

SETUP MQTT (RASPBERRY PI)
Install MQTT broker:
sudo apt update
sudo apt install mosquitto mosquitto-clients -y
Start broker:
sudo systemctl start mosquitto


PROJECT STRUCTURE
backend/
│── main.py
│── mqtt_client.py
│── database.py
│── models.py
│── auth.py
│── requirements.txt
│── .gitignore


RUN BACKEND 
WebSocket endpoint must be:  /ws
uvicorn main:app --host 0.0.0.0 --port 8000
IMPORTANT:
MUST use 0.0.0.0 (not localhost)
Allows all devices to connect

FIND SERVER IP
On server device:
Windows:
ipconfig
Raspberry Pi / Linux:
hostname -I
CLIENT CONNECTION RULE
All clients must connect using:
ws://<SERVER-IP>:8000/ws

TEAM WORKFLOW
Daily Work:
git pull origin main
After changes:
git add .
git commit -m "your message"
git push origin main

WORK DISTRIBUTION
(PC-PC):
Test multiple browser tabs / PCs
Validate WebSocket broadcast works between PCs
(Pi-PC):
Run backend on Raspberry Pi
Test connection from PC to Pi
Ensure Pi broadcasts correctly

What to run on each device
Backend (PC/server):
-m uvicorn main:app --host 0.0.0.0 --port 8000
(Use MQTT Broker: Mosquitto)
Raspberry Pi (publisher only):
import json
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("BACKEND_PC_IP", 1883, 60)

event = {"temp": 42, "status": "ok"}
client.publish("pi/events", json.dumps(event))
client.disconnect()
PC WebSocket client
Connect to:
ws://BACKEND_PC_IP:8000/ws?token=<JWT>

 FINAL ARCHITECTURE
PC Clients (UI)
    │
    │ WebSocket
    ▼
FastAPI Backend (Server)
    │
    │ MQTT
    ▼
Raspberry Pi (device/events)

PC Client 1 ──WS──▶ Backend ──WS──▶ PC Client 2
Pi ──MQTT──▶ Broker ──MQTT──▶ Backend ──WS──▶ PCs

