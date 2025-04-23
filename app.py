import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Load from environment variable

# ---------- Car Recommendation Logic ----------
def get_car_recommendations(car_type, budget, fuel_type, transmission, car_brand):
    if not GEMINI_API_KEY:
        return {"error": "Gemini API key not set", "recommendations": []}

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    brand_text = f"{car_brand} " if car_brand else ""
    prompt = f"""
    Recommend 9 cars within ₹{budget} budget for a {brand_text}{car_type} with:
    - Fuel Type: {fuel_type}
    - Transmission: {transmission}

    Provide JSON only in this format:
    {{
      "recommendations": [
        {{
          "name": "Car Name",
          "price": "₹XX,XXX",
          "fuel_type": "Type",
          "transmission": "Type",
          "features": {{
            "engine": "Details",
            "fuel_efficiency": "XX km/l",
            "safety": "Rating"
          }},
          "description": "Brief description",
          "image_url": "https://example.com/car.jpg"
        }}
      ]
    }}
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            model_output = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

            # Remove markdown if included
            if "```json" in model_output:
                json_start = model_output.find("{")
                json_end = model_output.rfind("}") + 1
                model_output = model_output[json_start:json_end]

            parsed_data = json.loads(model_output)
            if "recommendations" in parsed_data:
                return parsed_data
            else:
                return {"error": "Invalid AI response structure", "recommendations": []}
        return {"error": f"API request failed: {response.status_code}", "recommendations": []}
    except Exception as e:
        return {"error": f"Exception: {str(e)}", "recommendations": []}

# ---------- Chatbot Logic ----------
def chatbot_response(user_message):
    if not GEMINI_API_KEY:
        return {"error": "Gemini API key not set", "response": ""}

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    prompt = f"You are a helpful AI assistant. Respond briefly and clearly:\n\nUser: {user_message}\nAI:"

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            reply = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            return {"response": reply}
        return {"error": f"API request failed: {response.status_code}", "response": ""}
    except Exception as e:
        return {"error": f"Chat error: {str(e)}", "response": ""}

# ---------- API Routes ----------
@app.route('/get-car-recommendations', methods=['POST'])
def recommend_cars():
    try:
        data = request.get_json()
        recommendations = get_car_recommendations(
            data.get("carType", ""),
            data.get("budget", "50000"),
            data.get("fuelType", ""),
            data.get("transmission", ""),
            data.get("carBrand", "")
        )
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}", "recommendations": []})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        if not user_message:
            return jsonify({"error": "No message provided", "response": ""})
        return jsonify(chatbot_response(user_message))
    except Exception as e:
        return jsonify({"error": f"Chat server error: {str(e)}", "response": ""})

# ---------- Serve Frontend ----------
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static_file(path):
    return send_from_directory(app.static_folder, path)

# ---------- Run App ----------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
