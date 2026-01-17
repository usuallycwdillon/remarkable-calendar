from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import calendar
from datetime import date, timedelta
import os

from pages import (
    YearlyOverviewPage, MonthlyOverviewPage, WeeklyPage,
    DailySchedulePage, DailyTasksPage, NotesPage
)
from data_processor import PlannerDataProcessor

def generate_monthly_planner(year, month, output_dir, data_processor):
    """Generate a single monthly planner PDF."""
    month_name = calendar.month_name[month]
    filename = f"{year}_{month:02d}_{month_name}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    
    pages = []
    
    yearly_items = data_processor.get_yearly_overview_items(year)
    
    for i in range(4):
        start_month = i * 3 + 1
        pages.append(YearlyOverviewPage(year, i+1, start_month, current_month=month, yearly_items=yearly_items))
    
    pages.append(MonthlyOverviewPage(year, month))
    
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    current_date = first_day
    while current_date.weekday() != 0:
        current_date -= timedelta(days=1)
    
    week_starts = []
    while current_date <= last_day:
        week_starts.append(current_date)
        current_date += timedelta(days=7)
    
    for week_start in week_starts:
        weekly_events = data_processor.get_weekly_events(week_start)
        pages.append(WeeklyPage(week_start, events=weekly_events))
    
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        day_date = date(year, month, day)
        
        daily_events = data_processor.get_daily_events(day_date)
        daily_tasks = data_processor.get_daily_tasks(day_date)
        headline_events = data_processor.get_headline_events_for_day(day_date)
        
        pages.append(DailySchedulePage(day_date, events=daily_events))
        pages.append(DailyTasksPage(day_date, tasks=daily_tasks, headline_events=headline_events))
    
    for i in range(10):
        pages.append(NotesPage(i+1))
    
    for i, page in enumerate(pages):
        page.page_number = i + 1
    
    bookmark_to_page = {page.bookmark_name: page.page_number for page in pages}
    
    for page in pages:
        page.render(c)
        
        for link in page.links:
            dest_bookmark = link['dest']
            if dest_bookmark in bookmark_to_page:
                dest_page = bookmark_to_page[dest_bookmark]
                x1, y1, x2, y2 = link['rect']
                c.linkAbsolute('', dest_bookmark, (x1, y1, x2, y2))
        
        c.showPage()
    
    c.save()
    print(f"Generated: {filepath}")

def generate_full_year_planner(year):
    """Generate planner PDFs for all 12 months of the year."""
    output_dir = f"planner_{year}"
    os.makedirs(output_dir, exist_ok=True)
    
    data_processor = PlannerDataProcessor()
    
    for month in range(1, 13):
        generate_monthly_planner(year, month, output_dir, data_processor)

if __name__ == "__main__":
    generate_full_year_planner(2026)