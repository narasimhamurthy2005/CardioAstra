# ❤️ CardioAstra

CardioAstra is an AI-based heart health monitoring system that analyzes heart rate data to detect dangerous or abnormal conditions at an early stage.
The project uses machine learning to identify risk patterns and provides results through a simple web interface.

# Features

📊 Analyzes heart rate data to detect dangerous conditions

🤖 Uses a trained Machine Learning model for prediction

🌐 Web interface for user interaction (login & dashboard)

⚡ Backend server to process data and return results

📁 Supports CSV-based heart rate datasets


# Technologies Used

-- Python

-- Machine Learning (Scikit-learn)

-- Flask (Backend Server)

-- HTML (Frontend Templates)

-- Arduino (for sensor data – optional/experimental)

-- CSV datasets

# 📂 Project Structure
CARDIO ASTRA/<br>
│
├── model.py         <br>            # ML model training and prediction
├── server.py        <br>            # Flask backend server
├── heart_danger_pipeline.pkl <br>   # Trained ML model
├── danger_heart_rate_data.csv <br>  # Dataset
├── arduino.c              <br>      # Arduino sensor code
│
├── templates/<br>
│   ├── login.html   <br>            # Login page
│   └── index.html   <br>          # Main dashboard
│
└── README.md<br>

# ⚙️ How It Works

Heart rate data is collected (from dataset or sensors)

The ML model analyzes the data

Risk patterns are detected

The server sends results to the web interface

Users can view alerts or health status

# ▶️How to Run the Project

1️⃣ Install dependencies
pip install flask scikit-learn pandas numpy

2️⃣ Run the server
python server.py

3️⃣ Open in browser
http://127.0.0.1:5000/
