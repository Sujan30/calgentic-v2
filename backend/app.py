import json
import os
import main
import requests
from flask import Flask, send_from_directory, jsonify, request, redirect, session
from flask_session import Session
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

# Determine environment
environment = os.environ.get("FLASK_ENV", "development")
frontend_url = os.getenv('frontend_url', 'http://localhost:8080')

# Session configuration - different for dev and prod
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=5)
app.config['SESSION_COOKIE_SECURE'] = environment == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_NAME'] = 'calgentic_session'

# Set cookie domain and SameSite based on environment
if environment == 'production':
    app.config['SESSION_COOKIE_DOMAIN'] = '.calgentic.onrender.com'
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True

else:
    # For development, don't set domain (defaults to current domain)
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize Flask-Session
Session(app)

# Enable CORS for allowed origins
CORS(app, 
     supports_credentials=True, 
     resources={r"/*": {
         "origins": [
             "http://localhost:8080",
             "http://127.0.0.1:8080",
             "http://localhost:8081",
             "http://127.0.0.1:8081",
             "http://localhost:5001",
             "http://127.0.0.1:5001",
             "https://calgentic.com",
             "https://www.calgentic.com",
             "https://calgentic.onrender.com",
         ],
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization", "Accept"],
         "expose_headers": ["Content-Type", "Authorization"],
         "max_age": 3600,
         "send_wildcard": False,
         "vary_header": True,
         "supports_credentials": True
     }}
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Google OAuth credentials from environment variables
GOOGLE_CLIENT_ID = os.getenv("google_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("google_client_secret")
redirect_url = os.getenv('redirect_url', 'http://localhost:5001/auth/callback')

logger.info(f"FRONTEND_URL set to: {frontend_url}")
logger.info(f"REDIRECT_URL set to: {redirect_url}")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise Exception("Google OAuth credentials not set. Check your environment variables.")

client_secret_file = os.getenv('credentials_path')
if not os.path.exists(client_secret_file):
    raise FileNotFoundError(f"Credentials file not found at: {client_secret_file}")

@app.before_request
def log_request_info():
    # Debug logging only; sensitive details should not be logged in production.
    logger.info('Request Method: %s', request.method)
    logger.info('Request URL: %s', request.url)
    logger.info('Request Headers: %s', dict(request.headers))
    logger.info('Request Body: %s', request.get_data())
    logger.info('Session: %s', session)
    logger.info('Cookies: %s', request.cookies)
    logger.info('Origin: %s', request.headers.get('Origin'))
    logger.info('Host: %s', request.headers.get('Host'))

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/prompt", methods=["POST", "OPTIONS"])
def onboard():
    logger.info("Received request to /prompt endpoint")

    # Handle OPTIONS preflight
    if request.method == "OPTIONS":
        logger.info("Handling OPTIONS request")
        response = app.make_default_options_response()
        origin = request.headers.get("Origin", "")
        allowed_origins = [
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:8081",
            "http://127.0.0.1:8081",
            "http://localhost:5001",
            "http://127.0.0.1:5001",
            "https://calgentic.com",
            "https://www.calgentic.com",
            "https://calgentic.onrender.com",
        ]
        response.headers["Access-Control-Allow-Origin"] = (
            origin if origin in allowed_origins else allowed_origins[0]
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "3600"
        return response

    try:
        data = request.get_json()
        logger.info("Received JSON data: %s", data)

        # ── Validate that both "prompt" and "userTimeZone" exist ─────────────────
        if not data or "prompt" not in data or "userTimeZone" not in data:
            logger.error("Missing 'prompt' or 'userTimeZone' in request body")
            return (
                jsonify({"error": "Request body must include both 'prompt' and 'userTimeZone'."}),
                400,
            )

        prompt = data["prompt"]
        user_tz = data["userTimeZone"]
        logger.info("Processing prompt: %s", prompt)
        logger.info("UserTimeZone: %s", user_tz)

        # CORS response headers
        response_headers = {
            "Access-Control-Allow-Origin": request.headers.get("Origin", "https://calgentic.com"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
            "Access-Control-Expose-Headers": "Content-Type, Authorization",
        }

        # ── Pass BOTH prompt and user_tz into promptToEvent ───────────────────────
        ai_response = main.promptToEvent(prompt, user_tz)

        if isinstance(ai_response, dict) and "error" in ai_response:
            logger.error("Error in prompt processing: %s", ai_response["error"])
            return jsonify(ai_response), 400, response_headers

        response_dict = ai_response
        if "action_type" not in response_dict:
            logger.error("Missing action_type in response")
            return (
                jsonify({"error": "Invalid response format from AI service"}),
                400,
                response_headers,
            )

        if response_dict["action_type"] == "create":
            if "eventParams" not in response_dict or "eventCompletion" not in response_dict:
                logger.error("Missing eventParams or eventCompletion in create action")
                return jsonify({"error": "Invalid event creation parameters"}), 400, response_headers

            eventParams = response_dict["eventParams"]
            if isinstance(eventParams, list) and len(eventParams) > 0:
                event_data = eventParams[0]

                # ── Inject the same user_tz into the event_data dict so formatEvent can pick it up ──
                event_data["timeZone"] = user_tz

                try:
                    result = main.formatEvent(event_data)
                    if result and result.get("success", False):
                        message = response_dict["eventCompletion"]
                        return jsonify({"message": message, "success": True}), 200, response_headers
                    else:
                        logger.error("Failed to format/create event: %s", result)
                        return jsonify({"error": "Failed to create event"}), 400, response_headers
                except Exception as e:
                    logger.error("Exception in formatEvent: %s", str(e))
                    return jsonify({"error": f"Error processing event: {str(e)}"}), 400, response_headers
            else:
                logger.error("eventParams is not in the expected format")
                return jsonify({"error": "Invalid event parameters format"}), 400, response_headers

        elif response_dict["action_type"] == "view":
            if "query_details" not in response_dict:
                logger.error("Missing query_details in view action")
                return jsonify({"error": "Missing event query parameters"}), 400, response_headers

            query_details = response_dict["query_details"]

            try:
                return jsonify(main.findEvent(query_details=query_details, user_tz=user_tz)), 200, response_headers
            except Exception as e:
                logger.error("Error in findEvent: %s", str(e))
                return jsonify({"error": f"Error finding events: {str(e)}"}), 400, response_headers

        else:
            logger.error("Unknown action_type: %s", response_dict["action_type"])
            return jsonify({"error": "Unsupported action type"}), 400, response_headers

    except Exception as e:
        logger.error("Unexpected error in prompt endpoint: %s", str(e))
        return (
            jsonify({"error": "An unexpected error occurred. Please try again."}),
            500,
            response_headers,
        )


@app.route('/api/login')
def login():
    try:
        SCOPES = [
            'openid',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        
        # Create OAuth flow using environment variables
        flow = InstalledAppFlow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_url]
                }
            },
            scopes=SCOPES
        )
        
        flow.redirect_uri = redirect_url
        logger.info(f"Redirect URI set to: {flow.redirect_uri}")

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to ensure we get refresh token
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
        logger.info("=== AUTH CALLBACK STARTED ===")
        logger.info(f"Request args: {dict(request.args)}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        code = request.args.get('code')
        if not code:
            logger.error("No code in request")
            return redirect(f"{frontend_url}/login?error=no_code")

        logger.info(f"OAuth code received: {code[:20]}...")

        token_url = "https://oauth2.googleapis.com/token"
        client_id = os.getenv('google_client_id')
        client_secret = os.getenv('google_client_secret')
        redirect_uri = os.getenv('redirect_url', 'http://localhost:5001/auth/callback')

        logger.info(f"Using client_id: {client_id}")
        logger.info(f"Using redirect_uri: {redirect_uri}")
        
        if not client_id or not client_secret:
            logger.error("Missing OAuth credentials!")
            return redirect(f"{frontend_url}/login?error=missing_credentials")

        logger.info(
            f"Exchanging code for tokens with data: {{'code': '{code[:20]}...', 'client_id': '{client_id}', "
            f"'client_secret': '***', 'redirect_uri': '{redirect_uri}', 'grant_type': 'authorization_code'}}"
        )

        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        logger.info("Making token exchange request...")
        token_response = requests.post(token_url, data=token_data)
        logger.info(f"Token response status: {token_response.status_code}")
        logger.info(f"Token response headers: {dict(token_response.headers)}")
        
        if not token_response.ok:
            logger.error(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
            return redirect(f"{frontend_url}/login?error=token_exchange_failed")

        tokens = token_response.json()
        logger.info("Received tokens: %s", {k: v if k not in ['id_token', 'access_token'] else v[:10] + '...' for k, v in tokens.items()})

        id_token = tokens.get('id_token')
        if not id_token:
            logger.error("No ID token received")
            return redirect(f"{frontend_url}/login?error=no_id_token")

        logger.info("Decoding ID token...")
        # Decode the ID token without verifying signature
        user_data = jwt.decode(id_token, options={"verify_signature": False})
        logger.info("User authenticated: %s", user_data.get('email'))
        logger.info("User data keys: %s", list(user_data.keys()))

        logger.info("Setting session data...")
        # Set session data
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

        # Log session data for debugging
        user_email = user_data.get('email', '')
        logger.info(f"Authentication successful for user: {user_email}")
        logger.info(f"Session data set: {dict(session)}")
        
        # Ensure session is saved before redirect
        session.modified = True
        logger.info("Session marked as modified")
        
        # Redirect directly to dashboard instead of frontend auth callback
        redirect_url_final = f"{frontend_url}/dashboard"
        logger.info(f"Redirecting directly to dashboard: {redirect_url_final}")
        logger.info("=== AUTH CALLBACK COMPLETED ===")
        return redirect(redirect_url_final)

    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return redirect(f"{frontend_url}/login?error=exception")

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

@app.route('/api/test-session', methods=['GET', 'POST'])
def test_session():
    if request.method == 'POST':
        # Set a test session value
        session['test_user'] = {
            'email': 'test@example.com',
            'name': 'Test User',
            'timestamp': datetime.utcnow().isoformat()
        }
        session.modified = True
        logger.info(f"Test session set: {dict(session)}")
        return jsonify({
            'success': True,
            'message': 'Test session created',
            'session_data': dict(session)
        })
    else:
        # Check if test session exists
        logger.info(f"Checking test session: {dict(session)}")
        return jsonify({
            'session_exists': 'test_user' in session,
            'session_data': dict(session),
            'cookies_received': len(request.cookies) > 0,
            'cookie_names': list(request.cookies.keys()),
            'environment': environment
        })

@app.route('/api/check-auth')
def check_auth():
    logger.info(f"Check auth request received from: {request.remote_addr}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"All cookies received: {dict(request.cookies)}")
    logger.info(f"Session cookie name: {app.config['SESSION_COOKIE_NAME']}")
    logger.info(f"Session contents: {dict(session)}")

    # Check if we have any session data
    if not session:
        logger.info("No session data found")
        return jsonify({
            'authenticated': False,
            'message': 'No session found',
            'debug': {
                'session_exists': False,
                'cookies_received': len(request.cookies) > 0,
                'cookie_names': list(request.cookies.keys()),
                'environment': environment
            }
        })

    # Check if user is in session
    if 'user' not in session:
        logger.info("No user in session")
        return jsonify({
            'authenticated': False,
            'message': 'No user session found',
            'debug': {
                'session_exists': True,
                'session_keys': list(session.keys()),
                'cookies_received': len(request.cookies) > 0,
                'cookie_names': list(request.cookies.keys()),
                'environment': environment
            }
        })

    # Check if tokens exist and are valid
    if 'tokens' not in session:
        logger.info("No tokens in session")
        return jsonify({
            'authenticated': False,
            'message': 'No tokens found',
            'debug': {
                'session_exists': True,
                'user_exists': True,
                'cookies_received': len(request.cookies) > 0,
                'cookie_names': list(request.cookies.keys()),
                'environment': environment
            }
        })

    tokens = session['tokens']
    if time.time() > tokens.get('expires_at', 0):
        logger.info("Tokens expired")
        return jsonify({
            'authenticated': False,
            'message': 'Authentication expired',
            'debug': {
                'session_exists': True,
                'user_exists': True,
                'token_expired_at': tokens.get('expires_at'),
                'current_time': time.time(),
                'cookies_received': len(request.cookies) > 0,
                'cookie_names': list(request.cookies.keys()),
                'environment': environment
            }
        })

    user_email = session['user'].get('email')
    logger.info(f"User authenticated successfully: {user_email}")
    return jsonify({
        'authenticated': True,
        'user': session['user'],
        'debug': {
            'session_exists': True,
            'user_exists': True,
            'tokens_valid': True,
            'cookies_received': len(request.cookies) > 0,
            'cookie_names': list(request.cookies.keys()),
            'environment': environment
        }
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
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:5001",
        "http://127.0.0.1:5001",
        "https://calgentic.com",
        "https://www.calgentic.com",
        "https://calgentic.onrender.com",
    ]
    
    # Log response details
    logger.info('Response Status: %s', response.status)
    logger.info('Response Headers: %s', dict(response.headers))
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = allowed_origins[0]

    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization'
    
    # Handle cookies based on environment
    if 'Set-Cookie' in response.headers:
        cookies = response.headers.getlist('Set-Cookie')
        response.headers.pop('Set-Cookie')  # Remove existing cookies
        
        for cookie in cookies:
            if environment == 'production':
                # Production: ensure SameSite=None and Secure
                if 'SameSite=None' not in cookie:
                    cookie = cookie.replace('SameSite=Lax', 'SameSite=None')
                if 'Secure' not in cookie:
                    cookie += '; Secure'
            else:
                # Development: use SameSite=Lax (no Secure needed for localhost)
                if 'SameSite=None' in cookie:
                    cookie = cookie.replace('SameSite=None', 'SameSite=Lax')
                # Remove Secure flag for localhost
                cookie = cookie.replace('; Secure', '')
                
            response.headers.add('Set-Cookie', cookie)
    
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

@app.route('/api/test-auth', methods=['GET'])
def test_auth():
    # Simulate what happens after successful OAuth
    session.permanent = True
    session['user'] = {
        'id': 'test_user_id',
        'email': 'test@example.com',
        'name': 'Test User',
        'picture': 'https://example.com/pic.jpg',
        'authenticated': True,
        'login_time': datetime.utcnow().isoformat()
    }

    session['tokens'] = {
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'id_token': 'test_id_token',
        'expires_at': time.time() + 3600
    }
    
    session.modified = True
    logger.info(f"Test auth session created: {dict(session)}")
    
    return jsonify({
        'success': True,
        'message': 'Test authentication session created',
        'session_data': dict(session)
    })

if __name__ == '__main__':
    # In production, use a proper WSGI server (e.g., Gunicorn or uWSGI)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=False)