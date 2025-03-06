import os
import flask
import os.path
import datetime

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
    global creds
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    # Use absolute paths to the credentials and token files
    credentials_path = "/Users/sujannandikolsunilkumar/ai calendar/credentials.json"
    token_path = "/Users/sujannandikolsunilkumar/ai calendar/token.json"
    
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f'Error loading credentials: {e}. Deleting token.json and re-authenticating.')
            os.remove(token_path)  # Delete the invalid token file
            creds = None  # Reset creds to None to trigger re-authentication

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())


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


    
def createEvent(summary, description, start, end, calendarId='primary'):
   try:
      global service
      global creds
      
      # Call calendarAuth() to ensure credentials are initialized
      if creds is None:
          calendarAuth()
      
      # Initialize service if not already done
      if service is None and creds is not None:
          service = build('calendar', 'v3', credentials=creds)
      
      # Validate inputs
      if not summary or not description or not start or not end:
          print("Missing required parameters for createEvent")
          return False
      
      # Parse the datetime strings to ensure they're valid
      try:
          # Get the local timezone
          local_tz = datetime.datetime.now().astimezone().tzinfo
          
          # Parse the datetime strings
          start_dt = datetime.datetime.fromisoformat(start)
          end_dt = datetime.datetime.fromisoformat(end)
          
          # Ensure end time is after start time
          if end_dt <= start_dt:
              print("Error: End time must be after start time")
              return False
              
      except ValueError as e:
          print(f"Invalid datetime format: {e}")
          return False
      
      # Create the event object
      event = {
         'summary': summary,
         'description': description,
         'start': {
            'dateTime': start,
            'timeZone': str(local_tz),  # Use the local timezone
         },
         'end': {
            'dateTime': end,
            'timeZone': str(local_tz),  # Use the local timezone
         }
      }
      
      # Print the event object for debugging
      print(f"Event object: {event}")
      
      # Add retry logic with timeout handling
      import socket
      from googleapiclient.errors import HttpError
      
      # Set a timeout for socket operations
      original_timeout = socket.getdefaulttimeout()
      socket.setdefaulttimeout(30)  # 30 seconds timeout
      
      max_retries = 3
      retry_count = 0
      
      while retry_count < max_retries:
          try:
              # Insert the event
              event = service.events().insert(calendarId=calendarId, body=event).execute()
              print(f'Event created: {event.get("htmlLink")}')
              # Reset socket timeout to original value
              socket.setdefaulttimeout(original_timeout)
              return event
          except socket.timeout:
              retry_count += 1
              print(f"Request timed out. Retry attempt {retry_count} of {max_retries}")
              if retry_count >= max_retries:
                  print("Max retries reached. Could not create event due to timeout.")
                  # Reset socket timeout to original value
                  socket.setdefaulttimeout(original_timeout)
                  return False
          except HttpError as error:
              print(f'HTTP error occurred: {error}')
              # Reset socket timeout to original value
              socket.setdefaulttimeout(original_timeout)
              return False
          except Exception as e:
              print(f'Unexpected error in createEvent: {str(e)}')
              # Reset socket timeout to original value
              socket.setdefaulttimeout(original_timeout)
              return False
   except Exception as e:
      print(f'Unexpected error in createEvent: {str(e)}')
      import traceback
      traceback.print_exc()
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




def promptToEvent(prompt):
    
    client = OpenAI(api_key=os.getenv('openai_key'))
    
    # Get current date and timezone for reference
    local_tz = datetime.datetime.now().astimezone().tzinfo
    current_date = datetime.datetime.now().astimezone()
    
    # Get the timezone offset as a string (e.g., "-07:00")
    tz_offset = current_date.strftime('%z')
    # Format it with a colon (e.g., "-07:00")
    if len(tz_offset) == 5:
        tz_offset = f"{tz_offset[:3]}:{tz_offset[3:]}"
    
    print(f"Local timezone offset: {tz_offset}")
    
    modified_prompt = f"""
    You are a calendar assistant. Given the user's input, determine if they want to create a new event or view existing events.
    
    Today's date is {current_date.strftime('%Y-%m-%d')} and the current time is {current_date.strftime('%H:%M:%S')} in timezone {tz_offset}.
    
    When interpreting dates and times:
    - For relative dates like "tomorrow", "next week", etc., calculate the actual date based on today's date.
    - Always use the current year ({current_date.year}) for dates unless a specific year is mentioned.
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
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": modified_prompt}]
    )
    
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
                return False
        
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
                return True
            else:
                print("Error in createEvent function")
                return False
        except Exception as e:
            print(f"Error in createEvent: {str(e)}")
            return False
    except Exception as e:
        print(f"Error in formatEvent: {str(e)}")
        import traceback
        traceback.print_exc()  # Print the full stack trace
        return False

def findEvent(query_details):
    """Finds an event based on provided criteria."""
    global service
    global creds
    
    # Initialize service if not already done
    if service is None and creds is not None:
        service = build('calendar', 'v3', credentials=creds)
    
    # Use get() method to safely access dictionary keys with default values
    date = query_details.get('date', None)
    title = query_details.get('title', None)
    start = query_details.get('start', None)
    end = query_details.get('end', None)
    calendarId = query_details.get('calendarId', 'primary')
    
    try:
        timeMin = None
        timeMax = None
        
        # Set up time range based on available parameters
        if start:
            start_datetime = datetime.datetime.fromisoformat(start).astimezone(datetime.timezone.utc)
            timeMin = start_datetime.isoformat()
            
            if end:
                end_datetime = datetime.datetime.fromisoformat(end).astimezone(datetime.timezone.utc)
                timeMax = end_datetime.isoformat()
            elif date:
                date_obj = datetime.datetime.fromisoformat(date).astimezone(datetime.timezone.utc).date()
                timeMax = datetime.datetime.combine(date_obj, datetime.time.max, tzinfo=datetime.timezone.utc).isoformat()
            else:
                date_obj = start_datetime.date()
                timeMax = datetime.datetime.combine(date_obj, datetime.time.max, tzinfo=datetime.timezone.utc).isoformat()
        elif date:
            date_obj = datetime.datetime.fromisoformat(date).astimezone(datetime.timezone.utc).date()
            timeMin = datetime.datetime.combine(date_obj, datetime.time.min, tzinfo=datetime.timezone.utc).isoformat()
            timeMax = datetime.datetime.combine(date_obj, datetime.time.max, tzinfo=datetime.timezone.utc).isoformat()
        else:
            # If no date or time specified, use current date
            today = datetime.datetime.now(datetime.timezone.utc).date()
            timeMin = datetime.datetime.combine(today, datetime.time.min, tzinfo=datetime.timezone.utc).isoformat()
            timeMax = datetime.datetime.combine(today, datetime.time.max, tzinfo=datetime.timezone.utc).isoformat()
        
        # Build the query parameters
        params = {
            'calendarId': calendarId,
            'timeMin': timeMin,
            'timeMax': timeMax,
            'singleEvents': True,
            'orderBy': 'startTime',
            'maxResults': 10
        }
        
        # Add title as a search query if provided
        if title:
            params['q'] = title
        
        # Execute the query
        events_result = service.events().list(**params).execute()
        events = events_result.get('items', [])
        
        if not events:
            return {"message": "No events found."}
        
        # Format the events for response
        formatted_events = []
        for event in events:
            formatted_event = {
                'summary': event.get('summary', 'No title'),
                'description': event.get('description', 'No description'),
                'start': event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'No start time')),
                'end': event.get('end', {}).get('dateTime', event.get('end', {}).get('date', 'No end time')),
                'link': event.get('htmlLink', 'No link available')
            }
            formatted_events.append(formatted_event)
        
        return {"events": formatted_events}
        
    except HttpError as error:
        print(f'An error occurred: {error}')
        return {"error": f"An error occurred: {str(error)}"}
    except Exception as e:
        print(f'Unexpected error: {e}')
        return {"error": f"Unexpected error: {str(e)}"}




        

    except:
        print("error")
   
def main():
    calendarAuth()