import requests
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import config

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class TodoistClient:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.todoist.com/rest/v2"
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def get_tasks(self, filter_string=None):
        """Fetch tasks from Todoist."""
        url = f"{self.base_url}/tasks"
        params = {}
        if filter_string:
            params['filter'] = filter_string
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_task_by_date(self, date_obj):
        """Get tasks due on a specific date."""
        date_str = date_obj.strftime('%Y-%m-%d')
        return self.get_tasks(filter_string=f"due: {date_str}")


class GoogleCalendarClient:
    def __init__(self):
        self.creds = None
        self._authenticate()
        self.service = build('calendar', 'v3', credentials=self.creds)
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        if os.path.exists(config.GOOGLE_TOKEN_FILE):
            self.creds = Credentials.from_authorized_user_file(config.GOOGLE_TOKEN_FILE, SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.GOOGLE_CREDENTIALS_FILE, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(config.GOOGLE_TOKEN_FILE, 'w') as token:
                token.write(self.creds.to_json())
    
    def get_events(self, start_date, end_date, calendar_id='primary'):
        """Fetch events between start_date and end_date."""
        start_time = start_date.isoformat() + 'T00:00:00Z'
        end_time = end_date.isoformat() + 'T23:59:59Z'
        
        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    
    def get_events_for_day(self, date_obj):
        """Get events for a specific day."""
        return self.get_events(date_obj, date_obj)


def test_apis():
    """Test function to explore API data without rate limit abuse."""
    print("Testing Todoist API...")
    todoist = TodoistClient(config.TODOIST_API_TOKEN)
    
    # Get today's tasks
    today = datetime.now().date()
    tasks = todoist.get_task_by_date(today)
    print(f"\nTasks for {today}:")
    for task in tasks[:3]:  # Only show first 3
        print(f"  - {task.get('content')} (Due: {task.get('due', {}).get('date')})")
    
    print("\n" + "="*50)
    print("Testing Google Calendar API...")
    gcal = GoogleCalendarClient()
    
    # Get today's events
    events = gcal.get_events_for_day(today)
    print(f"\nEvents for {today}:")
    for event in events[:3]:  # Only show first 3
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"  - {event.get('summary')} at {start}")


if __name__ == "__main__":
    test_apis()