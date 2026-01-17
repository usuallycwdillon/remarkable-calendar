from datetime import datetime, timedelta
from api_client import TodoistClient, GoogleCalendarClient
import config
import json

def explore_todoist_data():
    """Explore Todoist task structure."""
    print("="*60)
    print("TODOIST DATA STRUCTURE")
    print("="*60)
    
    todoist = TodoistClient(config.TODOIST_API_TOKEN)
    
    # Get tasks for next 7 days
    today = datetime.now().date()
    for i in range(7):
        date = today + timedelta(days=i)
        tasks = todoist.get_task_by_date(date)
        
        if tasks:
            print(f"\n{date.strftime('%A, %B %d, %Y')}:")
            for task in tasks:
                print(f"\n  Task: {task.get('content')}")
                print(f"    ID: {task.get('id')}")
                print(f"    Due: {task.get('due')}")
                print(f"    Priority: {task.get('priority')}")
                print(f"    Labels: {task.get('labels')}")
                print(f"    Project ID: {task.get('project_id')}")
                if i == 0:  # Only show full JSON for first task
                    print(f"\n    Full JSON: {json.dumps(task, indent=2)}")
                    break
            if i == 0:
                break

def explore_calendar_data():
    """Explore Google Calendar event structure."""
    print("\n" + "="*60)
    print("GOOGLE CALENDAR DATA STRUCTURE")
    print("="*60)
    
    gcal = GoogleCalendarClient()
    
    # Get events for next 7 days
    today = datetime.now().date()
    start = today
    end = today + timedelta(days=7)
    
    events = gcal.get_events(start, end)
    
    if events:
        print(f"\nEvents from {start} to {end}:")
        for i, event in enumerate(events[:5]):  # Show first 5
            print(f"\n  Event: {event.get('summary')}")
            print(f"    Start: {event.get('start')}")
            print(f"    End: {event.get('end')}")
            print(f"    Description: {event.get('description', 'N/A')}")
            print(f"    Location: {event.get('location', 'N/A')}")
            
            if i == 0:  # Show full JSON for first event
                print(f"\n    Full JSON: {json.dumps(event, indent=2)}")

if __name__ == "__main__":
    explore_todoist_data()
    explore_calendar_data()

    