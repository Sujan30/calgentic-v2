import json
import os
import main
import requests
from flask import Flask, send_from_directory, jsonify, request, redirect, session
from google_auth_oauthlib.flow import InstalledAppFlow
from flask_cors import CORS
from datetime import timedelta, datetime
import time
from dotenv import load_dotenv
import logging
import jwt

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')

# Use a strong secret key; load from environment in production
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=5)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_NAME'] = 'calgentic_session'

# Enable CORS for allowed origins
CORS(app, supports_credentials=True, resources={r"/*": {"origins": [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5001",
    "http://127.0.0.1:5001",
    "https://calgentic.com",
    "https://www.calgentic.com",
    "https://calgentic.onrender.com"
]}})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Google OAuth credentials from environment variables
GOOGLE_CLIENT_ID = os.getenv("google_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("google_client_secret")
frontend_url = os.getenv('frontend_url', 'http://127.0.0.1:5000')
redirect_url = os.getenv('redirect_url', f"{frontend_url}/auth/callback")

logger.info(f"FRONTEND_URL set to: {frontend_url}")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise Exception("Google OAuth credentials not set. Check your .env file.")

# Create credentials.json if it doesn't exist
client_secret_file = os.getenv('google_client_id_path', 'credentials.json')
if not os.path.exists(client_secret_file):
    try:
        credentials_data = {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "project_id": "gen-lang-client-0051339096",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [
                    "http://localhost",
                    "https://calgentic.com",
                    "https://www.calgentic.com"
                ]
            }
        }
        with open(client_secret_file, 'w') as f:
            json.dump(credentials_data, f)
        logger.info(f"Created credentials file at: {client_secret_file}")
    except Exception as e:
        logger.error(f"Failed to create credentials file: {str(e)}")

@app.before_request
def log_request_info():
    # Debug logging only; sensitive details should not be logged in production.
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())
    logger.debug('Session: %s', session)
    logger.debug('Cookies: %s', request.cookies)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/prompt/<prompt>', methods=['GET'])
def onboard(prompt):
    try:
        logger.info(f"Processing prompt: {prompt}")
        response = main.promptToEvent(prompt)
        
        if isinstance(response, dict) and 'error' in response:
            logger.error(f"Error in prompt processing: {response['error']}")
            return jsonify(response), 400
            
        response_dict = response
        if 'action_type' not in response_dict:
            logger.error("Missing action_type in response")
            return jsonify({"error": "Invalid response format from AI service"}), 400

        if response_dict['action_type'] == 'create':
            if 'eventParams' not in response_dict or 'eventCompletion' not in response_dict:
                logger.error("Missing eventParams or eventCompletion in create action")
                return jsonify({"error": "Invalid event creation parameters"}), 400
            eventParams = response_dict['eventParams']
            if isinstance(eventParams, list) and len(eventParams) > 0:
                event_data = eventParams[0]
                try:
                    if main.formatEvent(event_data):
                        message = response_dict['eventCompletion']
                        return jsonify({"message": message, "success": True})
                    else:
                        logger.error("Failed to format event")
                        return jsonify({"error": "Failed to format event data"}), 400
                except Exception as e:
                    logger.error(f"Exception in formatEvent: {str(e)}")
                    return jsonify({"error": f"Error processing event: {str(e)}"}), 400
            else:
                logger.error("eventParams is not in the expected format")
                return jsonify({"error": "Invalid event parameters format"}), 400
        elif response_dict['action_type'] == 'view':
            if 'query_details' not in response_dict:
                logger.error("Missing query_details in view action")
                return jsonify({"error": "Missing event query parameters"}), 400
            query_details = response_dict['query_details']
            try:
                return jsonify(main.findEvent(query_details=query_details))
            except Exception as e:
                logger.error(f"Error in findEvent: {str(e)}")
                return jsonify({"error": f"Error finding events: {str(e)}"}), 400
        else:
            logger.error(f"Unknown action_type: {response_dict['action_type']}")
            return jsonify({"error": "Unsupported action type"}), 400
    except Exception as e:
        logger.error(f"Unexpected error in prompt endpoint: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

@app.route('/api/login')
def login():
    try:
        SCOPES = [
            'openid',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        client_secret_file = os.getenv('google_client_id_path')
        logger.info(f"Using client secret file: {client_secret_file}")
        if not os.path.exists(client_secret_file):
            logger.error(f"Client secret file not found at: {client_secret_file}")
            return jsonify({
                'error': 'Authentication failed',
                'message': f"Client secret file not found at: {client_secret_file}"
            }), 500

        flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes=SCOPES)
        flow.redirect_uri = redirect_url
        logger.info(f"Redirect URI set to: {flow.redirect_uri}")

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        session['state'] = state
        logger.info(f"Authorization URL: {authorization_url}")

        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        return jsonify({'error': 'Authentication failed', 'message': str(e)}), 500

@app.route('/auth/callback')
def auth_callback():
    try:
        code = request.args.get('code')
        if not code:
            logger.error("No code in request")
            return redirect(f"{frontend_url}?auth_error=no_code")

        token_url = "https://oauth2.googleapis.com/token"
        client_id = os.getenv('google_client_id')
        client_secret = os.getenv('google_client_secret')
        redirect_uri = os.getenv('redirect_url', f"{frontend_url}/auth/callback")

        logger.info(
            f"Exchanging code for tokens with data: {{'code': '{code}', 'client_id': '{client_id}', "
            f"'client_secret': '***', 'redirect_uri': '{redirect_uri}', 'grant_type': 'authorization_code'}}"
        )

        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        token_response = requests.post(token_url, data=token_data)
        if not token_response.ok:
            logger.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
            return redirect(f"{frontend_url}?auth_error=token_exchange_failed")

        tokens = token_response.json()
        logger.info("Received tokens: %s", {k: v if k not in ['id_token', 'access_token'] else v[:10] + '...' for k, v in tokens.items()})

        id_token = tokens.get('id_token')
        if not id_token:
            logger.error("No ID token received")
            return redirect(f"{frontend_url}?auth_error=no_id_token")

        # Decode the ID token without verifying signature
        user_data = jwt.decode(id_token, options={"verify_signature": False})
        logger.info("User authenticated: %s", user_data.get('email'))

        session.permanent = True
        session['user'] = {
            'id': user_data.get('sub'),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'picture': user_data.get('picture'),
            'authenticated': True,
            'login_time': datetime.utcnow().isoformat()
        }

        session['tokens'] = {
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token', ''),
            'id_token': tokens.get('id_token'),
            'expires_at': time.time() + tokens.get('expires_in', 3600)
        }

        user_email = user_data.get('email', '')
        # Redirect to the frontend home page with auth_success flag
        redirect_target = f"{frontend_url}?auth_success=true&user={user_email}"
        logger.info(f"Authentication successful, redirecting to: {redirect_target}")
        return redirect(redirect_target)

    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return redirect(f"{frontend_url}?auth_error=exception")

@app.route("/auth/user")
def get_user():
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify(user)

@app.route("/auth/logout")
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logged out successfully"})

@app.route("/auth/test-session")
def test_session():
    if "test_value" not in session:
        session["test_value"] = "Test value set at " + str(time.time())
        is_new = True
    else:
        is_new = False

    return jsonify({
        "session_working": True,
        "test_value": session.get("test_value"),
        "is_new_value": is_new,
        "session_data": {k: v for k, v in session.items() if k != "user"}
    })

@app.route('/api/check-auth')
def check_auth():
    logger.info(f"Check auth request received from: {request.remote_addr}")
    logger.info(f"Session cookie: {request.cookies.get(app.config['SESSION_COOKIE_NAME'])}")

    cookies_received = len(request.cookies) > 0
    cookie_names = list(request.cookies.keys())

    if 'user' not in session:
        logger.info("No user in session")
        return jsonify({
            'authenticated': False,
            'message': 'No user session found',
            'session_exists': 'session' in request.cookies,
            'cookies_received': cookies_received,
            'cookie_names': cookie_names
        })

    if 'tokens' not in session:
        logger.info("No tokens in session")
        return jsonify({
            'authenticated': False,
            'message': 'No tokens found',
            'session_exists': True,
            'cookies_received': cookies_received,
            'cookie_names': cookie_names
        })

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
    try:
        user_email = session.get('user', {}).get('email')
        if user_email:
            logger.info("Logging out user: %s", user_email)
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
    origin = request.headers.get('Origin', '')
    allowed_origins = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        "https://calgentic.com",
        "https://www.calgentic.com",
        "https://calgentic.onrender.com"
    ]
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', allowed_origins[0])

    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Expose-Headers', 'Content-Type, X-Auth-Token')
    response.headers.add('Vary', 'Origin, Access-Control-Request-Headers, Access-Control-Request-Method')
    if response.mimetype == 'application/json' and 'Content-Type' not in response.headers:
        response.headers.add('Content-Type', 'application/json')
    return response

def generate_new_token(refresh_token):
    try:
        token_endpoint = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': os.getenv('google_client_id'),
            'client_secret': os.getenv('google_client_secret'),
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }
        response = requests.post(token_endpoint, data=data)
        if not response.ok:
            raise Exception(f"Token refresh failed: {response.text}")
        tokens = response.json()
        return tokens.get('access_token')
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise

@app.route('/refresh-token', methods=['POST'])
def refresh_token_route():
    refresh_token_val = request.cookies.get('refresh_token')
    if not refresh_token_val:
        return jsonify({"error": "No refresh token"}), 401

    try:
        new_access_token = generate_new_token(refresh_token_val)
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

@app.route('/api/test-cookie', methods=['GET'])
def test_cookie():
    test_value = f"test-value-{int(time.time())}"
    resp = jsonify({
        "success": True,
        "message": "Test cookie set",
        "test_value": test_value,
        "cookies_received": len(request.cookies) > 0,
        "cookie_names": list(request.cookies.keys()) if request.cookies else []
    })
    resp.set_cookie('test_cookie', test_value, max_age=3600, path='/', domain=None, secure=True, httponly=False, samesite='None')
    return resp

@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # In production, use a proper WSGI server (e.g., Gunicorn or uWSGI)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=False)