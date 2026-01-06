#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include "MAX30105.h"
#include <WiFiUdp.h>
#include <NTPClient.h>

// --- WiFi credentials ---
#define WIFI_SSID ""
#define WIFI_PASSWORD ""

// --- Firebase Realtime Database ---
#define FIREBASE_URL ""

// --- Flask server endpoint (Ensure this is your PC's IP address) ---
#define FLASK_URL ""

// --- User Profile (Match this to your personal data for better ML accuracy) ---
int userAge = 45; 
String currentActivity = "resting"; // Can be "resting", "walking", or "exercise"

// --- NTP for timestamp ---
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 19800); // IST (+5:30)

MAX30105 particleSensor;

unsigned long lastFirebaseUpload = 0;
const unsigned long firebaseInterval = 30000; 

int getHeartRate() {
    long irValue = particleSensor.getIR();
    static long lastIR = 0;
    static int bpm = 0;

    // Basic logic: if finger is detected
    if (irValue > 50000) {
        // For testing, we use a random range. 
        // In a real setup, use the HeartRate.h library for actual calculation.
        bpm = random(65, 120); 
    } else {
        bpm = 0; // No finger detected
    }
    return bpm;
}

String calculateStress(int hr) {
    if (hr == 0) return "low";
    if (hr < 80) return "low";
    else if (hr < 100) return "medium";
    else return "high";
}

int calculateBP(int hr) {
    if (hr == 0) return 0;
    return 110 + (hr - 70) / 2; 
}

void setup() {
    Serial.begin(115200);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected!");

    if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
        Serial.println("MAX30102 not found.");
        while (1);
    }
    particleSensor.setup(); 
    timeClient.begin();
}

void loop() {
    timeClient.update();
    String formattedTime = timeClient.getFormattedTime();
    unsigned long ts = timeClient.getEpochTime();

    int hr = getHeartRate();
    if (hr > 0) { // Only send data if a heart rate is detected
        int bpValue = calculateBP(hr);
        String stress = calculateStress(hr);

        // Build JSON payload with ALL features the ML model needs
        String jsonPayload = "{";
        jsonPayload += "\"heartrate\":" + String(hr) + ",";
        jsonPayload += "\"bp\":\"" + String(bpValue) + "/80\",";
        jsonPayload += "\"stress\":\"" + stress + "\",";
        jsonPayload += "\"activity\":\"" + currentActivity + "\",";
        jsonPayload += "\"age\":" + String(userAge) + ",";
        jsonPayload += "\"time\":\"" + formattedTime + "\"";
        jsonPayload += "}";

        // --- Send to Flask ---
        if (WiFi.status() == WL_CONNECTED) {
            HTTPClient http;
            http.begin(FLASK_URL);
            http.addHeader("Content-Type", "application/json");
            int httpCode = http.POST(jsonPayload);
            
            if (httpCode > 0) {
                Serial.println("Sent to Flask: " + jsonPayload);
            }
            http.end();
        }

        // --- Send to Firebase every 30s ---
        if (millis() - lastFirebaseUpload >= firebaseInterval) {
            String url = String(FIREBASE_URL) + "/readings/" + String(ts) + ".json";
            HTTPClient http;
            http.begin(url);
            http.PUT(jsonPayload);
            http.end();
            lastFirebaseUpload = millis();
        }
    }

    delay(1000); // Send data every 1 second
}