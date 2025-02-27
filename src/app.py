import json
import os
import main
import requests
from flask import Flask, send_from_directory, jsonify, request, redirect, session
from google.oauth2 import service_account
from flask_cors import CORS


app = Flask(__name__)


CORS(app, resources={r"/*": {"origins":["http://localhost:8080","http://127.0.0.1:5000" ]}})




GOOGLE_CLIENT_ID = os.getenv("google_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("google_client_secret")
REDIRECT_URI = os.getenv("redirect_url", "http://localhost:5000/auth/callback")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise Exception("Google OAuth credentials not set. Check .env file")

main.calendarAuth()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/prompt/<prompt>', methods=['GET'])
def onboard(prompt):
    response = main.promptToEvent(prompt)
    
    # Check if response contains an error
    if isinstance(response, dict) and 'error' in response:
        return jsonify(response), 400
    
    # No need to parse JSON again since promptToEvent already returns a dictionary
    response_dict = response
    
    if 'action_type' not in response_dict:
        return jsonify({"error": "Missing action_type in response"}), 400

    if response_dict['action_type'] == 'create':
        if 'eventParams' not in response_dict or 'eventCompletion' not in response_dict:
            return jsonify({"error": "Missing eventParams or eventCompletion"}), 400

        eventParams = response_dict['eventParams']
        # Check if eventParams is an array and get the first item
        if isinstance(eventParams, list) and len(eventParams) > 0:
            event_data = eventParams[0]  # Get the first event from the array
            try:
                if main.formatEvent(event_data):
                    message = response_dict['eventCompletion']
                    return jsonify({"message": message, "success": True})
                else:
                    return jsonify({"error": "Failed to format event"}), 400
            except Exception as e:
                return jsonify({"error": f"Exception in formatEvent: {str(e)}"}), 400
        else:
            return jsonify({"error": "eventParams is not in the expected format"}), 400

    elif response_dict['action_type'] == 'view':
        if 'query_details' not in response_dict:
            return jsonify({"error": "Missing query_details"}), 400

        query_details = response_dict['query_details']
        return jsonify(main.findEvent(query_details=query_details))

    return jsonify({"error": "Unknown action_type"}), 400

@app.route("/auth/login")
def login():
    """Redirect user to Google's OAuth consent page"""
    try:
        google_auth_url = (
            "https://accounts.google.com/o/oauth2/auth"
            "?response_type=code"
            f"&client_id={GOOGLE_CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            "&scope=email%20profile"
            "&access_type=offline"
        )
        return redirect(google_auth_url)
    except:
        print('error with logging in, invalid client ID or redirect URI')


@app.route("/auth/callback")
def handleLogin():
    """Handle OAuth callback and get user data"""
    code = request.args.get("code")
    
    if not code:
        return jsonify({"error": "Authorization code not found"}), 400

    # Exchange authorization code for access token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(token_url, data=token_data).json()
    access_token = token_response.get("access_token")

    if not access_token:
        return jsonify({"error": "Failed to get access token"}), 400

    # Fetch user info from Google
    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    user_info = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"}).json()

    # Store user in session
    session["user"] = user_info

    return jsonify(user_info)

@app.route("/auth/user")
def get_user():
    """Fetch logged-in user from session"""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify(user)

@app.route("/auth/logout")
def logout():
    """Clear session and log out user"""
    session.pop("user", None)
    return jsonify({"message": "Logged out successfully"})

if __name__ == '__main__':
    app.run(debug=True)
        
    


    


