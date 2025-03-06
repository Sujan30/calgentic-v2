import json
import os
import main
import requests
from flask import Flask, send_from_directory, jsonify, request, redirect, session, url_for
from google.oauth2 import service_account
from flask_cors import CORS
from datetime import timedelta, datetime
import time
from dotenv import load_dotenv
import logging
import jwt
import google_auth_oauthlib

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=5)
app.config['SESSION_COOKIE_SECURE'] = True  # Set to True to allow SameSite=None
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Required for cross-site cookies
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow the cookie to work on any domain
app.config['SESSION_COOKIE_PATH'] = '/'

# Enable session debugging
app.config['SESSION_COOKIE_NAME'] = 'calgentic_session'

# CORS configuration - ensure credentials are supported
CORS(app, 
     supports_credentials=True,  
     resources={r"/*": {"origins": [
         "http://localhost:8080",
         "http://127.0.0.1:8080", 
         "http://localhost:3000",
         "http://127.0.0.1:3000"
     ]}})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.getenv("google_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("google_client_secret")
REDIRECT_URI = os.getenv("redirect_url", "http://127.0.0.1:5000/callback")
FRONTEND_URL = os.getenv("frontend_url", "http://localhost:8080")

logger.info(f"FRONTEND_URL set to: {FRONTEND_URL}")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise Exception("Google OAuth credentials not set. Check .env file")
else:
    main.calendarAuth()

@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())
    logger.debug('Session: %s', session)
    logger.debug('Cookies: %s', request.cookies)

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

@app.route('/api/login')
def login():
    try:
        # Define the OAuth scopes
        SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
        
        # Use the credentials.json file in the root directory
        client_secret_file = os.getenv('google_client_id_path')
        
        # Log the client secret file path for debugging
        logger.info(f"Using client secret file: {client_secret_file}")
        
        if not os.path.exists(client_secret_file):
            logger.error(f"Client secret file not found at: {client_secret_file}")
            return jsonify({
                'error': 'Authentication failed',
                'message': f"Client secret file not found at: {client_secret_file}"
            }), 500
        
        # Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            client_secret_file,
            scopes=SCOPES)
        
        # Set the redirect URI
        flow.redirect_uri = url_for('auth_callback', _external=True)
        logger.info(f"Redirect URI set to: {flow.redirect_uri}")
        
        # Generate URL for request to Google's OAuth 2.0 server
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true')
        
        # Store the state so the callback can verify the auth server response
        session['state'] = state
        logger.info(f"Authorization URL: {authorization_url}")
        
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        return jsonify({
            'error': 'Authentication failed',
            'message': str(e)
        }), 500

@app.route('/callback')
def callback():
    # Get authorization code from Google
    code = request.args.get('code')
    if not code:
        logger.error("No authorization code received from Google")
        return redirect(f"{FRONTEND_URL}/login?error=no_code")

    try:
        # Exchange code for tokens
        token_endpoint = "https://oauth2.googleapis.com/token"
        data = {
            'code': code,
            'client_id': os.getenv('google_client_id'),
            'client_secret': os.getenv('google_client_secret'),
            'redirect_uri': url_for('auth_callback', _external=True),
            'grant_type': 'authorization_code'
        }
        
        logger.info("Exchanging code for tokens with data: %s", {k: v if k != 'client_secret' else '***' for k, v in data.items()})
        response = requests.post(token_endpoint, data=data)
        
        if not response.ok:
            logger.error("Token exchange failed: %s - %s", response.status_code, response.text)
            return redirect(f"{FRONTEND_URL}/login?error=token_exchange_failed&message={response.text}")
            
        tokens = response.json()
        logger.info("Received tokens: %s", {k: v if k != 'id_token' and k != 'access_token' else v[:10]+'...' for k, v in tokens.items()})
        
        # Get user info from ID token
        id_token = tokens.get('id_token')
        if not id_token:
            logger.error("No ID token received")
            return redirect(f"{FRONTEND_URL}/login?error=no_id_token")
            
        # Decode the ID token to get user info
        user_data = jwt.decode(id_token, options={"verify_signature": False})
        logger.info("User authenticated: %s", user_data.get('email'))
        
        # Store user info in session
        session.permanent = True
        session['user'] = {
            'id': user_data.get('sub'),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'picture': user_data.get('picture'),
            'authenticated': True,
            'login_time': datetime.now().isoformat()
        }
        
        # Store tokens in session
        session['tokens'] = {
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token', ''),
            'id_token': tokens.get('id_token'),
            'expires_at': time.time() + tokens.get('expires_in', 3600)
        }
        
        # Redirect to the frontend with auth_success parameter
        user_email = user_data.get('email', '')
        redirect_url = f"{FRONTEND_URL}/auth/callback?auth_success=true&user={user_email}"
        logger.info(f"Authentication successful, redirecting to: {redirect_url}")
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return redirect(f"{FRONTEND_URL}/login?error=callback_error&message={str(e)}")

@app.route("/auth/user")
def get_user():
    """Fetch logged-in user from session"""
    print(f"Session data in /auth/user: {session}")
    print(f"Session keys: {list(session.keys())}")
    print(f"Request cookies: {request.cookies}")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Origin: {request.headers.get('Origin', 'No origin')}")
    
    user = session.get("user")
    if not user:
        print("No user found in session")
        return jsonify({"error": "Not logged in"}), 401
    
    print(f"Returning user data: {user}")
    return jsonify(user)

@app.route("/auth/logout")
def logout():
    """Clear session and log out user"""
    session.pop("user", None)
    return jsonify({"message": "Logged out successfully"})

@app.route("/auth/test-session")
def test_session():
    """Test route to check if sessions are working properly"""
    # Set a test value in the session
    if "test_value" not in session:
        session["test_value"] = "This is a test value set at " + str(time.time())
        is_new = True
    else:
        is_new = False
    
    # Return the session data
    return jsonify({
        "session_working": True,
        "test_value": session.get("test_value"),
        "is_new_value": is_new,
        "session_data": {k: v for k, v in session.items() if k != "user"}
    })

@app.route('/api/check-auth')
def check_auth():
    # Log the request for debugging
    logger.info(f"Check auth request received from: {request.remote_addr}")
    logger.info(f"Session cookie: {request.cookies.get(app.config['SESSION_COOKIE_NAME'])}")
    
    # Check if cookies were received
    cookies_received = len(request.cookies) > 0
    cookie_names = list(request.cookies.keys())
    
    # Check if user is in session
    if 'user' not in session:
        logger.info("No user in session")
        return jsonify({
            'authenticated': False,
            'message': 'No user session found',
            'session_exists': 'session' in request.cookies,
            'cookies_received': cookies_received,
            'cookie_names': cookie_names
        })
    
    # Check if tokens are in session
    if 'tokens' not in session:
        logger.info("No tokens in session")
        return jsonify({
            'authenticated': False,
            'message': 'No tokens found',
            'session_exists': True,
            'cookies_received': cookies_received,
            'cookie_names': cookie_names
        })
    
    # Check if tokens are expired
    tokens = session['tokens']
    if time.time() > tokens.get('expires_at', 0):
        logger.info("Tokens expired")
        return jsonify({
            'authenticated': False,
            'message': 'Authentication expired',
            'session_exists': True,
            'token_expired_at': tokens.get('expires_at'),
            'current_time': time.time(),
            'cookies_received': cookies_received,
            'cookie_names': cookie_names
        })
    
    # User is authenticated
    logger.info(f"User authenticated: {session['user'].get('email')}")
    return jsonify({
        'authenticated': True,
        'user': session['user'],
        'session_exists': True,
        'cookies_received': cookies_received,
        'cookie_names': cookie_names
    })

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Log out the user by clearing their session"""
    try:
        logger.info("Logout request received")
        
        # Check if user is in session
        user_email = session.get('user', {}).get('email')
        if user_email:
            logger.info("Logging out user: %s", user_email)
        
        # Clear the session
        session.clear()
        
        response = jsonify({
            "success": True,
            "message": "Successfully logged out"
        })
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        response = jsonify({
            "success": False,
            "error": str(e)
        })
        response.headers['Content-Type'] = 'application/json'
        return response, 500

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    # Get the origin from the request
    origin = request.headers.get('Origin', '')
    
    # Check if the origin is in our allowed origins
    allowed_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080", 
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        # Default to the first allowed origin if the request origin is not in our list
        response.headers.add('Access-Control-Allow-Origin', allowed_origins[0])
    
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Type, X-Auth-Token')
    response.headers.add('Vary', 'Origin, Access-Control-Request-Headers, Access-Control-Request-Method')
    
    # Ensure content type is set for JSON responses
    if response.mimetype == 'application/json' and 'Content-Type' not in response.headers:
        response.headers.add('Content-Type', 'application/json')
    
    return response

@app.route('/refresh-token', methods=['POST'])
def refresh_token():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({"error": "No refresh token"}), 401
        
    # Validate refresh token
    try:
        # Generate new access token
        new_access_token = generate_new_token(refresh_token)
        response = jsonify({"success": True})
        response.set_cookie('access_token', new_access_token, httponly=True, secure=True)
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 401
@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({
        "error": "Access forbidden",
        "message": "Your session may have expired. Please refresh the page or log in again.",
        "code": 403
    }), 403

@app.route('/auth/callback')
def auth_callback():
    """Redirect to the main callback handler"""
    try:
        # Log the request for debugging
        logger.info(f"Auth callback received: {request.url}")
        logger.info(f"Query string: {request.query_string.decode('utf-8')}")
        
        # Check for error parameter
        error = request.args.get('error')
        if error:
            logger.error(f"Error in auth callback: {error}")
            error_description = request.args.get('error_description', 'Unknown error')
            return redirect(f"{FRONTEND_URL}/login?error={error}&message={error_description}")
        
        # Redirect to the main callback handler with the query string
        callback_url = '/callback?' + request.query_string.decode('utf-8')
        logger.info(f"Redirecting to: {callback_url}")
        return redirect(callback_url)
    except Exception as e:
        logger.error(f"Error in auth_callback: {str(e)}")
        return redirect(f"{FRONTEND_URL}/login?error=callback_error&message={str(e)}")

@app.route('/api/test-cookie', methods=['GET'])
def test_cookie():
    """Test endpoint to set and check cookies"""
    # Set a test cookie
    test_value = f"test-value-{int(time.time())}"
    resp = jsonify({
        "success": True,
        "message": "Test cookie set",
        "test_value": test_value,
        "cookies_received": len(request.cookies) > 0,
        "cookie_names": list(request.cookies.keys()) if request.cookies else []
    })
    
    # Set a test cookie that should be accessible from JavaScript
    resp.set_cookie(
        'test_cookie', 
        test_value, 
        max_age=3600, 
        path='/',
        domain=None,
        secure=True,  # Set to True to allow SameSite=None
        httponly=False,
        samesite='None'
    )
    
    return resp

if __name__ == '__main__':
    app.run(debug=True)
        
    


    


