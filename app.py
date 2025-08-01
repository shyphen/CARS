import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Your Gemini API key here
GEMINI_API_KEY = "AIzaSyB8q3KpqVJjAuRBPDWJDENl8Ou5l9JNllY"  # Replace with your actual key

# ---------- Car Recommendation Logic ----------
def get_car_recommendations(car_type, budget, fuel_type, transmission, car_brand):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    brand_text = f"{car_brand} " if car_brand else ""
    prompt = f"""
    Recommend 9 cars within a ₹{budget} budget for a {brand_text}{car_type} with:
    - Fuel Type: {fuel_type}
    - Transmission: {transmission}

    For each car, provide:
    - name (string): Full car name with year, make, and model 
    - price (string): Price formatted with rupee symbol and commas
    - fuel_type (string): Type of fuel the car uses
    - transmission (string): Transmission type
    - features (object): With properties:
        - engine (string): Engine specifications
        - fuel_efficiency (string): Efficiency rating
        - safety (string): Safety rating or features
    - description (string): A brief description of the car
    - image_url (string): A real image URL of the car from the internet

    Return ONLY valid JSON format like this (no markdown or explanation):
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
            response_json = response.json()
            model_response = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

            if "```json" in model_response:
                json_start = model_response.find("{")
                json_end = model_response.rfind("}") + 1
                json_data = model_response[json_start:json_end]
            else:
                json_data = model_response

            parsed_data = json.loads(json_data)
            if "recommendations" not in parsed_data:
                return {"error": "Invalid response format from AI", "recommendations": []}
            return parsed_data

        return {"error": f"API request failed with status code {response.status_code}", "recommendations": []}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}", "recommendations": []}
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        return {"error": f"Failed to parse AI response: {str(e)}", "recommendations": []}

# ---------- Chatbot Logic ----------
def chatbot_response(user_message):
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    prompt = f"You are a helpful AI chatbot. Answer the following user message in a short and clean way and if i ask aything out of this just say sorry i can only deal with cars:\n\nUser: {user_message}\nAI:"

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            response_json = response.json()
            reply = response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
            return {"response": reply}
        return {"error": f"API request failed with status code {response.status_code}", "response": ""}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}", "response": ""}

# ---------- API Routes ----------
@app.route('/get-car-recommendations', methods=['POST'])
def recommend_cars():
    try:
        data = request.get_json()
        car_type = data.get("carType", "")
        budget = data.get("budget", "50000")
        fuel_type = data.get("fuelType", "")
        transmission = data.get("transmission", "")
        car_brand = data.get("carBrand", "")
        recommendations = get_car_recommendations(car_type, budget, fuel_type, transmission, car_brand)
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
        response = chatbot_response(user_message)
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"Chat server error: {str(e)}", "response": ""})

# ---------- Serve Frontend ----------
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# ---------- Run App ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
