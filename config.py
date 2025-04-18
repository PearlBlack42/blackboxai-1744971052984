import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Security settings
SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_replace_in_production')

# Database settings
DATABASE_PATH = os.path.join(BASE_DIR, 'simkopkar.mDB')

# App settings
DEBUG = True
