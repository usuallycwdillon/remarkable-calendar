import requests
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import logging
import config

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        """Authenticate with Google Calendar API with proper token refresh handling."""
        if os.path.exists(config.GOOGLE_TOKEN_FILE):
            try:
                self.creds = Credentials.from_authorized_user_file(config.GOOGLE_TOKEN_FILE, SCOPES)
                logger.info("Loaded existing credentials from token file")
            except Exception as e:
                logger.warning(f"Failed to load credentials: {e}")
                self.creds = None
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    logger.info("Access token expired, refreshing...")
                    self.creds.refresh(Request())
                    logger.info("Successfully refreshed access token")
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    logger.info("Re-authenticating from scratch...")
                    self.creds = self._run_oauth_flow()
            else:
                logger.info("No valid credentials found, starting OAuth flow...")
                self.creds = self._run_oauth_flow()
            
            self._save_credentials()
    
    def _run_oauth_flow(self):
        """Run the OAuth flow to get new credentials."""
        if not os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
            raise FileNotFoundError(
                f"Credentials file '{config.GOOGLE_CREDENTIALS_FILE}' not found. "
                "Please download it from Google Cloud Console."
            )
        
        flow = InstalledAppFlow.from_client_secrets_file(
            config.GOOGLE_CREDENTIALS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)
        logger.info("Successfully completed OAuth flow")
        return creds
    
    def _save_credentials(self):
        """Save credentials to token file."""
        try:
            with open(config.GOOGLE_TOKEN_FILE, 'w') as token:
                token.write(self.creds.to_json())
            logger.info(f"Saved credentials to {config.GOOGLE_TOKEN_FILE}")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    def get_events(self, start_date, end_date, calendar_id='primary'):
        """Fetch events between start_date and end_date."""
        start_time = start_date.isoformat() + 'T00:00:00Z'
        end_time = end_date.isoformat() + 'T23:59:59Z'
        
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        
        except HttpError as error:
            if error.resp.status == 401:
                logger.error("Authentication failed. Token may be revoked or expired.")
                logger.info("Attempting to re-authenticate...")
                self._revoke_and_reauth()
                return self.get_events(start_date, end_date, calendar_id)
            else:
                logger.error(f"An error occurred: {error}")
                raise
    
    def _revoke_and_reauth(self):
        """Revoke current credentials and re-authenticate."""
        if os.path.exists(config.GOOGLE_TOKEN_FILE):
            os.remove(config.GOOGLE_TOKEN_FILE)
        self._authenticate()
        self.service = build('calendar', 'v3', credentials=self.creds)
    
    def get_events_for_day(self, date_obj):
        """Get events for a specific day."""
        return self.get_events(date_obj, date_obj)


def test_apis():
    """Test function to explore API data without rate limit abuse."""
    print("Testing Todoist API...")
    todoist = TodoistClient(config.TODOIST_API_TOKEN)
    
    today = datetime.now().date()
    tasks = todoist.get_task_by_date(today)
    print(f"\nTasks for {today}:")
    for task in tasks[:3]:
        print(f"  - {task.get('content')} (Due: {task.get('due', {}).get('date')})")
    
    print("\n" + "="*50)
    print("Testing Google Calendar API...")
    gcal = GoogleCalendarClient()
    
    events = gcal.get_events_for_day(today)
    print(f"\nEvents for {today}:")
    for event in events[:3]:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"  - {event.get('summary')} at {start}")


if __name__ == "__main__":
    test_apis()