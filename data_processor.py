from datetime import datetime, timedelta
from dateutil import parser
from api_client import TodoistClient, GoogleCalendarClient
import config
import re

class PlannerDataProcessor:
    def __init__(self):
        self.todoist = TodoistClient(config.TODOIST_API_TOKEN)
        self.gcal = GoogleCalendarClient()
    
    def format_task_labels(self, labels):
        """Format labels with time tags first."""
        time_tags = []
        other_tags = []
        
        for label in labels:
            if 'min' in label or 'hr' in label:
                time_tags.append(f"@{label}")
            else:
                other_tags.append(f"@{label}")
        
        return ' '.join(time_tags + other_tags)
    
    def normalize_text(self, text):
        """Normalize text for comparison."""
        return re.sub(r'[^\w\s]', '', text.lower()).strip()
    
    def is_task_on_calendar(self, task, calendar_events):
        """Check if a Todoist task is already on the calendar."""
        task_content = self.normalize_text(task['content'])
        
        for event in calendar_events:
            event_summary = self.normalize_text(event.get('summary', ''))
            if task_content == event_summary:
                return True
        
        return False
    
    def parse_event_time(self, event_time):
        """Parse event start/end time."""
        if 'dateTime' in event_time:
            return parser.parse(event_time['dateTime'])
        else:
            return parser.parse(event_time['date'])
    
    def get_daily_tasks(self, date_obj):
        """Get tasks for a specific day, excluding calendar duplicates."""
        tasks = self.todoist.get_task_by_date(date_obj)
        calendar_events = self.gcal.get_events_for_day(date_obj)
        
        formatted_tasks = []
        for task in tasks:
            if not self.is_task_on_calendar(task, calendar_events):
                labels_str = self.format_task_labels(task.get('labels', []))
                task_text = task['content']
                if labels_str:
                    task_text = f"{task_text} {labels_str}"
                
                formatted_tasks.append({
                    'text': task_text,
                    'priority': task.get('priority', 1)
                })
        
        return formatted_tasks
    
    def get_daily_events(self, date_obj):
        """Get calendar events for a specific day with start/end times and labels."""
        events = self.gcal.get_events_for_day(date_obj)
        
        formatted_events = []
        for event in events:
            start_time = self.parse_event_time(event['start'])
            end_time = self.parse_event_time(event['end'])
            
            is_all_day = 'date' in event['start']
            
            formatted_events.append({
                'label': event.get('summary', 'Untitled'),
                'start': start_time,
                'end': end_time,
                'is_all_day': is_all_day
            })
        
        return formatted_events
    
    def get_weekly_events(self, week_start_date):
        """Get calendar events for a week."""
        week_end = week_start_date + timedelta(days=6)
        events = self.gcal.get_events(week_start_date, week_end)
        
        formatted_events = []
        for event in events:
            start_time = self.parse_event_time(event['start'])
            end_time = self.parse_event_time(event['end'])
            
            formatted_events.append({
                'label': event.get('summary', 'Untitled'),
                'start': start_time,
                'end': end_time,
                'is_all_day': 'date' in event['start']
            })
        
        return formatted_events
    
    def get_yearly_overview_items(self, year):
        """Get tasks and events tagged with @headline for the yearly overview, plus holidays."""
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        
        events = self.gcal.get_events(start_date, end_date)
        try:
            holidays = self.gcal.get_events(start_date, end_date, calendar_id='en.usa#holiday@group.v.calendar.google.com')
        except:
            holidays = []
        
        all_tasks = self.todoist.get_tasks()
        
        items = []
        
        for event in events:
            description = event.get('description', '')
            if '@headline' in description.lower():
                event_date = self.parse_event_time(event['start']).date()
                if start_date <= event_date <= end_date:
                    items.append({
                        'date': event_date,
                        'text': event.get('summary', 'Untitled'),
                        'type': 'event'
                    })
        
        for holiday in holidays:
            holiday_date = self.parse_event_time(holiday['start']).date()
            items.append({
                'date': holiday_date,
                'text': holiday.get('summary', 'Holiday'),
                'type': 'holiday'
            })
        
        for task in all_tasks:
            if 'headline' in [label.lower() for label in task.get('labels', [])]:
                if task.get('due') and task['due'].get('date'):
                    task_date = parser.parse(task['due']['date']).date()
                    if start_date <= task_date <= end_date:
                        items.append({
                            'date': task_date,
                            'text': task['content'],
                            'type': 'task'
                        })
        
        items.sort(key=lambda x: x['date'])
        return items
    
    def get_headline_events_for_day(self, date_obj):
        """Get headline events for a specific day."""
        events = self.gcal.get_events_for_day(date_obj)
        
        headline_events = []
        for event in events:
            description = event.get('description', '')
            if '@headline' in description.lower():
                headline_events.append({
                    'text': event.get('summary', 'Untitled'),
                    'type': 'event'
                })
        
        return headline_events


def test_processor():
    """Test the data processor."""
    processor = PlannerDataProcessor()
    today = datetime.now().date()
    
    print("="*60)
    print("DAILY TASKS (excluding calendar duplicates):")
    print("="*60)
    tasks = processor.get_daily_tasks(today)
    for task in tasks:
        print(f"  - {task['text']}")
    
    print("\n" + "="*60)
    print("DAILY EVENTS:")
    print("="*60)
    events = processor.get_daily_events(today)
    for event in events:
        if event['is_all_day']:
            print(f"  - {event['label']} (All day)")
        else:
            start_str = event['start'].strftime('%H:%M')
            end_str = event['end'].strftime('%H:%M')
            print(f"  - {event['label']} ({start_str} - {end_str})")
    
    print("\n" + "="*60)
    print("WEEKLY EVENTS:")
    print("="*60)
    week_start = today - timedelta(days=today.weekday())
    weekly_events = processor.get_weekly_events(week_start)
    for event in weekly_events[:5]:
        day = event['start'].strftime('%a')
        if event['is_all_day']:
            print(f"  - {day}: {event['label']} (All day)")
        else:
            time_str = event['start'].strftime('%H:%M')
            print(f"  - {day} {time_str}: {event['label']}")


if __name__ == "__main__":
    test_processor()