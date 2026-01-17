# reMarkable Calendar Generator

A Python tool that generates interactive PDF planners with Google Calendar and Todoist integration, optimized for the reMarkable tablet. Features terminal-style monospace fonts, subtle styling, and automatic (one way) sync to your reMarkable device.

I wanted to make more use of my reMarkable tablet now that I spend less time collecting, reading, and taking notes on journal articles. I like the simplicity of a daily journal page that tells me what is on the docket each day and wanted to save myself some time  transferring calendar events and todo items from Todoist. Because I already sync Todoist with my Google calendar I've handled things like duplicate entries, too. I still need to mark todo items done in the Todist app (ok, I _get_ to mark them done once on the remarkable as I work my way through my list and again in teh app at the end of the day - twice the satisfaction, really) but if (_when_) I push a few tasks to a future day, I wake up in the morning with an accurate journal page waiting for me.

I still take meeting notes in projet folders, but I like having the notes pages at the end of the month to collect the random notes/phone numbers/error codes/part numbers that seemed to otherwise collect in the margins of my paper journals. 

I broke the calendar out into months with an annual overview in each month for reference, but I rarely need to look back at the past in the annual overview. I just want to see what's happening in the future. Oh, there's a special note here: **Any todo item tagged with `@headline` in todoist gets added to that annual overview, so noteworthy things like travel, and holidays show up there. 

## Features

- **Interactive Navigation**: Clickable links between years, months, weeks, and days
- **Google Calendar Integration**: Automatically imports events from your Google Calendar
- **Todoist Integration**: Pulls tasks for each day
- **Terminal Aesthetic**: Courier monospace fonts for a clean, geeky look
- **Optimized for reMarkable**: Subtle shading, readable font sizes, weekend highlighting
- **Automatic Sync**: Direct SSH upload to reMarkable tablet
- **Docker Support**: Run as a scheduled container on your server
- **Comprehensive Views**:
  - Yearly overview (4 pages, 3 months each)
  - Monthly calendar
  - Weekly time-budget worksheets
  - Daily schedule pages (5am-11pm)
  - Daily task pages with priorities and summary sections
  - 10 dot-grid notes pages per month

## Prerequisites

- Python 3.7+
- reMarkable tablet (for sync feature)
- Google Calendar API credentials (optional)
- Todoist API token (optional)

## Installation

### Option 1: Local Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/remarkable-calendar.git
cd remarkable-calendar
```
2. Setup your virtual environment (however _you_ do that with your OS of choice)
3. Install the dependencies
```bash
pip install -r requirements.txt
```
4.  Gather the necessary configuration file information from Google and Todoist in addition to getting/having your reMarkable device ready for synchronizing, then create your .env file with the required credentials and settings.
```bash
# Optional: Google Calendar integration
GOOGLE_CREDENTIALS_FILE=credentials.json

# Optional: Todoist integration
TODOIST_API_TOKEN=your_todoist_token_here

# Optional: reMarkable sync
REMARKABLE_HOST=10.11.99.1
REMARKABLE_PASSWORD=your_remarkable_password
```

### Option 2: Docker Installation (Recommended for Servers)

Clone the repository:
```bash
git clone https://github.com/yourusername/remarkable-calendar.git
cd remarkable-calendar
```
1. Create .env file with your credentials (see Configuration section)
2. Build the Docker image:
```bash
docker-componse build
```

## Configuration

### Google Calendar Setup (Optional)

1. Go to Google Cloud Console
1. Create a new project
1. Enable the Google Calendar API
1. Create OAuth 2.0 credentials (Desktop app)
1. Download credentials and save as credentials.json
1. First run will open browser for authentication

### Todoist Setup (Optional)

1. Get your API token from Todoist Settings
1. Add to .env file as TODOIST_API_TOKEN
1. reMarkable Setup (Optional)
1. Enable SSH on your reMarkable:
1. Settings → Help → About → Copyrights and licenses
1. Tap on "GPLv3 Compliance" multiple times
1. Note the password shown
1. Connect reMarkable to same network as your computer
1. Find reMarkable IP address (Settings → Help → About)
1. Add to .env file

## Usage

### Local Usage

Generate a full year of monthly planners:
```bash
python cal_generator.py
```

Generate a full year of planners and sync them to your reMarkable device:
```bash
python generate_and_sync.py
``` 


#### Customize the Year

```python
if __name__ == "__main__":
    generate_full_year_planner(2026)  # Change year here
```


### Docker Usage

One-time run:
```bash
docker-compose run --rm calendar 2026
```

#### Automated daily sync

Setup a cron job on your server to run daily before you wake up:
```bash
crontab -e
```
Example for running at 5am:
```
0 5 * * * cd /path/to/remarkable-calendar && docker-compose run --rm calendar 2026 >> /var/log/remarkable-sync.log 2>&1
```

...or at 430am:
```
30 4 * * * cd /path/to/remarkable-calendar && docker-compose run --rm calendar 2026 >> /var/log/remarkable-sync.log 2>&1
```

#### Cron alternative: systemd Timer

Create `/etc/systemd/system/remarkable-sync.service` and paste this in there:
```ini
[Unit]
Description=Sync reMarkable Calendar
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/path/to/remarkable-calendar
ExecStart=/usr/bin/docker-compose run --rm calendar 2026
User=youruser
Group=yourgroup
```

Create `/etc/systemd/system/remarkable-sync.timer
```ini
[Unit]
Description=Daily reMarkable Calendar Sync
Requires=remarkable-sync.service

[Timer]
OnCalendar=*-*-* 05:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the service and start it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable remarkable-sync.timer
sudo systemctl start remarkable-sync.timer
```

Check the status:
```bash
sudo systemctl status remarkable-sync.timer
sudo systemctl list-timers
```

#### Customize the year

Edit the `docker-compose.yml` 
```yaml
command: ["2027"]  # Change year here
```
Or,
```bash
docker-compose run --rm calendar 2027
```

#### Environment Variables
The Docker container uses the same .env file as local installation. Required variables:

```bash
# Google Calendar (optional)
GOOGLE_CREDENTIALS_FILE=credentials.json

# Todoist (optional)
TODOIST_API_TOKEN=your_token

# reMarkable Sync (required for auto-sync)
REMARKABLE_HOST=10.11.99.1
REMARKABLE_PASSWORD=your_password
```

#### Volumes

The docker-compose.yml mounts:
```
./planner_YYYY:/app/planner_YYYY - Generated PDFs (persisted)
./credentials.json:/app/credentials.json:ro - Google credentials (read-only)
./token.json:/app/token.json - Google auth token (read-write)
```

#### Network Mode

Uses `network_mode: host` to access reMarkable on local network. If your reMarkable is on a different network, adjust accordingly.

#### Logs

View logs:
```bash
docker-compose logs
```
Or if using cron, check:
```bash
tail -f /var/log/remarkable-sync.log
```

## Project Structure
```plaintext
remarkable-calendar/
├── cal_generator.py       # Main planner generation logic
├── pages.py               # Page layout definitions
├── data_processor.py      # Google Calendar & Todoist integration
├── api_client.py          # API client implementations
├── sync_to_remarkable.py  # reMarkable sync functionality
├── generate_and_sync.py   # Combined generation and sync
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── dockerfile             # Docker image definition
├── docker-compose.yml     # Docker orchestration
├── .env                   # Environment variables (create this)
└── .gitignore             # Git ignore rules
```


## Customization
I've tried to make this easy to modify because I haven't really figured out for myself how this should look. (This would be a great place to contribution if you have design skills or a reasonable sense of asthetics. I obviously do not.)

### Fonts
```python
FONT_HEADER = 'Courier-Bold'  # Change to your preferred font
FONT_BODY = 'Courier'
FONT_SMALL = 'Courier'
```

### Colors

```python
COLOR_GRID = HexColor('#E0E0E0')      # Grid lines
COLOR_TEXT = HexColor('#000000')      # Main text
COLOR_LINK = HexColor('#0066CC')      # Clickable links
COLOR_EVENT = HexColor('#4A90E2')     # Events
COLOR_WEEKEND = HexColor('#F5F5F5')   # Weekend shading
```

### Page Layout

You might also want to modify the page contents to better suit your needs. I set this up to satisfy my personal workflow. Each page type is a class in pages.py:

* YearlyOverviewPage - Annual calendar view
* MonthlyOverviewPage - Month grid
* WeeklyPage - Time-budget worksheet
* DailySchedulePage - Hourly schedule
* DailyTasksPage - Tasks and priorities
* NotesPage - Dot-grid notes

## Troubleshooting

I may or may not have encountered issues with the setup and "learned a lot" while working through this. Here's a list of things that I discovered and resolved during the process:

### Google Calendar not syncing

Delete token.json and re-authenticate
Check that Calendar API is enabled in Google Cloud Console

### reMarkable sync fails

Verify reMarkable is on same network
Check SSH password is correct
Try connecting manually: `ssh root@10.11.99.1`

## Docker container can't reach reMarkable

Verify network_mode: host in docker-compose.yml
Test connectivity: `docker-compose run --rm calendar ping 10.11.99.1`
Ensure reMarkable is powered on and connected

### Cron job not running

Check cron logs: `grep CRON /var/log/syslog`
Verify paths are absolute in crontab
Ensure user has Docker permissions: `sudo usermod -aG docker $USER`

### PDFs look wrong on reMarkable

Ensure you're using letter size (8.5" x 11")
Font sizes below 7pt may be hard to read

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

Built with ReportLab for PDF generation
Integrates with Google Calendar API
Integrates with Todoist API
Inspired by the reMarkable community
Vibe coded with Claude Sonnet 4.5 via Abacus AI and CodeLLM 
