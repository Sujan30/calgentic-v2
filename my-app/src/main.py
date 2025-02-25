import os
import flask
import os.path
import datetime

from openai import OpenAI
from dotenv import load_dotenv

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
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception as e:
            print(f'Error loading credentials: {e}. Deleting token.json and re-authenticating.')
            os.remove("token.json")  # Delete the invalid token file
            creds = None  # Reset creds to None to trigger re-authentication

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
def createEvent(summary, description, start, end, calendarId='primary'):
   try:
      global service
      global creds
      service = build('calendar', 'v3', credentials=creds)
      event = {
         'summary': summary,
         'description': description,
         'start': {
            'dateTime': start,
            'timeZone': 'UTC',
         },
         'end': {
            'dateTime': end,
            'timeZone': 'UTC',
         }
      }
      event = service.events().insert(calendarId=calendarId, body=event).execute()
      print(f'Event created: {event.get("htmlLink")}')
      return event
   except HttpError as error:
      print(f'An error occurred: {error}')
      raise error

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

def main():
    calendarAuth()
    createEvent(summary='Test Event', description='This is a test event', start='2024-01-01T12:00:00', end='2024-01-01T13:00:00')

def askPrompt():
    input_prompt = input("What's coming up next?': ")
    return input_prompt




def promptToEvent(prompt):
    client = OpenAI()
    modified_prompt = f"""
    You are a calendar assistant. Given the user's input, determine if they want to create a new event or view existing events.
    
    - If they want to create an event, return the following JSON structure:
      ```json
      {{
        "action_type": "create",
        "eventParams": [
          {{
            "summary": "Event title",
            "description": "Event details",
            "start": "YYYY-MM-DDTHH:MM:SS-07:00",
            "end": "YYYY-MM-DDTHH:MM:SS-07:00",
            "calendarId": "primary"
          }}
        ]
        "eventCompletion" : "A little summary about the event, that acts as a confirmation
      }}
      ```
    
    - If they want to view an event, return:
        - At least one of the following fields must be included: `date`, `title`, `start`, `end`, `calendarId`.
      ```json
      {{
        "action_type": "view",
        "query_details": [
            "date" : "date of the event they want to view",
            "title" : "title of the event they want to view",
            "start": "YYYY-MM-DDTHH:MM:SS-07:00"
            "end": "YYYY-MM-DDTHH:MM:SS-07:00",
            "calendarId": "primary"
        ]
      }}
      ```
    
    Ensure the response is **valid JSON format**.
    
    User input: {prompt}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": modified_prompt}]
    )
    
    return response.choices[0].message.content  # Returns JSON string

def formatEvent(event):
    try:
        
        summary = event['summary']
        description = event['description']
        start = event['start']
        end = event['end']
        calendarId = event['calendarId']
        if(createEvent(summary, description, start, end, calendarId)):
            return True
        else:
            print("error formatting the event")
            return False
    except:
        print("error, prompt format is wrong")
        return False

def findEvent(query_details):
    """Finds an event based on provided criteria."""
    global service
    
    date = query_details['date']
    title = query_details['title']
    start = query_details['start']
    end = query_details['end']
    calendarId = query_details['calendarId']

    try:
        timeMin = None
        timeMax = None

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

        if timeMin:
            events_result = service.events().list(calendarId=calendarId,
                                                  timeMin=timeMin,
                                                  timeMax=timeMax,
                                                  singleEvents=True,
                                                  orderBy='startTime').execute()
            events = events_result.get('items', [])

            for event in events:
                event_start = event['start'].get('dateTime', event['start'].get('date'))
                if 'dateTime' in event['start']:
                    event_start_date = datetime.datetime.fromisoformat(event_start[:-1]).astimezone(datetime.timezone.utc).date()
                else:
                    event_start_date = datetime.datetime.strptime(event_start, '%Y-%m-%d').date()

                if date and event_start_date != datetime.datetime.fromisoformat(date).astimezone(datetime.timezone.utc).date():
                    continue

                if title and title.lower() not in event['summary'].lower():
                    continue

                return event

        return None

    except ValueError as e:
        print(f"Invalid date format: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None      
            
            



        

    except:
        print("error")
   
main()