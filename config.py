import os
from dotenv import load_dotenv

load_dotenv()

TODOIST_API_TOKEN = os.getenv('TODOIST_API_TOKEN')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_TOKEN_FILE = 'token.json'
