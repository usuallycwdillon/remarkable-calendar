from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import calendar
from datetime import date, timedelta

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.5 * inch

COLOR_GRID = HexColor('#E0E0E0')
COLOR_TEXT = HexColor('#000000')
COLOR_LINK = HexColor('#0066CC')
COLOR_EVENT = HexColor('#2C5F8D')
COLOR_WEEKEND = HexColor('#F5F5F5')

FONT_HEADER = 'Courier-Bold'
FONT_BODY = 'Courier'
FONT_SMALL = 'Courier'


class PlannerPage:
    """Base class for all planner pages."""
    def __init__(self, bookmark_name):
        self.bookmark_name = bookmark_name
        self.page_number = None
        self.links = []
    
    def add_link(self, x1, y1, x2, y2, dest):
        """Store link information to be created after page numbers are assigned."""
        self.links.append({
            'rect': (x1, y1, x2, y2),
            'dest': dest
        })
    
    def render(self, c):
        """Render the page content. Must be implemented by subclasses."""
        raise NotImplementedError


class YearlyOverviewPage(PlannerPage):
    """Yearly overview page showing 3 months in matrix format."""
    def __init__(self, year, page_num, start_month, current_month=None, yearly_items=None):
        super().__init__(f'year_{year}_page{page_num}')
        self.year = year
        self.page_num = page_num
        self.start_month = start_month
        self.current_month = current_month
        self.yearly_items = yearly_items or []
    
    def render(self, c):
        c.bookmarkPage(self.bookmark_name)
        
        c.setFont(FONT_HEADER, 16)
        c.drawString(MARGIN, PAGE_HEIGHT - 0.5*inch, f"{self.year} Overview (Page {self.page_num}/4)")
        
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        
        dow_col_width = 0.15*inch
        grid_x = MARGIN + dow_col_width
        grid_y = MARGIN + 0.3*inch
        grid_width = PAGE_WIDTH - 2*MARGIN - dow_col_width
        grid_height = PAGE_HEIGHT - 1*inch - grid_y
        
        num_months = 3
        month_width = grid_width / num_months
        
        day_labels = ['M', 'T', 'W', 'R', 'F', 'S', 'U']
        num_rows = 37
        row_height = grid_height / (num_rows + 1)
        
        c.setFont(FONT_HEADER, 11)
        for i in range(num_months):
            month_idx = self.start_month + i - 1
            if month_idx >= 12:
                break
            
            month_x = grid_x + i * month_width
            c.drawString(month_x + 0.1*inch, grid_y + grid_height + 0.15*inch, 
                        month_names[month_idx])
        
        c.setStrokeColor(COLOR_GRID)
        c.setLineWidth(0.5)
        
        for i in range(num_rows + 2):
            y_pos = grid_y + grid_height - i * row_height
            c.line(MARGIN, y_pos, grid_x + grid_width, y_pos)
        
        c.line(MARGIN + dow_col_width, grid_y, MARGIN + dow_col_width, grid_y + grid_height)
        
        for i in range(num_months + 1):
            x_pos = grid_x + i * month_width
            c.line(x_pos, grid_y, x_pos, grid_y + grid_height)
        
        c.setFont(FONT_SMALL, 10)
        for i in range(num_rows):
            dow_label = day_labels[i % 7]
            label_y = grid_y + grid_height - (i + 0.5) * row_height - 0.05*inch
            c.drawString(MARGIN + 0.03*inch, label_y, dow_label)
        
        for i in range(num_months):
            month_idx = self.start_month + i - 1
            if month_idx >= 12:
                break
            
            month_x = grid_x + i * month_width
            date_col_width = month_width * 0.08
            event_col_width = month_width * 0.92
            
            divider_x = month_x + date_col_width
            c.line(divider_x, grid_y, divider_x, grid_y + grid_height)
            
            self._draw_month_column(c, month_x, grid_y, date_col_width, event_col_width,
                                   row_height, self.year, month_idx + 1, day_labels)
    
    def _draw_month_column(self, c, x, y, date_width, event_width, row_height, year, month, day_labels):
        first_day = date(year, month, 1)
        num_days = calendar.monthrange(year, month)[1]

        c.setFont(FONT_SMALL, 10)

        for day in range(1, num_days + 1):
            current_date = date(year, month, day)
            weekday = current_date.weekday()

            row_idx = (day - 1) + (first_day.weekday())
            cell_y = y + (37 - row_idx) * row_height

            if weekday >= 5:
                c.setFillColor(COLOR_WEEKEND)
                c.rect(x, cell_y - row_height, date_width + event_width, row_height, fill=1, stroke=0)

            if self.current_month == month:
                c.setFillColor(COLOR_LINK)
            else:
                c.setFillColor(COLOR_TEXT)

            day_str = str(day)
            c.drawString(x + 0.02*inch, cell_y - row_height/2 - 0.05*inch, day_str)

            if self.current_month == month:
                day_width = c.stringWidth(day_str, FONT_SMALL, 10)
                self.add_link(x + 0.02*inch, cell_y - row_height/2 - 0.1*inch,
                             x + 0.02*inch + day_width + 0.05*inch, cell_y - row_height/2 + 0.1*inch,
                             f'day_{year}_{month:02d}_{day:02d}_schedule')
            
            items_for_day = [item for item in self.yearly_items if item['date'] == current_date]
            if items_for_day:
                c.setFont(FONT_SMALL, 9)
                c.setFillColor(COLOR_EVENT)
                event_text = items_for_day[0]['text']
                if len(event_text) > 20:
                    event_text = event_text[:19] + ".."
                c.drawString(x + date_width + 0.02*inch, cell_y - row_height/2 - 0.05*inch, event_text)
                c.setFont(FONT_SMALL, 8)

            if weekday == 0:
                week_num = current_date.isocalendar()[1]
                c.setFont(FONT_SMALL, 9)
                c.setFillColor(COLOR_TEXT)
                c.drawRightString(x + date_width + event_width - 0.02*inch, cell_y - row_height/2 - 0.05*inch,
                           f"({week_num})")
                c.setFont(FONT_SMALL, 8)


class MonthlyOverviewPage(PlannerPage):
    """Monthly calendar overview page."""
    def __init__(self, year, month):
        super().__init__(f'month_{year}_{month:02d}')
        self.year = year
        self.month = month
    
    def render(self, c):
        c.bookmarkPage(self.bookmark_name)
        
        month_name = calendar.month_name[self.month]
        c.setFont(FONT_HEADER, 16)
        c.drawString(MARGIN, PAGE_HEIGHT - 0.6*inch, f"{month_name} {self.year}")
        
        grid_x = MARGIN
        grid_y = MARGIN + 0.5*inch
        grid_width = PAGE_WIDTH - 2*MARGIN
        grid_height = PAGE_HEIGHT - 1.5*inch - grid_y
        
        num_cols = 7
        col_width = grid_width / num_cols
        
        cal = calendar.monthcalendar(self.year, self.month)
        num_weeks = len(cal)
        row_height = grid_height / (num_weeks + 1)
        
        c.setFont(FONT_HEADER, 12)
        header_y = grid_y + grid_height + 0.1*inch
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day_name in enumerate(day_names):
            c.drawString(grid_x + i*col_width + 0.1*inch, header_y, day_name)
        
        c.setStrokeColor(COLOR_GRID)
        c.setLineWidth(0.5)
        
        for i in range(num_weeks + 2):
            line_y = grid_y + grid_height - i * row_height
            c.line(grid_x, line_y, grid_x + grid_width, line_y)
        
        for i in range(num_cols + 1):
            line_x = grid_x + i * col_width
            c.line(line_x, grid_y, line_x, grid_y + grid_height)
        
        for week_idx, week in enumerate(cal):
            if week[0] != 0:
                first_day_of_week = date(self.year, self.month, week[0])
            else:
                for day in week:
                    if day != 0:
                        first_day_of_week = date(self.year, self.month, day)
                        break
                while first_day_of_week.weekday() != 0:
                    first_day_of_week -= timedelta(days=1)
                
                week_num = first_day_of_week.isocalendar()[1]
                week_y = grid_y + grid_height - week_idx * row_height - 0.25*inch
                
                c.setFillColor(COLOR_LINK)
                c.setFont(FONT_SMALL, 10)
                c.drawString(MARGIN + 0.05*inch, week_y, f"({week_num})")
                
                self.add_link(MARGIN, week_y - 0.05*inch, MARGIN + 0.35*inch, week_y + 0.15*inch,
                             f'week_{self.year}_W{week_num:02d}')
            
            for day_idx, day in enumerate(week):
                if day != 0:
                    cell_x = grid_x + day_idx * col_width + 0.1*inch
                    cell_y = grid_y + grid_height - week_idx * row_height - 0.25*inch
                    
                    c.setFillColor(COLOR_LINK)
                    c.setFont(FONT_BODY, 12)
                    c.drawString(cell_x, cell_y, str(day))
                    
                    day_date = date(self.year, self.month, day)
                    self.add_link(cell_x - 0.05*inch, cell_y - 0.05*inch, 
                                 cell_x + col_width - 0.15*inch, cell_y + 0.2*inch,
                                 f'day_{day_date.year}_{day_date.month:02d}_{day_date.day:02d}_schedule')
        
        c.setFillColor(COLOR_TEXT)


class WeeklyPage(PlannerPage):
    """Weekly time-budget worksheet page."""
    def __init__(self, week_start_date, events=None):
        self.week_start_date = week_start_date
        self.week_num = week_start_date.isocalendar()[1]
        self.events = events or []
        super().__init__(f'week_{week_start_date.year}_W{self.week_num:02d}')
    
    def render(self, c):
        c.bookmarkPage(self.bookmark_name)
        
        week_end = self.week_start_date + timedelta(days=6)
        
        c.setFont(FONT_HEADER, 16)
        header_text = f"Week ({self.week_num}), {self.week_start_date.strftime('%b %d')} -> {week_end.strftime('%b %d, %Y')}"
        c.drawString(MARGIN, PAGE_HEIGHT - 0.6*inch, header_text)
        
        c.setFillColor(COLOR_LINK)
        c.setFont(FONT_SMALL, 12)
        link_x = PAGE_WIDTH - MARGIN - 1*inch
        c.drawString(link_x, PAGE_HEIGHT - 0.6*inch, "-> Notes")
        self.add_link(link_x, PAGE_HEIGHT - 0.7*inch, link_x + 0.6*inch, PAGE_HEIGHT - 0.5*inch, 'notes')
        c.setFillColor(COLOR_TEXT)
        
        grid_top = PAGE_HEIGHT - 1*inch
        grid_height = grid_top - MARGIN - 0.5*inch
        self._draw_weekly_grid(c, MARGIN, MARGIN + 0.5*inch, PAGE_WIDTH - 2*MARGIN, 
                        grid_height, self.week_start_date)
    
    def _draw_weekly_grid(self, c, x, y, width, height, week_start):
        time_col_width = 0.65*inch
        day_cols_width = width - time_col_width
        num_day_cols = 7
        day_col_width = day_cols_width / num_day_cols
        num_rows = 38
        row_height = height / num_rows
        
        c.setFont(FONT_HEADER, 12)
        header_y = y + height + 0.1*inch
        headers = ["Time", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        c.drawString(x + 0.02*inch, header_y, headers[0])
        for i in range(1, 8):
            header_x = x + time_col_width + (i-1)*day_col_width + 0.05*inch
            c.drawString(header_x, header_y, headers[i])
        
        c.setStrokeColor(COLOR_GRID)
        c.setLineWidth(0.5)
        
        for i in range(num_rows + 1):
            line_y = y + height - i * row_height
            c.line(x, line_y, x + width, line_y)
        
        c.line(x + time_col_width, y, x + time_col_width, y + height)
        
        for i in range(1, num_day_cols + 1):
            line_x = x + time_col_width + i * day_col_width
            c.line(line_x, y, line_x, y + height)
        
        c.setFont(FONT_SMALL, 8)
        c.drawString(x + 0.02*inch, y + height - 0.5*row_height - 0.05*inch, "00:00-05:00")
        
        for i in range(37):
            hour = 5 + i // 2
            minute = 30 if i % 2 == 1 else 0
            next_hour = hour if minute == 0 else hour + 1
            next_minute = 30 if minute == 0 else 0
            
            time_str = f"{hour:02d}:{minute:02d}-{next_hour:02d}:{next_minute:02d}"
            row_y = y + height - (i + 1.5) * row_height - 0.05*inch
            c.drawString(x + 0.02*inch, row_y, time_str)
        
        self._draw_events(c, x, y, width, height, time_col_width, day_col_width, row_height)
    
    def _draw_events(self, c, x, y, width, height, time_col_width, day_col_width, row_height):
        """Draw events on the weekly grid."""
        c.setFont(FONT_SMALL, 8)
        
        for event in self.events:
            if event['is_all_day']:
                continue
            
            event_date = event['start'].date()
            days_from_start = (event_date - self.week_start_date).days
            
            if 0 <= days_from_start < 7:
                start_hour = event['start'].hour
                start_minute = event['start'].minute
                end_hour = event['end'].hour
                end_minute = event['end'].minute
                
                if start_hour >= 5 and start_hour < 23:
                    start_row = ((start_hour - 5) * 2) + (1 if start_minute >= 30 else 0)
                    duration_minutes = (end_hour * 60 + end_minute) - (start_hour * 60 + start_minute)
                    duration_rows = duration_minutes / 30.0
                    
                    event_x = x + time_col_width + days_from_start * day_col_width + 0.02*inch
                    event_y = y + height - (start_row + 1.5) * row_height
                    event_height = duration_rows * row_height
                    event_width = day_col_width - 0.04*inch
                    
                    c.setFillColorRGB(0.29, 0.56, 0.89, alpha=0.1)
                    c.rect(event_x, event_y, event_width, event_height, fill=1, stroke=0)
                    
                    c.setFillColor(COLOR_EVENT)
                    label = event['label']
                    if len(label) > 15:
                        label = label[:12] + "..."
                    
                    c.drawString(event_x + 0.02*inch, event_y + event_height - 0.1*inch, label)
        
        c.setFillColor(COLOR_TEXT)


class DailySchedulePage(PlannerPage):
    """Daily schedule page with hourly time blocks."""
    def __init__(self, date_obj, events=None):
        self.date_obj = date_obj
        self.events = events or []
        super().__init__(f'day_{date_obj.year}_{date_obj.month:02d}_{date_obj.day:02d}_schedule')
    
    def render(self, c):
        c.bookmarkPage(self.bookmark_name)
        
        y = PAGE_HEIGHT - 0.6*inch
        self._draw_daily_header(c, y)
        
        grid_top = PAGE_HEIGHT - 1*inch
        grid_height = grid_top - MARGIN - 0.5*inch
        self._draw_daily_schedule(c, MARGIN, MARGIN + 0.5*inch, PAGE_WIDTH - 2*MARGIN, 
                                 grid_height)
    
    def _draw_daily_header(self, c, y):
        c.setFont(FONT_HEADER, 14)
        
        month_name = self.date_obj.strftime("%B")
        day_str = self.date_obj.strftime("%A, ")
        day_num = self.date_obj.strftime(" %d, ")
        year_str = str(self.date_obj.year)
        iso_cal = self.date_obj.isocalendar()
        week_str = f" ({iso_cal[1]})"
        
        current_x = MARGIN
        
        c.setFillColor(COLOR_TEXT)
        c.drawString(current_x, y, day_str)
        current_x += c.stringWidth(day_str, FONT_HEADER, 16)
        
        c.setFillColor(COLOR_LINK)
        c.drawString(current_x, y, month_name)
        month_width = c.stringWidth(month_name, FONT_HEADER, 16)
        self.add_link(current_x, y - 0.05*inch, current_x + month_width, y + 0.15*inch,
                     f'month_{self.date_obj.year}_{self.date_obj.month:02d}')
        current_x += month_width
        
        c.setFillColor(COLOR_TEXT)
        c.drawString(current_x, y, day_num)
        current_x += c.stringWidth(day_num, FONT_HEADER, 14)
        
        c.setFillColor(COLOR_LINK)
        c.drawString(current_x, y, year_str)
        year_width = c.stringWidth(year_str, FONT_HEADER, 14)
        
        year_page_num = ((self.date_obj.month - 1) // 3) + 1
        self.add_link(current_x, y - 0.05*inch, current_x + year_width, y + 0.15*inch,
                     f'year_{self.date_obj.year}_page{year_page_num}')
        current_x += year_width
        
        c.setFillColor(COLOR_TEXT)
        c.drawString(current_x, y, week_str)
        
        c.setFillColor(COLOR_LINK)
        c.setFont(FONT_SMALL, 11)
        link_x = PAGE_WIDTH - MARGIN - 1*inch
        c.drawString(link_x, y, "-> Notes")
        self.add_link(link_x, y - 0.1*inch, link_x + 0.6*inch, y + 0.15*inch, 'notes')
        c.setFillColor(COLOR_TEXT)
    
    def _draw_daily_schedule(self, c, x, y, width, height):
        c.setFont(FONT_SMALL, 11)
        
        start_hour = 5
        end_hour = 23
        num_hours = end_hour - start_hour
        hour_height = height / num_hours
        
        c.setStrokeColor(COLOR_GRID)
        c.setLineWidth(0.5)
        
        for i in range(num_hours + 1):
            line_y = y + height - i * hour_height
            c.line(x, line_y, x + width, line_y)
        
        time_col_width = 0.6*inch
        c.line(x + time_col_width, y, x + time_col_width, y + height)
        
        for i in range(num_hours):
            hour = start_hour + i
            time_str = f"{hour:02d}:00"
            time_y = y + height - i * hour_height - 0.15*inch
            c.drawString(x + 0.05*inch, time_y, time_str)
        
        self._draw_events(c, x, y, width, height, time_col_width, hour_height, start_hour)
    
    def _draw_events(self, c, x, y, width, height, time_col_width, hour_height, start_hour):
        """Draw events on the daily schedule."""
        c.setFont(FONT_SMALL, 9)
        
        for event in self.events:
            if event['is_all_day']:
                continue
            
            start_hour_val = event['start'].hour
            start_minute = event['start'].minute
            end_hour_val = event['end'].hour
            end_minute = event['end'].minute
            
            if start_hour_val >= start_hour and start_hour_val < 23:
                hours_from_start = start_hour_val - start_hour
                minutes_from_hour = start_minute / 60.0
                
                event_y_offset = (hours_from_start + minutes_from_hour) * hour_height
                event_y = y + height - event_y_offset
                
                duration_hours = (end_hour_val - start_hour_val) + (end_minute - start_minute) / 60.0
                event_height = duration_hours * hour_height
                
                event_x = x + time_col_width + 0.05*inch
                event_width = width - time_col_width - 0.1*inch
                
                c.setFillColorRGB(0.29, 0.56, 0.89, alpha=0.1)
                c.rect(event_x, event_y - event_height, event_width, event_height, fill=1, stroke=0)
                
                c.setFillColor(COLOR_EVENT)
                c.drawString(event_x + 0.05*inch, event_y - 0.15*inch, event['label'])
        
        c.setFillColor(COLOR_TEXT)


class DailyTasksPage(PlannerPage):
    """Daily tasks and summary page."""
    def __init__(self, date_obj, tasks=None, headline_events=None):
        self.date_obj = date_obj
        self.tasks = tasks or []
        self.headline_events = headline_events or []
        super().__init__(f'day_{date_obj.year}_{date_obj.month:02d}_{date_obj.day:02d}_tasks')
    
    def render(self, c):
        c.bookmarkPage(self.bookmark_name)
        
        y = PAGE_HEIGHT - 0.6*inch
        self._draw_daily_header(c, y)
        
        section_y = PAGE_HEIGHT - 1.2*inch
        
        if self.headline_events:
            headline_height = 0.6*inch
            self._draw_headline_section(c, MARGIN, section_y, PAGE_WIDTH - 2*MARGIN, 
                                       headline_height, self.headline_events)
            section_y -= headline_height + 0.2*inch
        
        remaining_height = section_y - MARGIN - 0.2*inch
        section_height = remaining_height / 3
        
        self._draw_section(c, MARGIN, section_y, PAGE_WIDTH - 2*MARGIN, 
                          section_height, "Top 3 Priorities", 3)
        
        section_y -= section_height + 0.2*inch
        self._draw_tasks_section(c, MARGIN, section_y, PAGE_WIDTH - 2*MARGIN, 
                          section_height, "Today's Tasks", self.tasks)
        
        section_y -= section_height + 0.2*inch
        self._draw_section(c, MARGIN, section_y, PAGE_WIDTH - 2*MARGIN, 
                          section_height, "Daily Summary", 0)
    
    def _draw_daily_header(self, c, y):
        c.setFont(FONT_HEADER, 14)
        
        month_name = self.date_obj.strftime("%B")
        day_str = self.date_obj.strftime("%A, ")
        day_num = self.date_obj.strftime(" %d, ")
        year_str = str(self.date_obj.year)
        iso_cal = self.date_obj.isocalendar()
        week_str = f" ({iso_cal[1]})"
        
        current_x = MARGIN
        
        c.setFillColor(COLOR_TEXT)
        c.drawString(current_x, y, day_str)
        current_x += c.stringWidth(day_str, FONT_HEADER, 14)
        
        c.setFillColor(COLOR_LINK)
        c.drawString(current_x, y, month_name)
        month_width = c.stringWidth(month_name, FONT_HEADER, 14)
        self.add_link(current_x, y - 0.05*inch, current_x + month_width, y + 0.15*inch,
                     f'month_{self.date_obj.year}_{self.date_obj.month:02d}')
        current_x += month_width
        
        c.setFillColor(COLOR_TEXT)
        c.drawString(current_x, y, day_num)
        current_x += c.stringWidth(day_num, FONT_HEADER, 14)
        
        c.setFillColor(COLOR_LINK)
        c.drawString(current_x, y, year_str)
        year_width = c.stringWidth(year_str, FONT_HEADER, 14)
        
        year_page_num = ((self.date_obj.month - 1) // 3) + 1
        self.add_link(current_x, y - 0.05*inch, current_x + year_width, y + 0.15*inch,
                     f'year_{self.date_obj.year}_page{year_page_num}')
        current_x += year_width
        
        c.setFillColor(COLOR_TEXT)
        c.drawString(current_x, y, week_str)
        
        c.setFillColor(COLOR_LINK)
        c.setFont(FONT_SMALL, 9)
        link_x = PAGE_WIDTH - MARGIN - 1*inch
        c.drawString(link_x, y, "-> Notes")
        self.add_link(link_x, y - 0.1*inch, link_x + 0.6*inch, y + 0.15*inch, 'notes')
        c.setFillColor(COLOR_TEXT)
    
    def _draw_headline_section(self, c, x, y, width, height, headline_events):
        """Draw headline events section."""
        c.setFont(FONT_HEADER, 11)
        c.setFillColor(COLOR_EVENT)
        c.drawString(x, y + height - 0.2*inch, "* Headline Events")
        
        c.setStrokeColor(COLOR_GRID)
        c.setLineWidth(0.5)
        c.rect(x, y, width, height)
        
        c.setFont(FONT_SMALL, 11)
        c.setFillColor(COLOR_TEXT)
        
        for i, event in enumerate(headline_events[:2]):
            event_y = y + height - 0.4*inch - i * 0.15*inch
            c.drawString(x + 0.1*inch, event_y, f"- {event['text']}")
    
    def _draw_section(self, c, x, y, width, height, title, num_lines):
        c.setFont(FONT_HEADER, 11)
        c.drawString(x, y + height - 0.2*inch, title)
        
        c.setStrokeColor(COLOR_GRID)
        c.setLineWidth(0.5)
        c.rect(x, y, width, height)
        
        if num_lines > 0:
            line_height = (height - 0.3*inch) / num_lines
            for i in range(1, num_lines):
                line_y = y + height - 0.3*inch - i * line_height
                c.line(x, line_y, x + width, line_y)
    
    def _draw_tasks_section(self, c, x, y, width, height, title, tasks):
        """Draw tasks section with actual tasks from Todoist."""
        c.setFont(FONT_HEADER, 11)
        c.drawString(x, y + height - 0.2*inch, title)
        
        c.setStrokeColor(COLOR_GRID)
        c.setLineWidth(0.5)
        c.rect(x, y, width, height)
        
        num_lines = 8
        line_height = (height - 0.3*inch) / num_lines
        
        for i in range(1, num_lines):
            line_y = y + height - 0.3*inch - i * line_height
            c.line(x, line_y, x + width, line_y)
        
        c.setFont(FONT_SMALL, 10)
        c.setFillColor(COLOR_TEXT)
        
        for i, task in enumerate(tasks[:num_lines]):
            task_y = y + height - 0.3*inch - i * line_height - 0.15*inch
            c.drawString(x + 0.1*inch, task_y, f"[ ] {task['text']}")


class NotesPage(PlannerPage):
    """Dot-grid notes page."""
    def __init__(self, page_num):
        super().__init__('notes')
        self.page_num = page_num
    
    def render(self, c):
        if self.page_num == 1:
            c.bookmarkPage(self.bookmark_name)
        
        c.setFont(FONT_HEADER, 12)
        c.drawString(MARGIN, PAGE_HEIGHT - 0.5*inch, f"Notes ({self.page_num}/10)")
        
        dot_spacing = 0.2*inch
        start_x = MARGIN
        start_y = MARGIN + 0.5*inch
        end_x = PAGE_WIDTH - MARGIN
        end_y = PAGE_HEIGHT - 0.8*inch
        
        c.setFillColor(COLOR_GRID)
        x = start_x
        while x <= end_x:
            y = start_y
            while y <= end_y:
                c.circle(x, y, 0.5, fill=1, stroke=0)
                y += dot_spacing
            x += dot_spacing
        
        c.setFillColor(COLOR_TEXT)