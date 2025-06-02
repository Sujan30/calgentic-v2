import os
import flask
import os.path
import datetime
import pytz  # Add this import at the top

from openai import OpenAI
from dotenv import load_dotenv

import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]


app = flask.Flask(__name__)

creds = None
service = None
calendarId = None




def calendarAuth():
    global creds # Make sure 'creds' is accessible outside this function if needed

    # Get tokens from session
    session = flask.session
    if not session or 'tokens' not in session:
        print("No tokens found in session")
        raise Exception("Authentication required. Please log in through the web interface.")

    tokens = session['tokens']
    if not tokens or 'access_token' not in tokens:
        print("No access token found in session")
        raise Exception("Authentication required. Please log in through the web interface.")

    try:
        # Create credentials from session tokens
        creds = Credentials(
            token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            scopes=SCOPES
        )
        print("Successfully created credentials from session tokens")
    except Exception as e:
        print(f"Error creating credentials from session tokens: {e}")
        raise Exception("Failed to create credentials from session tokens")

    # Check if token needs refresh
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Update session with new tokens
            session['tokens']['access_token'] = creds.token
            session['tokens']['expires_at'] = creds.expiry.timestamp() if creds.expiry else None
            print("Successfully refreshed tokens")
        except Exception as e:
            print(f"Error refreshing tokens: {e}")
            raise Exception("Failed to refresh tokens")

    return creds

"""

def deleteEvent(date, title, start, end, calendarId='primary'):
    try:
        global service
        global creds
        calendarAuth()
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().delete(calendarId=calendarId, eventId=eventId).execute()
        return True
    except Exception as e:
        print(f"Error in deleteEvent: {e}")
        return False
"""


    

def createEvent(summary, description, start_iso, end_iso=None, calendar_id="primary", user_tz="UTC"):
    """
    Create a Google Calendar event using exactly the user's IANA timezone (user_tz).
    - `start_iso` and `end_iso` must already be full ISO‐8601 strings with offset (e.g. "2025-06-02T17:00:00+02:00").
    - `user_tz` is something like "Europe/Paris" or "America/Los_Angeles".
    """
    global service, creds

    # Ensure credentials exist
    if creds is None:
        calendarAuth()

    if service is None and creds is not None:
        service = build("calendar", "v3", credentials=creds)

    if not summary or not start_iso:
        print("Missing required parameters for createEvent")
        return False

    try:
        # Now that ChatGPT has given us a full ISO‐8601 with offset in start_iso,
        # we can parse it into a tz-aware datetime:
        start_dt = datetime.datetime.fromisoformat(start_iso)
        # If end_iso is omitted, default to 1 hour after:
        if not end_iso or end_iso == "":
            end_dt = start_dt + datetime.timedelta(hours=1)
            end_iso = end_dt.isoformat()
        else:
            end_dt = datetime.datetime.fromisoformat(end_iso)

        if end_dt <= start_dt:
            print("Error: End time must be after start time")
            return False

    except ValueError as e:
        print(f"Invalid datetime format: {e}")
        return False

    # Use the USER’S timezone (user_tz), not server’s. Do NOT compute server‐side tz anymore.
    event_body = {
        "summary": summary,
        "description": description or "",
        "start": {
            "dateTime": start_iso,   # e.g. "2025-06-02T17:00:00+02:00"
            "timeZone": user_tz,     # e.g. "Europe/Paris"
        },
        "end": {
            "dateTime": end_iso,
            "timeZone": user_tz,
        },
    }

    print(f"Event object being sent to Google: {event_body}")

    # Retry logic for timeouts, etc.
    import socket

    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            created = service.events().insert(calendarId=calendar_id, body=event_body).execute()
            print(f"Event created: {created.get('htmlLink')}")
            socket.setdefaulttimeout(original_timeout)
            return created
        except socket.timeout:
            retry_count += 1
            print(f"Request timed out. Retry attempt {retry_count} of {max_retries}")
            if retry_count >= max_retries:
                print("Max retries reached. Could not create event.")
                socket.setdefaulttimeout(original_timeout)
                return False
        except HttpError as error:
            print(f"HTTP error occurred: {error}")
            socket.setdefaulttimeout(original_timeout)
            return False
        except Exception as e:
            print(f"Unexpected error in createEvent: {str(e)}")
            socket.setdefaulttimeout(original_timeout)
            return False

    socket.setdefaulttimeout(original_timeout)
    return False


def getEvents(calendarId='primary', day=None):
    if day is None:
        # Initialize to the current UTC time if no day is provided
        day = datetime.datetime.now(datetime.timezone.utc).isoformat()
       
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=day,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

def intializeDiffCalendarID(calId):
   try:
      global calendarId
      calendar_list = service.calendarList().list().execute()
      for calendar in calendar_list.get('items'):
        if calendar.get('id') == calId:
            calendarId = calId
            break
                
   except Exception as e:
      print(f'Calendar ID not found: {e}')
      raise e


def askPrompt():
    input_prompt = input("What's coming up next?': ")
    return input_prompt




def promptToEvent(prompt, user_tz):
    try:
        # Initialize OpenAI client with minimal configuration
        client = OpenAI(
            api_key=os.getenv('openai_key_v3'),
            base_url="https://api.openai.com/v1"  # Explicitly set the base URL
        )
        
        # Get current date and timezone for reference
        
        

        zone = pytz.timezone(user_tz)
        now_local = datetime.datetime.now(zone)
        today_str = now_local.strftime("%Y-%m-%d")           # e.g. "2025-06-01"
        time_str  = now_local.strftime("%H:%M:%S")           # e.g. "14:23:45"
        tz_offset = now_local.strftime("%z")                 # e.g. "-0700"
        # Insert the colon so GPT sees "-07:00":
        tz_offset = f"{tz_offset[:3]}:{tz_offset[3:]}"
        
        print(f"Local timezone offset: {tz_offset}")
        
        modified_prompt = f"""
        You are a calendar assistant. Given the user's input, determine if they want to create a new event or view existing events.
        
        Today's date is {today_str} in the timezone {time_str} in the time zone {tz_offset} which is the users time zone as {user_tz}
        When interpreting “tomorrow at 5pm”, interpret “5pm” in exactly {user_tz} (including DST).  
        If they want to create an event, return raw JSON only:
        
        When interpreting dates and times:
        - For relative dates like "tomorrow", "next week", etc., calculate the actual date based on today's date.
        - Always use the current year ({today_str.year}) for dates unless a specific year is mentioned.
        - Never schedule events in the past.
        - When a user specifies a time (like 9 AM), use that EXACT time. Do not adjust for any timezone differences.
        - Use the user's local timezone offset of {tz_offset} in the output.
        
        - If they want to create an event, return the following JSON structure:
        - factor in the timezone offset in the output, including daylight savings time, so if a user says 6 pm before DST, it should still schedule it for 6pm not for 7pm
          
          {{
            "action_type": "create",
            "eventParams": [
              {{
                "summary": "Event title",
                "description": "Event details",
                "start": "YYYY-MM-DDTHH:MM:SS{tz_offset}",
                "end": "YYYY-MM-DDTHH:MM:SS{tz_offset}",
                "calendarId": "primary"
              }}
            ],
            "eventCompletion" : "A little summary about the event, that acts as a confirmation"
          }}
          
        
        - If they want to view an event, return:
            - At least one of the following fields must be included: `date`, `title`, `start`, `end`, `calendarId`.
          {{
            "action_type": "view",
            "query_details": {{
                "date" : "date of the event they want to view",
                "title" : "title of the event they want to view",
                "start": "YYYY-MM-DDTHH:MM:SS{tz_offset}",
                "end": "YYYY-MM-DDTHH:MM:SS{tz_offset}",
                "calendarId": "primary"
            }}
          }}
          - If they want to delete an event
            - atleast one of the following fields must be included: `date`, `title`, `start`, `end`
            - if calendarID is provided, then change the calendarID to the one provided, else assume it is primary
            -if only calendarID is provided, then don't do anything. 
            return the following JSON structure:
          {{
            "action_type": "delete",
            "query_details": {{
                "date" : "date of the event they want to view",
                "title" : "title of the event they want to view",
                "start": "YYYY-MM-DDTHH:MM:SS{tz_offset}",
                "end": "YYYY-MM-DDTHH:MM:SS{tz_offset}",
                "calendarId": "primary"
            }}
          }}
        
        Ensure the response is **valid JSON format**. Do not include markdown formatting like ```json at the beginning or ``` at the end. Just return the raw JSON.
        
        IMPORTANT: When the user specifies a time like "9 AM", make sure to use exactly 09:00:00 in the output, not 08:00:00 or any other time. Do not adjust the time in any way.
        
        User input: {prompt}
        """
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": modified_prompt}]
        )
        
        if not response or not response.choices or not response.choices[0]:
            print("Invalid response from OpenAI API")
            return {
                "error": "Invalid response from AI service",
                "message": "The AI service returned an invalid response. Please try again."
            }
        
        content = response.choices[0].message.content
        print(f"data from chatgpt {content}")
        
        # Strip markdown code block formatting if present
        if "```" in content:
            # Remove all occurrences of ```json or ``` from the content
            content = content.replace("```json", "").replace("```", "").strip()
        
        # Add error handling for JSON parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response after stripping: {content}")
            # Return a structured error response
            return {
                "error": "Invalid JSON response from ChatGPT",
                "raw_response": content
            }
    except Exception as e:
        print(f"Error in promptToEvent: {str(e)}")
        return {
            "error": "Error processing prompt",
            "message": "An error occurred while processing the prompt"
        }

def formatEvent(event):
    try:
        # Print the event data for debugging
        print(f"Event data received: {event}")
        print(f"Event data type: {type(event)}")
        
        # Check if all required keys exist
        required_keys = ['summary', 'description', 'start', 'end']
        for key in required_keys:
            if key not in event:
                print(f"Missing required key: {key}")
                return {
                    "success": False,
                    "message": f"Missing required key: {key}",
                    "error": f"Event data is missing the required '{key}' field"
                }
        
        summary = event['summary']
        description = event['description']
        start = event['start']
        end = event['end']
        calendarId = event.get('calendarId', 'primary')  # Use get with default value
        
        # Print the extracted values for debugging
        print(f"Summary: {summary}")
        print(f"Description: {description}")
        print(f"Start: {start}")
        print(f"End: {end}")
        print(f"CalendarId: {calendarId}")
        
        try:
            result = createEvent(summary, description, start, end, calendarId)
            if result:
                return {
                    "success": True,
                    "message": "Event created successfully",
                    "event": {
                        "summary": summary,
                        "description": description,
                        "start": start,
                        "end": end,
                        "calendarId": calendarId,
                        "link": result.get('htmlLink', '')
                    }
                }
            else:
                print("Error in createEvent function")
                return {
                    "success": False,
                    "message": "Failed to create event",
                    "error": "Unknown error in createEvent function"
                }
        except Exception as e:
            print(f"Error in createEvent: {str(e)}")
            return {
                "success": False,
                "message": "Error creating event",
                "error": str(e)
            }
    except Exception as e:
        print(f"Error in formatEvent: {str(e)}")
        import traceback
        traceback.print_exc()  # Print the full stack trace
        return {
            "success": False,
            "message": "Error formatting event",
            "error": str(e)
        }
def findEvent(query_details, user_tz):
    """
    Finds events based on provided criteria in the user’s timezone.
    - query_details may include:
        - date:       "YYYY-MM-DD"
        - title:      string
        - start:      full ISO-8601 string with offset (e.g. "2025-06-02T17:00:00+02:00")
        - end:        full ISO-8601 string with offset
        - calendarId: string (defaults to "primary")
    - user_tz is the user’s IANA timezone (e.g. "America/Los_Angeles").
    """
    global service, creds

    # Initialize Google Calendar service if needed
    if service is None and creds is not None:
        service = build("calendar", "v3", credentials=creds)

    # Safely pull out fields
    date_str    = query_details.get("date", None)       # "YYYY-MM-DD"
    title       = query_details.get("title", None)
    start_iso   = query_details.get("start", None)      # "2025-06-02T17:00:00+02:00"
    end_iso     = query_details.get("end", None)
    cal_id      = query_details.get("calendarId", "primary")

    try:
        tz = pytz.timezone(user_tz)
        timeMin = None
        timeMax = None

        # 1) If full ISO start is provided, convert from that zone to UTC
        if start_iso:
            # This will parse the offset inside start_iso, e.g. "+02:00", then convert to UTC
            start_dt_utc = datetime.datetime.fromisoformat(start_iso).astimezone(datetime.timezone.utc)
            timeMin = start_dt_utc.isoformat()

            if end_iso:
                end_dt_utc = datetime.datetime.fromisoformat(end_iso).astimezone(datetime.timezone.utc)
                timeMax = end_dt_utc.isoformat()
            elif date_str:
                # If they gave a date and a start, interpret date in user_tz, then set timeMax to end of that local day
                date_local = datetime.datetime.fromisoformat(date_str).date()
                # midnight at user’s timezone
                start_of_day_local = tz.localize(datetime.datetime.combine(date_local, datetime.time.min))
                end_of_day_local   = tz.localize(datetime.datetime.combine(date_local, datetime.time.max))
                timeMax = end_of_day_local.astimezone(datetime.timezone.utc).isoformat()
            else:
                # If no end but start given, set timeMax to end of that same local date
                local_date = start_dt_utc.astimezone(tz).date()
                end_of_day_local = tz.localize(datetime.datetime.combine(local_date, datetime.time.max))
                timeMax = end_of_day_local.astimezone(datetime.timezone.utc).isoformat()

        # 2) If only date (no start) is provided, interpret midnight→23:59:59 in user_tz
        elif date_str:
            date_local = datetime.datetime.fromisoformat(date_str).date()
            start_of_day_local = tz.localize(datetime.datetime.combine(date_local, datetime.time.min))
            end_of_day_local   = tz.localize(datetime.datetime.combine(date_local, datetime.time.max))
            timeMin = start_of_day_local.astimezone(datetime.timezone.utc).isoformat()
            timeMax = end_of_day_local.astimezone(datetime.timezone.utc).isoformat()

        # 3) If neither start nor date is provided, default to “today” in user_tz
        else:
            now_local = datetime.datetime.now(tz)
            today_local = now_local.date()
            start_of_day_local = tz.localize(datetime.datetime.combine(today_local, datetime.time.min))
            end_of_day_local   = tz.localize(datetime.datetime.combine(today_local, datetime.time.max))
            timeMin = start_of_day_local.astimezone(datetime.timezone.utc).isoformat()
            timeMax = end_of_day_local.astimezone(datetime.timezone.utc).isoformat()

        # Build the query parameters for Google Calendar (all times must be in UTC for the API)
        params = {
            "calendarId": cal_id,
            "timeMin": timeMin,
            "timeMax": timeMax,
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 10,
        }

        if title:
            params["q"] = title

        events_result = service.events().list(**params).execute()
        events = events_result.get("items", [])

        if not events:
            return {
                "success": True,
                "message": "No events found for the specified criteria.",
                "events": []
            }

        formatted_events = []
        for ev in events:
            formatted_events.append({
                "summary": ev.get("summary", "No title"),
                "description": ev.get("description", "No description"),
                # These are returned in the event’s own timezone, so just relay them as-is
                "start": ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", "No start time")),
                "end":   ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date", "No end time")),
                "link":  ev.get("htmlLink", "No link available")
            })

        return {
            "success": True,
            "message": f"Found {len(formatted_events)} events.",
            "events": formatted_events
        }

    except HttpError as error:
        print(f"An error occurred: {error}")
        return {
            "success": False,
            "message": "Failed to retrieve events",
            "error": str(error)
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "success": False,
            "message": "Failed to retrieve events",
            "error": str(e)
        }
   
def main():
    calendarAuth()