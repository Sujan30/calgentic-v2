import json
import os
import main
import requests
from flask import Flask, send_from_directory, jsonify, request, redirect, session, abort
from flask_session import Session
from google_auth_oauthlib.flow import InstalledAppFlow
from flask_cors import CORS
from datetime import timedelta, datetime, timezone
import time
from dotenv import load_dotenv
import logging
import jwt
import uuid
from supabase import create_client, Client
from cryptography.fernet import Fernet
import base64

#hello world

# Load environment variables from .env file
load_dotenv()

start_time = time.time()
app = Flask(__name__, static_folder='static', static_url_path='')

# Use a strong secret key; load from environment in production
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    logger = logging.getLogger(__name__)
    supabase: Client = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Determine environment
environment = os.environ.get("FLASK_ENV", "development")
frontend_url = os.getenv('frontend_url', 'http://localhost:8080')

# Session configuration - different for dev and prod
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=5)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_NAME'] = 'calgentic_session'

# Set cookie domain and SameSite based on environment
if environment == 'production':
    app.config['SESSION_COOKIE_DOMAIN'] = '.calgentic.com'
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    # For development, don't set domain (defaults to current domain)
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False

# Initialize Flask-Session
Session(app)

# Enable CORS for allowed origins
CORS(app,
     supports_credentials=True,
     resources={r"/*": {
         "origins": [
             "https://calgentic.com",
             "https://www.calgentic.com"
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

# User Database Operations
def create_or_update_user(email, name, google_id=None, picture=None):
    """Create or update user in Supabase database"""
    if not supabase:
        return None
    
    try:
        # Check if user exists
        existing_user = supabase.table('users').select('*').eq('email', email).execute()
        
        user_data = {
            'email': email,
            'name': name,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if google_id:
            user_data['google_id'] = google_id
        if picture:
            user_data['picture'] = picture
            
        if existing_user.data:
            # Update existing user
            user_id = existing_user.data[0]['id']
            result = supabase.table('users').update(user_data).eq('id', user_id).execute()
            return result.data[0] if result.data else None
        else:
            # Create new user
            user_data['id'] = str(uuid.uuid4())
            user_data['created_at'] = datetime.now(timezone.utc).isoformat()
            result = supabase.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
            
    except Exception as e:
        return None

def get_user_by_email(email):
    """Get user from database by email"""
    if not supabase:
        return None
        
    try:
        result = supabase.table('users').select('*').eq('email', email).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        return None

def get_user_by_id(user_id):
    """Get user from database by ID"""
    if not supabase:
        return None
        
    try:
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        return None

# Prompt Database Operations
def create_prompt_log(user_email, user_id, prompt_text, ai_response=None, action_type=None, 
                     status='processing', error_message=None, user_timezone=None, 
                     processing_time_ms=None, token_usage=None, event_created=False, 
                     event_data=None, ip_address=None, user_agent=None):
    """Create a new prompt log entry in Supabase database"""
    if not supabase:
        return None
    
    try:
        prompt_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'user_email': user_email,
            'prompt_text': prompt_text,
            'ai_response': ai_response,
            'action_type': action_type,
            'status': status,
            'error_message': error_message,
            'user_timezone': user_timezone,
            'processing_time_ms': processing_time_ms,
            'token_usage': token_usage,
            'event_created': event_created,
            'event_data': event_data,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table('prompts').insert(prompt_data).execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        return None

def update_prompt_log(prompt_id, ai_response=None, status='success', error_message=None, 
                     processing_time_ms=None, token_usage=None, event_created=False, 
                     event_data=None, action_type=None):
    """Update an existing prompt log entry"""
    if not supabase:
        return None
        
    try:
        update_data = {
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        if ai_response is not None:
            update_data['ai_response'] = ai_response
        if status is not None:
            update_data['status'] = status
        if error_message is not None:
            update_data['error_message'] = error_message
        if processing_time_ms is not None:
            update_data['processing_time_ms'] = processing_time_ms
        if token_usage is not None:
            update_data['token_usage'] = token_usage
        if event_created is not None:
            update_data['event_created'] = event_created
        if event_data is not None:
            update_data['event_data'] = event_data
        if action_type is not None:
            update_data['action_type'] = action_type
            
        result = supabase.table('prompts').update(update_data).eq('id', prompt_id).execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        return None

def get_user_prompts(user_email, limit=50, offset=0):
    """Get prompts for a specific user"""
    if not supabase:
        return []
        
    try:
        result = supabase.table('prompts').select('*').eq('user_email', user_email).order('created_at', desc=True).limit(limit).offset(offset).execute()
        encryptor = PromptEncryptor()
        for prompt in result.data:
            try:
                prompt['prompt_text'] = encryptor.decrypt(prompt['prompt_text'])
            except Exception:
                prompt['prompt_text'] = '[decryption failed]'
        return result.data
    except Exception as e:
        return []

# Load Google OAuth credentials from environment variables
GOOGLE_CLIENT_ID = os.getenv("google_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("google_client_secret")
redirect_url = os.getenv('redirect_url', 'http://localhost:5001/auth/callback')

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise Exception("Google OAuth credentials not set. Check your environment variables.")

client_secret_file = os.getenv('credentials_path')
if not os.path.exists(client_secret_file):
    raise FileNotFoundError(f"Credentials file not found at: {client_secret_file}")

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


def require_tokens():
    tokens = session.get('tokens')
    if not tokens:
        abort(401, "Login required")
    return tokens

@app.route("/prompt", methods=["POST", "OPTIONS"])
def onboard():
    # Handle OPTIONS preflight
    if request.method == "OPTIONS":
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
            "https://api.calgentic.com",
            "https://www.api.calgentic.com"
        ]
        response.headers["Access-Control-Allow-Origin"] = (
            origin if origin in allowed_origins else allowed_origins[0]
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "3600"
        return response

    # Track processing time
    start_time = time.time()
    prompt_log_id = None
    
    # CORS response headers
    response_headers = {
        "Access-Control-Allow-Origin": request.headers.get("Origin", "https://calgentic.com"),
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
        "Access-Control-Expose-Headers": "Content-Type, Authorization",
    }

    try:
        data = request.get_json()

        # Get user information from session
        user_session = session.get("user")
        user_email = user_session.get('email') if user_session else "anonymous"
        user_id = user_session.get('db_user_id') if user_session else None
        tokens = require_tokens()
        # Only log if user is authenticated (has valid user_id)
        should_log = user_email != "anonymous" and user_id is not None
        
        # Validate that both "prompt" and "userTimeZone" exist
        if not data or "prompt" not in data or "userTimeZone" not in data:
            error_msg = "Request body must include both 'prompt' and 'userTimeZone'."
            
            # Log failed request only if user is authenticated
            if should_log:
                try:
                    encryptor = PromptEncryptor()
                    create_prompt_log(
                        user_email=user_email,
                        user_id=user_id,
                        prompt_text=encryptor.encrypt(data.get("prompt", "") if data else ""),
                        status='error',
                        error_message=error_msg,
                        user_timezone=data.get("userTimeZone") if data else None,
                        ip_address=str(request.remote_addr),
                        user_agent=request.headers.get('User-Agent', '')
                    )
                except Exception as log_error:
                    print(f'error {log_error}')
            
            return jsonify({"error": error_msg}), 400, response_headers

        prompt = data["prompt"]
        user_tz = data["userTimeZone"]

        # Send plain prompt to AI
        ai_response = main.promptToEvent(prompt, user_tz)
        print("AI response:", ai_response)

        # Encrypt only for storage
        encryptor = PromptEncryptor()
        encrypted_prompt = encryptor.encrypt(prompt)

        # Create initial prompt log entry only if user is authenticated
        if should_log:
            try:
                prompt_log = create_prompt_log(
                    user_email=user_email,
                    user_id=user_id,
                    prompt_text=encrypted_prompt,
                    status='processing',
                    user_timezone=user_tz,
                    ip_address=str(request.remote_addr),
                    user_agent=request.headers.get('User-Agent', '')
                )
                prompt_log_id = prompt_log.get('id') if prompt_log else None
            except Exception as log_error:
                prompt_log_id = None
        else:
            prompt_log_id = None

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Determine status and error message
        if isinstance(ai_response, dict) and "error" in ai_response:
            status = "error"
            error_message = ai_response.get("error")
        else:
            status = "success"
            error_message = None

        # Update prompt log with final status, response, and processing time
        if prompt_log_id:
            try:
                update_prompt_log(
                    prompt_id=prompt_log_id,
                    ai_response=ai_response,
                    status=status,
                    error_message=error_message,
                    processing_time_ms=processing_time_ms,
                    action_type=ai_response.get("action_type") if isinstance(ai_response, dict) else None,
                    event_data=ai_response.get("eventParams") if isinstance(ai_response, dict) else None
                )
            except Exception as log_error:
                pass

        response_dict = ai_response
        if "action_type" not in response_dict:
            error_msg = "Invalid response format from AI service"
            
            if prompt_log_id:
                update_prompt_log(
                    prompt_id=prompt_log_id,
                    ai_response=response_dict,
                    status='error',
                    error_message=error_msg,
                    processing_time_ms=processing_time_ms
                )
            
            return jsonify({"error": error_msg}), 400, response_headers

        action_type = response_dict["action_type"]
        event_created = False
        event_data = None

        if action_type == "create":
            if "eventParams" not in response_dict or "eventCompletion" not in response_dict:
                error_msg = "Invalid event creation parameters"
                
                if prompt_log_id:
                    update_prompt_log(
                        prompt_id=prompt_log_id,
                        ai_response=response_dict,
                        status='error',
                        error_message=error_msg,
                        processing_time_ms=processing_time_ms
                    )
                
                return jsonify({"error": error_msg}), 400, response_headers

            eventParams = response_dict["eventParams"]
            if isinstance(eventParams, list) and len(eventParams) > 0:
                event_data = eventParams[0]
                event_data["timeZone"] = user_tz

                try:
                    print("Event data to formatEvent:", event_data)
                    # Pass session to formatEvent
                    result, refreshed_tokens = main.formatEvent(tokens, event_data)
                    session['tokens'] = refreshed_tokens
                    print("Result from formatEvent:", result)
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    
                    if result and result.get("success", False):
                        event_created = True
                        message = response_dict["eventCompletion"]
                        
                        # Update prompt log with success
                        if prompt_log_id:
                            try:
                                update_prompt_log(
                                    prompt_id=prompt_log_id,
                                    ai_response=response_dict,
                                    status='success',
                                    processing_time_ms=processing_time_ms,
                                    event_created=True,
                                    event_data=event_data,
                                    action_type=action_type
                                )
                            except Exception as log_error:
                                pass
                        
                        return jsonify({"message": message, "success": True}), 200, response_headers
                    else:
                        error_msg = f"Failed to create event: {result}"
                        
                        if prompt_log_id:
                            try:
                                update_prompt_log(
                                    prompt_id=prompt_log_id,
                                    ai_response=response_dict,
                                    status='error',
                                    error_message=error_msg,
                                    processing_time_ms=processing_time_ms,
                                    event_data=event_data,
                                    action_type=action_type
                                )
                            except Exception as log_error:
                                pass
                        
                        return jsonify({"error": "Failed to create event"}), 400, response_headers
                        
                except Exception as e:
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    error_msg = f"Error processing event: {str(e)}"
                    
                    if prompt_log_id:
                        try:
                            update_prompt_log(
                                prompt_id=prompt_log_id,
                                ai_response=response_dict,
                                status='error',
                                error_message=error_msg,
                                processing_time_ms=processing_time_ms,
                                event_data=event_data,
                                action_type=action_type
                            )
                        except Exception as log_error:
                            pass
                    
                    return jsonify({"error": error_msg}), 400, response_headers
            else:
                processing_time_ms = int((time.time() - start_time) * 1000)
                error_msg = "Invalid event parameters format"
                
                if prompt_log_id:
                    try:
                        update_prompt_log(
                            prompt_id=prompt_log_id,
                            ai_response=response_dict,
                            status='error',
                            error_message=error_msg,
                            processing_time_ms=processing_time_ms,
                            action_type=action_type
                        )
                    except Exception as log_error:
                        pass
                
                return jsonify({"error": error_msg}), 400, response_headers

        elif action_type == "view":
            if "query_details" not in response_dict:
                error_msg = "Missing event query parameters"
                
                if prompt_log_id:
                    try:
                        update_prompt_log(
                            prompt_id=prompt_log_id,
                            ai_response=response_dict,
                            status='error',
                            error_message=error_msg,
                            processing_time_ms=processing_time_ms,
                            action_type=action_type
                        )
                    except Exception as log_error:
                        pass
                
                return jsonify({"error": error_msg}), 400, response_headers

            query_details = response_dict["query_details"]

            try:
                # Pass session to findEvent
                view_result , refreshed_tokens = main.findEvent(session=tokens, query_details=query_details, user_tz=user_tz)
                session['tokens'] = refreshed_tokens
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Update prompt log with success
                if prompt_log_id:
                    try:
                        update_prompt_log(
                            prompt_id=prompt_log_id,
                            ai_response=response_dict,
                            status='success',
                            processing_time_ms=processing_time_ms,
                            action_type=action_type,
                            event_data=query_details
                        )
                    except Exception as log_error:
                        pass
                
                return jsonify(view_result), 200, response_headers
                
            except Exception as e:
                processing_time_ms = int((time.time() - start_time) * 1000)
                error_msg = f"Error finding events: {str(e)}"
                
                if prompt_log_id:
                    try:
                        update_prompt_log(
                            prompt_id=prompt_log_id,
                            ai_response=response_dict,
                            status='error',
                            error_message=error_msg,
                            processing_time_ms=processing_time_ms,
                            action_type=action_type
                        )
                    except Exception as log_error:
                        pass
                
                return jsonify({"error": error_msg}), 400, response_headers

        elif action_type == "delete":
            if "query_details" not in response_dict:
                error_msg = "Missing event query parameters for deletion"
                
                if prompt_log_id:
                    try:
                        update_prompt_log(
                            prompt_id=prompt_log_id,
                            ai_response=response_dict,
                            status='error',
                            error_message=error_msg,
                            processing_time_ms=processing_time_ms,
                            action_type=action_type
                        )
                    except Exception as log_error:
                        pass
                
                return jsonify({"error": error_msg}), 400, response_headers

            query_details = response_dict["query_details"]
            
            try:
                # First find the event to get its ID
                find_result, refreshed_tokens = main.findEvent(session=session, query_details=query_details, user_tz=user_tz)
                session['tokens'] = refreshed_tokens
                
                if find_result.get("success") and find_result.get("events") and len(find_result["events"]) > 0:
                    # Delete the first matching event
                    event_to_delete = find_result["events"][0]
                    delete_result, refreshed_tokens = main.deleteEvent(
                        session=tokens,
                        eventId=event_to_delete.get("id"),
                        calendarId=query_details.get("calendarId", "primary")
                    )
                    session['tokens'] = refreshed_tokens
                    
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Update prompt log
                    if prompt_log_id:
                        try:
                            update_prompt_log(
                                prompt_id=prompt_log_id,
                                ai_response=response_dict,
                                status='success' if delete_result.get("success") else 'error',
                                error_message=delete_result.get("error") if not delete_result.get("success") else None,
                                processing_time_ms=processing_time_ms,
                                action_type=action_type,
                                event_data=query_details
                            )
                        except Exception as log_error:
                            pass
                    
                    return jsonify(delete_result), 200 if delete_result.get("success") else 400, response_headers
                else:
                    error_msg = "No matching event found to delete"
                    
                    if prompt_log_id:
                        try:
                            update_prompt_log(
                                prompt_id=prompt_log_id,
                                ai_response=response_dict,
                                status='error',
                                error_message=error_msg,
                                processing_time_ms=int((time.time() - start_time) * 1000),
                                action_type=action_type
                            )
                        except Exception as log_error:
                            pass
                    
                    return jsonify({
                        "success": False,
                        "message": error_msg
                    }), 404, response_headers
                    
            except Exception as e:
                processing_time_ms = int((time.time() - start_time) * 1000)
                error_msg = f"Error deleting event: {str(e)}"
                
                if prompt_log_id:
                    try:
                        update_prompt_log(
                            prompt_id=prompt_log_id,
                            ai_response=response_dict,
                            status='error',
                            error_message=error_msg,
                            processing_time_ms=processing_time_ms,
                            action_type=action_type
                        )
                    except Exception as log_error:
                        pass
                
                return jsonify({"error": error_msg}), 400, response_headers

        else:
            error_msg = f"Unsupported action type: {action_type}"
            
            if prompt_log_id:
                try:
                    update_prompt_log(
                        prompt_id=prompt_log_id,
                        ai_response=response_dict,
                        status='error',
                        error_message=error_msg,
                        processing_time_ms=processing_time_ms,
                        action_type=action_type
                    )
                except Exception as log_error:
                    pass
            
            return jsonify({"error": "Unsupported action type"}), 400, response_headers

    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        error_msg = f"An unexpected error occurred: {str(e)}"
        
        if prompt_log_id:
            try:
                update_prompt_log(
                    prompt_id=prompt_log_id,
                    status='error',
                    error_message=error_msg,
                    processing_time_ms=processing_time_ms
                )
            except Exception as log_error:
                pass
        
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500, response_headers

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

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to ensure we get refresh token
        )
        session['state'] = state

        return redirect(authorization_url)
    except Exception as e:
        return jsonify({'error': 'Authentication failed', 'message': str(e)}), 500

@app.route('/auth/callback')
def auth_callback():
    try:
        code = request.args.get('code')
        if not code:
            return redirect(f"{frontend_url}/login?error=no_code")

        token_url = "https://oauth2.googleapis.com/token"
        client_id = os.getenv('google_client_id')
        client_secret = os.getenv('google_client_secret')
        redirect_uri = os.getenv('redirect_url', 'http://localhost:5001/auth/callback')
        
        if not client_id or not client_secret:
            return redirect(f"{frontend_url}/login?error=missing_credentials")

        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        token_response = requests.post(token_url, data=token_data)
        
        if not token_response.ok:
            return redirect(f"{frontend_url}/login?error=token_exchange_failed")

        tokens = require_tokens()

        id_token = tokens.get('id_token')
        if not id_token:
            return redirect(f"{frontend_url}/login?error=no_id_token")

        # Decode the ID token without verifying signature
        user_data = jwt.decode(id_token, options={"verify_signature": False})

        # Save or update user in Supabase database
        user_email = user_data.get('email')
        user_name = user_data.get('name')
        google_id = user_data.get('sub')
        picture = user_data.get('picture')
        
        db_user = create_or_update_user(
            email=user_email,
            name=user_name,
            google_id=google_id,
            picture=picture
        )
        
        # Set session data
        session.permanent = True
        
        # Include database user ID if available
        user_session_data = {
            'id': user_data.get('sub'),
            'email': user_email,
            'name': user_name,
            'picture': picture,
            'authenticated': True,
            'login_time': datetime.now(timezone.utc).isoformat()
        }
        
        # Add database user ID if available
        if db_user and db_user.get('id'):
            user_session_data['db_user_id'] = db_user['id']
            
        session['user'] = user_session_data

        session['tokens'] = {
            'access_token': tokens.get('access_token'),
            'refresh_token': tokens.get('refresh_token', ''),
            'id_token': tokens.get('id_token'),
            'expires_at': time.time() + tokens.get('expires_in', 3600)
        }
        
        # Ensure session is saved before redirect
        session.modified = True
        
        # Redirect directly to dashboard instead of frontend auth callback
        redirect_url_final = f"{frontend_url}/dashboard"
        return redirect(redirect_url_final)

    except Exception as e:
        import traceback
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
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        session.modified = True
        return jsonify({
            'success': True,
            'message': 'Test session created',
            'session_data': dict(session)
        })
    else:
        # Check if test session exists
        return jsonify({
            'session_exists': 'test_user' in session,
            'session_data': dict(session),
            'cookies_received': len(request.cookies) > 0,
            'cookie_names': list(request.cookies.keys()),
            'environment': environment
        })

@app.route('/api/check-auth')
def check_auth():
    # Check if we have any session data
    if not session:
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
        session.clear()
        response = jsonify({
            "success": True,
            "message": "Successfully logged out"
        })
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        response = jsonify({
            "success": False,
            "error": str(e)
        })
        response.headers['Content-Type'] = 'application/json'
        return response, 500

@app.route('/ping')
def ping():
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - start_time,
        'status_code ' : 200
    }

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
        "https://api.calgentic.com",
        "https://www.api.calgentic.com"
    ]
    
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
        'login_time': datetime.now(timezone.utc).isoformat()
    }

    session['tokens'] = {
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'id_token': 'test_id_token',
        'expires_at': time.time() + 3600
    }
    
    session.modified = True
    
    return jsonify({
        'success': True,
        'message': 'Test authentication session created',
        'session_data': dict(session)
    })

@app.route('/api/user/profile')
def get_user_profile():
    """Get current user's profile from database"""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get user from database if we have db_user_id
    if user.get('db_user_id'):
        db_user = get_user_by_id(user['db_user_id'])
        if db_user:
            return jsonify({
                'success': True,
                'user': {
                    'id': db_user['id'],
                    'email': db_user['email'],
                    'name': db_user['name'],
                    'picture': db_user.get('picture'),
                    'google_id': db_user.get('google_id'),
                    'created_at': db_user.get('created_at'),
                    'updated_at': db_user.get('updated_at')
                }
            })
    
    # Fallback to session data
    return jsonify({
        'success': True,
        'user': user,
        'note': 'Data from session (database user not found)'
    })

@app.route('/api/user/update', methods=['POST'])
def update_user_profile():
    """Update current user's profile"""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Only allow updating name for now
        name = data.get('name')
        if not name:
            return jsonify({"error": "Name is required"}), 400
        
        # Update in database
        db_user = create_or_update_user(
            email=user['email'],
            name=name,
            google_id=user.get('id'),
            picture=user.get('picture')
        )
        
        if db_user:
            # Update session
            session['user']['name'] = name
            session['user']['db_user_id'] = db_user['id']
            session.modified = True
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'user': {
                    'id': db_user['id'],
                    'email': db_user['email'],
                    'name': db_user['name'],
                    'picture': db_user.get('picture'),
                    'updated_at': db_user.get('updated_at')
                }
            })
        else:
            return jsonify({"error": "Failed to update profile"}), 500
            
    except Exception as e:
        return jsonify({"error": "Failed to update profile"}), 500

@app.route('/api/users', methods=['GET'])
def list_users():
    """List all users (admin endpoint - you may want to add admin authentication)"""
    if not supabase:
        return jsonify({"error": "Database not configured"}), 500
    
    try:
        result = supabase.table('users').select('id,email,name,created_at,updated_at').execute()
        return jsonify({
            'success': True,
            'users': result.data,
            'count': len(result.data)
        })
    except Exception as e:
        return jsonify({"error": "Failed to list users"}), 500

@app.route('/api/prompts', methods=['GET'])
def get_user_prompt_history():
    """Get current user's prompt history"""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)  # Max 100 per page
        offset = (page - 1) * limit
        
        user_email = user['email']
        prompts = get_user_prompts(user_email, limit=limit, offset=offset)
        
        # Get total count for pagination
        if supabase:
            count_result = supabase.table('prompts').select('id', count='exact').eq('user_email', user_email).execute()
            total_count = count_result.count if hasattr(count_result, 'count') else len(prompts)
        else:
            total_count = len(prompts)
        
        return jsonify({
            'success': True,
            'prompts': prompts,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        })
    except Exception as e:
        return jsonify({"error": "Failed to retrieve prompt history"}), 500

@app.route('/api/prompts/<prompt_id>', methods=['GET'])
def get_prompt_details(prompt_id):
    """Get details of a specific prompt"""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    
    if not supabase:
        return jsonify({"error": "Database not configured"}), 500
    
    try:
        # Get prompt and verify it belongs to the user
        result = supabase.table('prompts').select('*').eq('id', prompt_id).eq('user_email', user['email']).execute()
        
        if not result.data:
            return jsonify({"error": "Prompt not found"}), 404
        
        encryptor = PromptEncryptor()
        prompt = result.data[0]
        try:
            prompt['prompt_text'] = encryptor.decrypt(prompt['prompt_text'])
        except Exception:
            prompt['prompt_text'] = '[decryption failed]'
        return jsonify({
            'success': True,
            'prompt': prompt
        })
    except Exception as e:
        return jsonify({"error": "Failed to retrieve prompt details"}), 500

@app.route('/api/prompts/stats', methods=['GET'])
def get_user_prompt_stats():
    """Get user's prompt usage statistics"""
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    
    if not supabase:
        return jsonify({"error": "Database not configured"}), 500
    
    try:
        user_email = user['email']
        
        # Get total prompts
        total_result = supabase.table('prompts').select('id', count='exact').eq('user_email', user_email).execute()
        total_prompts = total_result.count if hasattr(total_result, 'count') else 0
        
        # Get success/error counts
        success_result = supabase.table('prompts').select('id', count='exact').eq('user_email', user_email).eq('status', 'success').execute()
        success_count = success_result.count if hasattr(success_result, 'count') else 0
        
        error_result = supabase.table('prompts').select('id', count='exact').eq('user_email', user_email).eq('status', 'error').execute()
        error_count = error_result.count if hasattr(error_result, 'count') else 0
        
        # Get events created count
        events_result = supabase.table('prompts').select('id', count='exact').eq('user_email', user_email).eq('event_created', True).execute()
        events_created = events_result.count if hasattr(events_result, 'count') else 0
        
        # Get recent prompts for activity
        recent_prompts = supabase.table('prompts').select('created_at,status,action_type').eq('user_email', user_email).order('created_at', desc=True).limit(10).execute()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_prompts': total_prompts,
                'successful_prompts': success_count,
                'failed_prompts': error_count,
                'events_created': events_created,
                'success_rate': round((success_count / total_prompts * 100), 2) if total_prompts > 0 else 0
            },
            'recent_activity': recent_prompts.data
        })
    except Exception as e:
        return jsonify({"error": "Failed to retrieve statistics"}), 500

@app.route('/api/admin/prompts', methods=['GET'])
def get_all_prompts():
    """Get all prompts (admin endpoint)"""
    # Note: You should add proper admin authentication here
    if not supabase:
        return jsonify({"error": "Database not configured"}), 500
    
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 per page
        offset = (page - 1) * limit
        
        result = supabase.table('prompts').select('*').order('created_at', desc=True).limit(limit).offset(offset).execute()
        
        # Get total count
        count_result = supabase.table('prompts').select('id', count='exact').execute()
        total_count = count_result.count if hasattr(count_result, 'count') else len(result.data)
        
        return jsonify({
            'success': True,
            'prompts': result.data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        })
    except Exception as e:
        return jsonify({"error": "Failed to retrieve prompts"}), 500



class PromptEncryptor:
    def __init__(self):
        key = os.environ.get('PROMPT_ENCRYPTION_KEY')
        if not key:
            raise Exception("PROMPT_ENCRYPTION_KEY not set in environment variables.")
        self.fernet = Fernet(key.encode())

    def encrypt(self, text):
        return base64.b64encode(self.fernet.encrypt(text.encode())).decode()

    def decrypt(self, token):
        return self.fernet.decrypt(base64.b64decode(token.encode())).decode()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=False)