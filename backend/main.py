import logging
from typing import Dict, Any, Tuple
import os
import datetime
import pytz
import socket
from openai import OpenAI
from dotenv import load_dotenv
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _calendar_auth(token_info: dict) -> Credentials:
    if not token_info or 'access_token' not in token_info:
        raise ValueError("Missing tokens; user not authenticated")

    creds = Credentials(
        token=token_info['access_token'],
        refresh_token=token_info.get('refresh_token'),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        scopes=SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # update the token_info dict in place so caller can re-save it
        token_info['access_token'] = creds.token
        token_info['expires_at']   = creds.expiry.timestamp() if creds.expiry else None

    return creds

def _build_service(token_info: dict):
    creds = _calendar_auth(token_info)
    return build('calendar', 'v3', credentials=creds)

def create_event(token_info: dict, event_body: dict) -> dict:
    service = _build_service(token_info)
    return service.events().insert(
        calendarId='primary',
        body=event_body
    ).execute()

def list_events(token_info: dict, **kwargs) -> dict:
    service = _build_service(token_info)
    return service.events().list(
        calendarId='primary',
        **kwargs
    ).execute()


def calendarAuth(session):
    """Authenticate using tokens from Flask session"""
    if not session or 'tokens' not in session:
        raise Exception("Authentication required. Please log in through the web interface.")

    tokens = session['tokens']
    if not tokens or 'access_token' not in tokens:
        raise Exception("Authentication required. Please log in through the web interface.")

    creds = Credentials(
        token=tokens['access_token'],
        refresh_token=tokens.get('refresh_token'),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        scopes=SCOPES
    )

    # Refresh if needed
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        session['tokens']['access_token'] = creds.token
        session['tokens']['expires_at'] = creds.expiry.timestamp() if creds.expiry else None

    return creds


def createEvent(token_info: Dict[str, Any], summary: str, description: str, start_iso: str, end_iso: str = None, calendar_id: str = "primary", user_tz: str = "UTC") -> Tuple[Any, Dict[str, Any]]:
    """
    Create a Google Calendar event using exactly the user's IANA timezone (user_tz).
    Returns (created_event_dict or False, updated_token_info).
    """
    creds = _calendar_auth(token_info)
    service = build("calendar", "v3", credentials=creds)

    if not summary or not start_iso:
        logging.error("Missing required parameters for createEvent")
        return False, token_info

    try:
        start_dt = datetime.datetime.fromisoformat(start_iso)
        if not end_iso:
            end_dt = start_dt + datetime.timedelta(hours=1)
            end_iso = end_dt.isoformat()
        else:
            end_dt = datetime.datetime.fromisoformat(end_iso)
        if end_dt <= start_dt:
            logging.error("End time must be after start time")
            return False, token_info
    except ValueError as e:
        logging.error(f"Invalid datetime format: {e}")
        return False, token_info

    event_body = {
        "summary": summary,
        "description": description or "",
        "start": {"dateTime": start_iso, "timeZone": user_tz},
        "end": {"dateTime": end_iso, "timeZone": user_tz},
    }

    logging.debug(f"Event object being sent to Google: {event_body}")

    original_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(30)
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            created = service.events().insert(calendarId=calendar_id, body=event_body).execute()
            logging.info(f"Event created: {created.get('htmlLink')}")
            socket.setdefaulttimeout(original_timeout)
            return created, token_info
        except socket.timeout:
            retry_count += 1
            logging.warning(f"Request timed out. Retry attempt {retry_count} of {max_retries}")
            if retry_count >= max_retries:
                logging.error("Max retries reached. Could not create event.")
                socket.setdefaulttimeout(original_timeout)
                return False, token_info
        except HttpError as error:
            logging.error(f"HTTP error occurred: {error}")
            socket.setdefaulttimeout(original_timeout)
            return False, token_info
        except Exception as e:
            logging.error(f"Unexpected error in createEvent: {e}")
            socket.setdefaulttimeout(original_timeout)
            return False, token_info

    socket.setdefaulttimeout(original_timeout)
    return False, token_info


def getEvents(token_info, calendarId='primary', day=None):
    """Get calendar events"""
    if day is None:
        day = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    creds = _calendar_auth(token_info)
    service = build("calendar", "v3", credentials=creds)
    
    events_result = service.events().list(
        calendarId=calendarId,
        timeMin=day,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    
    return events_result.get('items', [])

def validateCalendarId(token_info: Dict[str, Any], calId: str) -> Tuple[str, Dict[str, Any]]:
    """
    Validate if a calendar ID exists for the user.
    Returns (calId, updated_token_info) or raises ValueError.
    """
    creds = _calendar_auth(token_info)
    service = build("calendar", "v3", credentials=creds)

    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list.get('items', []):
        if calendar.get('id') == calId:
            return calId, token_info

    raise ValueError(f'Calendar ID {calId} not found')


def deleteEvent(token_info: Dict[str, Any], eventId: str, calendarId: str = 'primary') -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Delete a calendar event.
    Returns (response_dict, updated_token_info).
    """
    try:
        creds = _calendar_auth(token_info)
        service = build('calendar', 'v3', credentials=creds)
        service.events().delete(calendarId=calendarId, eventId=eventId).execute()
        return ({
            "success": True,
            "message": "Event deleted successfully"
        }, token_info)
    except HttpError as e:
        if e.resp.status == 404:
            return ({
                "success": False,
                "message": "Event not found",
                "error": "Event not found"
            }, token_info)
        return ({
            "success": False,
            "message": "Failed to delete event",
            "error": str(e)
        }, token_info)
    except Exception as e:
        logging.error(f"Error in deleteEvent: {e}")
        return ({
            "success": False,
            "message": "Error deleting event",
            "error": str(e)
        }, token_info)


def promptToEvent(prompt, user_tz):
    """Convert natural language prompt to event parameters using OpenAI"""
    try:
        client = OpenAI(
            api_key=os.getenv('openai_key_v3'),
            base_url="https://api.openai.com/v1"
        )
        
        # Get current date and timezone for reference
        zone = pytz.timezone(user_tz)
        now_local = datetime.datetime.now(zone)
        today_str = now_local.strftime("%Y-%m-%d")
        time_str = now_local.strftime("%H:%M:%S")
        tz_offset = now_local.strftime("%z")
        # Insert the colon so GPT sees "-07:00"
        tz_offset = f"{tz_offset[:3]}:{tz_offset[3:]}"
        
        print(f"Local timezone offset: {tz_offset}")
        
        modified_prompt = f"""
        You are a calendar assistant. Given the user's input, determine if they want to create a new event or view existing events.
        
        Today's date is {today_str} in the timezone {time_str} in the time zone {tz_offset} which is the users time zone as {user_tz}
        When interpreting "tomorrow at 5pm", interpret "5pm" in exactly {user_tz} (including DST).  
        If they want to create an event, return raw JSON only:
        
        When interpreting dates and times:
        - For relative dates like "tomorrow", "next week", etc., calculate the actual date based on today's date.
        - Always use the current year ({now_local.year}) for dates unless a specific year is mentioned.
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
            content = content.replace("```json", "").replace("```", "").strip()
        
        # Add error handling for JSON parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response after stripping: {content}")
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


def formatEvent(token_info: Dict[str, Any], event: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Create a Google Calendar event using token_info and event data.
    Returns (response_dict, updated_token_info).
    """
    # Validate required fields
    for key in ('summary', 'description', 'start', 'end'):
        if key not in event:
            return ({
                "success": False,
                "message": f"Missing required key: {key}",
                "error": f"Event data is missing '{key}'"
            }, token_info)

    # Build calendar service
    creds = _calendar_auth(token_info)
    service = build('calendar', 'v3', credentials=creds)

    body = {
        'summary':     event['summary'],
        'description': event['description'],
        'start':       {'dateTime': event['start'], 'timeZone': event.get('timeZone', 'UTC')},
        'end':         {'dateTime': event['end'],   'timeZone': event.get('timeZone', 'UTC')}
    }

    try:
        created = service.events().insert(calendarId=event.get('calendarId','primary'), body=body).execute()
        response = {
            "success": True,
            "message": "Event created successfully",
            "event": {
                "summary": event['summary'],
                "description": event['description'],
                "start": event['start'],
                "end": event['end'],
                "calendarId": event.get('calendarId','primary'),
                "link": created.get('htmlLink', '')
            }
        }
        return response, token_info

    except HttpError as e:
        err = e.error_details if hasattr(e, 'error_details') else str(e)
        return ({
            "success": False,
            "message": "Failed to create event",
            "error": err
        }, token_info)
    except Exception as e:
        return ({
            "success": False,
            "message": "Error formatting event",
            "error": str(e)
        }, token_info)



def findEvent(token_info: Dict[str, Any], query_details: dict, user_tz: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Finds events based on provided criteria in the user's timezone.
    - query_details may include:
        - date:       "YYYY-MM-DD"
        - title:      string
        - start:      full ISO-8601 string with offset (e.g. "2025-06-02T17:00:00+02:00")
        - end:        full ISO-8601 string with offset
        - calendarId: string (defaults to "primary")
    - user_tz is the user's IANA timezone (e.g. "America/Los_Angeles").
    Returns (result_dict, updated_token_info)
    """
    try:
        creds = _calendar_auth(token_info)
        service = build("calendar", "v3", credentials=creds)

        # Safely pull out fields
        date_str = query_details.get("date", None)
        title = query_details.get("title", None)
        start_iso = query_details.get("start", None)
        end_iso = query_details.get("end", None)
        cal_id = query_details.get("calendarId", "primary")

        tz = pytz.timezone(user_tz)
        timeMin = None
        timeMax = None

        # 1) If full ISO start is provided, convert from that zone to UTC
        if start_iso:
            start_dt_utc = datetime.datetime.fromisoformat(start_iso).astimezone(datetime.timezone.utc)
            timeMin = start_dt_utc.isoformat()

            if end_iso:
                end_dt_utc = datetime.datetime.fromisoformat(end_iso).astimezone(datetime.timezone.utc)
                timeMax = end_dt_utc.isoformat()
            elif date_str:
                date_local = datetime.datetime.fromisoformat(date_str).date()
                start_of_day_local = tz.localize(datetime.datetime.combine(date_local, datetime.time.min))
                end_of_day_local = tz.localize(datetime.datetime.combine(date_local, datetime.time.max))
                timeMax = end_of_day_local.astimezone(datetime.timezone.utc).isoformat()
            else:
                local_date = start_dt_utc.astimezone(tz).date()
                end_of_day_local = tz.localize(datetime.datetime.combine(local_date, datetime.time.max))
                timeMax = end_of_day_local.astimezone(datetime.timezone.utc).isoformat()

        # 2) If only date (no start) is provided, interpret midnight→23:59:59 in user_tz
        elif date_str:
            date_local = datetime.datetime.fromisoformat(date_str).date()
            start_of_day_local = tz.localize(datetime.datetime.combine(date_local, datetime.time.min))
            end_of_day_local = tz.localize(datetime.datetime.combine(date_local, datetime.time.max))
            timeMin = start_of_day_local.astimezone(datetime.timezone.utc).isoformat()
            timeMax = end_of_day_local.astimezone(datetime.timezone.utc).isoformat()

        # 3) If neither start nor date is provided, default to "today" in user_tz
        else:
            now_local = datetime.datetime.now(tz)
            today_local = now_local.date()
            start_of_day_local = tz.localize(datetime.datetime.combine(today_local, datetime.time.min))
            end_of_day_local = tz.localize(datetime.datetime.combine(today_local, datetime.time.max))
            timeMin = start_of_day_local.astimezone(datetime.timezone.utc).isoformat()
            timeMax = end_of_day_local.astimezone(datetime.timezone.utc).isoformat()

        # Build the query parameters for Google Calendar
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
            return ({
                "success": True,
                "message": "No events found for the specified criteria.",
                "events": []
            }, token_info)

        formatted_events = []
        for ev in events:
            formatted_events.append({
                "id": ev.get("id"),  # Include event ID for deletion
                "summary": ev.get("summary", "No title"),
                "description": ev.get("description", "No description"),
                "start": ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", "No start time")),
                "end": ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date", "No end time")),
                "link": ev.get("htmlLink", "No link available")
            })

        return ({
            "success": True,
            "message": f"Found {len(formatted_events)} events.",
            "events": formatted_events
        }, token_info)

    except HttpError as error:
        print(f"An error occurred: {error}")
        return ({
            "success": False,
            "message": "Failed to retrieve events",
            "error": str(error)
        }, token_info)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ({
            "success": False,
            "message": "Failed to retrieve events",
            "error": str(e)
        }, token_info)
    