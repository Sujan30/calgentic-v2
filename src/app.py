import json
import os
# import main  # Removing this import to fix deployment error
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
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables from .env file
load_dotenv()

# Set up frontend URL based on environment
FRONTEND_URL = os.getenv('frontend_url', 'http://localhost:8080')
if FRONTEND_URL.endswith('/'):
    FRONTEND_URL = FRONTEND_URL[:-1]  # Remove trailing slash if present

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
         "http://127.0.0.1:3000",
         "http://localhost:5000",
         "http://127.0.0.1:5000",
         "https://calgentic.com",
         "https://www.calgentic.com",
         "https://calgentic.onrender.com"
     ]}})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log important configuration
logger.info(f"FRONTEND_URL set to: {FRONTEND_URL}")
logger.info(f"CORS origins: {app.config.get('CORS_ORIGINS', 'Not directly accessible')}")
logger.info(f"Running in {'development' if os.getenv('FLASK_ENV') == 'development' else 'production'} mode")

GOOGLE_CLIENT_ID = os.getenv("google_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("google_client_secret")
REDIRECT_URI = os.getenv("redirect_url", "http://127.0.0.1:5000/callback")

logger.info(f"FRONTEND_URL set to: {FRONTEND_URL}")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise Exception("Google OAuth credentials not set. Check .env file")
else:
    # main.calendarAuth()
    pass

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

@app.route('/login')
def login_redirect():
    """Redirect /login to /api/login for compatibility"""
    logger.info("Redirecting from /login to /api/login")
    return redirect('/api/login')

@app.route('/api/login')
def login():
    try:
        # Define the OAuth scopes
        SCOPES = ['openid','https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
        
        # Get the client ID and secret from environment variables
        client_id = os.getenv('google_client_id')
        client_secret = os.getenv('google_client_secret')
        
        # Set the redirect URI based on the environment
        redirect_uri = os.getenv('redirect_url', f"{FRONTEND_URL}/auth/callback")
        
        # Create the OAuth flow
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            },
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        # Generate the authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Redirect to the authorization URL
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed", "message": str(e)}), 500

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
        redirect_uri = os.getenv('redirect_url', f"{FRONTEND_URL}/auth/callback")
        
        logger.info(f"Using redirect URI: {redirect_uri}")
        
        data = {
            'code': code,
            'client_id': os.getenv('google_client_id'),
            'client_secret': os.getenv('google_client_secret'),
            'redirect_uri': redirect_uri,
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
    # Add CORS headers to every response
    response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Max-Age', '3600')
    
    # Set SameSite attribute for cookies
    if 'Set-Cookie' in response.headers:
        cookies = response.headers.getlist('Set-Cookie')
        new_cookies = []
        for cookie in cookies:
            if 'SameSite=' not in cookie:
                cookie += '; SameSite=None; Secure'
            new_cookies.append(cookie)
        response.headers.pop('Set-Cookie')
        for cookie in new_cookies:
            response.headers.add('Set-Cookie', cookie)
    
    # Log the response for debugging
    logger.debug(f"Response headers: {dict(response.headers)}")
    
    return response

def refresh_google_token(refresh_token):
    """Refresh an expired Google OAuth token"""
    try:
        logger.info("Attempting to refresh expired token")
        token_endpoint = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': os.getenv('google_client_id'),
            'client_secret': os.getenv('google_client_secret'),
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_endpoint, data=data)
        
        if not response.ok:
            logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
            return None
            
        tokens = response.json()
        logger.info("Token refreshed successfully")
        
        # Update the session with the new token
        if 'tokens' in session:
            session['tokens']['access_token'] = tokens.get('access_token')
            session['tokens']['expires_at'] = time.time() + tokens.get('expires_in', 3600)
            session.modified = True
            
        return tokens.get('access_token')
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return None

def get_valid_access_token():
    """Get a valid access token, refreshing if necessary"""
    try:
        # Check if we have tokens in the session
        if 'tokens' not in session:
            logger.error("No tokens in session")
            return None
            
        tokens = session['tokens']
        
        # Check if the token is expired
        if time.time() > tokens.get('expires_at', 0):
            logger.info("Token expired, attempting to refresh")
            refresh_token = tokens.get('refresh_token')
            
            if not refresh_token:
                logger.error("No refresh token available")
                return None
                
            # Try to refresh the token
            new_access_token = refresh_google_token(refresh_token)
            if not new_access_token:
                logger.error("Failed to refresh token")
                return None
                
            return new_access_token
        
        # Token is still valid
        return tokens.get('access_token')
    except Exception as e:
        logger.error(f"Error getting valid access token: {str(e)}")
        return None

@app.route('/refresh-token', methods=['POST'])
def refresh_token():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({"error": "No refresh token"}), 401
        
    # Validate refresh token
    try:
        # Generate new access token
        new_access_token = get_valid_access_token()
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

@app.route('/test')
def test():
    return "hola render, server is a okay"


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

# Add a simple test endpoint
@app.route('/api/ping', methods=['GET'])
def ping():
    """Simple endpoint to test API connectivity"""
    logger.info(f"Ping received from: {request.remote_addr}, Origin: {request.headers.get('Origin', 'No origin')}")
    return jsonify({
        "status": "success",
        "message": "API is working!",
        "timestamp": datetime.now().isoformat(),
        "cors_enabled": True
    })

# Add a POST endpoint for /api/prompt
@app.route('/api/prompt', methods=['POST'])
def handle_prompt():
    """Handle prompt requests from the frontend"""
    try:
        # Get the prompt from the request body
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({"error": "No prompt provided"}), 400
            
        prompt = data['prompt']
        logger.info(f"Received prompt: {prompt}")
        
        # Make sure we have a valid token before processing the prompt
        access_token = get_valid_access_token()
        if not access_token:
            return jsonify({"error": "Not authenticated or token expired"}), 401
        
        # Process the prompt using the existing function
        try:
            response = main.promptToEvent(prompt)
            logger.info(f"Prompt response: {response}")
        except Exception as e:
            logger.error(f"Error in promptToEvent: {str(e)}")
            return jsonify({"error": f"Failed to process prompt: {str(e)}"}), 500
        
        # Check if response contains an error
        if isinstance(response, dict) and 'error' in response:
            return jsonify(response), 400
            
        # Check if response is a boolean (indicating success/failure)
        if isinstance(response, bool):
            return jsonify({
                "success": response,
                "message": "Prompt processed" if response else "Failed to process prompt"
            })
            
        # Check if response has the expected structure
        if not isinstance(response, dict) or 'action_type' not in response:
            return jsonify({
                "success": True,
                "message": "Prompt processed but response format is unexpected",
                "data": response
            })
        
        # Handle different action types
        try:
            if response['action_type'] == 'create':
                if not isinstance(response.get('eventParams', []), list) or len(response['eventParams']) == 0:
                    return jsonify({"error": "No event parameters provided"}), 400
                    
                formatted_event = main.formatEvent(response['eventParams'][0])
                if not formatted_event:
                    return jsonify({"error": "Failed to format event"}), 400
                    
                return jsonify({
                    "success": True,
                    "message": formatted_event.get('message', 'Event created'),
                    "data": formatted_event
                })
            elif response['action_type'] == 'view':
                if 'query_details' not in response:
                    return jsonify({"error": "No query details provided"}), 400
                    
                view_response = main.findEvent(response['query_details'])
                return jsonify({
                    "success": True,
                    "message": view_response.get('message', 'Events found'),
                    "data": view_response
                })
            else:
                return jsonify({
                    "success": True,
                    "message": response.get('message', 'Prompt processed'),
                    "data": response
                })
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return jsonify({"error": f"Error processing response: {str(e)}"}), 500
        
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}")
        return jsonify({"error": f"Failed to process prompt: {str(e)}"}), 500

# Add explicit handling for OPTIONS requests
@app.route('/api/prompt', methods=['OPTIONS'])
def handle_prompt_options():
    """Handle OPTIONS requests for CORS preflight"""
    response = app.make_default_options_response()
    return response

# Add explicit handling for OPTIONS requests for check-auth
@app.route('/api/check-auth', methods=['OPTIONS'])
def handle_check_auth_options():
    """Handle OPTIONS requests for CORS preflight for check-auth"""
    response = app.make_default_options_response()
    return response

# Add a catch-all route to handle frontend routes
@app.route('/<path:path>')
def catch_all(path):
    """Catch-all route to handle frontend routes"""
    # Check if this is an API route
    if path.startswith('api/'):
        return jsonify({"error": "API endpoint not found"}), 404
        
    # Special case for auth/callback - this should be handled by the backend
    if path == 'auth/callback':
        logger.info("Redirecting auth/callback to /auth/callback")
        return redirect('/auth/callback?' + request.query_string.decode('utf-8'))
        
    # For frontend routes, serve the index.html
    logger.info(f"Serving frontend route: {path}")
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
        
    


    


