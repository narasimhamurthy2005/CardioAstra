from flask import Flask, request, jsonify, render_template
import joblib
import pandas as pd
import smtplib
import requests
import json
import os
from email.message import EmailMessage

app = Flask(__name__)

# --- CLINICAL CONFIGURATION ---
# Replace with your actual OpenRouter API Key
OPENROUTER_API_KEY = "place your api key"  # Make sure this is your full sk-or-v1-... key

# Gmail Configuration
EMAIL_SENDER = "@gmail.com" 
EMAIL_PASSWORD = "" 
EMAIL_RECEIVER = "@gmail.com"

# Global state to maintain patient telemetry and GPS
latest_data = {
    "heartrate": 75,
    "bp": "120/80",
    "stress": "low",
    "prediction": "Normal",
    "lat": None,
    "lng": None
}

# --- LOAD ML MODEL ---
try:
    model = joblib.load("heart_danger_pipeline.pkl")
    print("✅ ML Pipeline Loaded Successfully")
except Exception as e:
    model = None
    print(f"⚠️ Warning: ML Pipeline not found ({e}). Running in bypass mode.")

# --- EMERGENCY ALERT LOGIC ---
def send_emergency_alert(data, risk_type):
    """Generates and sends a professional clinical alert via Email."""
    msg = EmailMessage()
    msg['Subject'] = f"⚠️ CRITICAL MEDICAL ALERT: {risk_type} Detected"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    
    if data['lat'] and data['lng']:
        loc_link = f"https://www.google.com/maps?q={data['lat']},{data['lng']}"
    else:
        loc_link = "GPS SIGNAL PENDING: Check dashboard for last known coordinates."

    msg.set_content(
        f"URGENT CLINICAL NOTIFICATION\n"
        f"---------------------------\n"
        f"Patient Status: {risk_type}\n"
        f"Heart Rate: {data.get('heartrate')} BPM\n"
        f"Blood Pressure: {data.get('bp')} mmHg\n"
        f"Stress Index: {data.get('stress').upper()}\n\n"
        f"📍 LIVE PATIENT LOCATION:\n{loc_link}\n\n"
        f"This is an automated alert from the CardioAstra PRO Surveillance System."
    )

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"🚀 Emergency alert dispatched for: {risk_type}")
    except Exception as e:
        print(f"❌ Failed to send alert: {e}")

# --- ROUTES ---

@app.route('/')
def index():
    """Serves the main Command Center dashboard."""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Serves the login/authentication page."""
    return render_template('login.html')

@app.route('/chat', methods=['POST'])
def clinical_chat():
    """Handles AI medical queries using the CardioAstra personality."""
    user_message = request.json.get("message")
    
    if not user_message:
        return jsonify({"reply": "No clinical query detected."})
    
    try:
        # Incorporate live vitals into the AI's context for better answers
        system_prompt = (
            f"You are CardioAstra, a clinical AI assistant. "
            f"Current Patient Stats: HR: {latest_data['heartrate']} BPM, BP: {latest_data['bp']}. "
            f"Provide concise, medical-grade responses. Be brief."
        )

        payload = {
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }
        
        # FIXED HEADERS: OpenRouter free models require Referer and X-Title
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:5000", 
            "X-Title": "CardioAstra PRO"
        }
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        
        res_json = response.json()

        if response.status_code != 200:
            print(f"OpenRouter Error: {res_json}")
            return jsonify({"reply": "The Clinical AI is currently adjusting parameters. Please try again."})

        if 'choices' in res_json and len(res_json['choices']) > 0:
            reply = res_json['choices'][0]['message']['content']
        else:
            reply = "Telemetry received. I cannot provide a specific analysis at this moment."
            
        return jsonify({"reply": reply})

    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"reply": "Clinical AI is currently offline. Monitoring vitals locally."})

@app.route('/update_location', methods=['POST'])
def update_location():
    global latest_data
    loc = request.get_json()
    latest_data['lat'] = loc.get('lat')
    latest_data['lng'] = loc.get('lng')
    return jsonify({"status": "location_sync_complete"})

@app.route('/data', methods=['POST'])
def receive_sensor_data():
    """Endpoint for Arduino/Sensors to push live telemetry."""
    global latest_data
    incoming = request.get_json()

    try:
        hr = int(incoming.get('heartrate', 70))
        bp = incoming.get('bp', '120/80')
        stress = incoming.get('stress', 'low')

        latest_data.update({
            "heartrate": hr,
            "bp": bp,
            "stress": stress
        })

        prediction = "Normal"
        if model:
            df_input = pd.DataFrame([{
                'age': 25, 
                'bpm': hr,
                'activity': 'resting',
                'stress_level': stress.lower()
            }])
            prediction = model.predict(df_input)[0]
            latest_data["prediction"] = prediction

        # Alert Logic for Critical Vitals
        if prediction != 'Normal' or hr > 100 or hr < 50:
            send_emergency_alert(latest_data, prediction)
        
        return jsonify({"status": "ok", "prediction": prediction})

    except Exception as e:
        print(f"Telemetry Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/manual_alert', methods=['POST'])
def manual_alert():
    send_emergency_alert(latest_data, "Manual Emergency Trigger")
    return jsonify({"status": "alert_dispatched"})

@app.route('/datajson')
def stream_data():
    """Streams data to the frontend (Command Center)."""
    return jsonify(latest_data)

if __name__ == '__main__':
    # Run on 0.0.0.0 so other devices on your Wi-Fi can access it
    app.run(host='0.0.0.0', port=5000, debug=True)