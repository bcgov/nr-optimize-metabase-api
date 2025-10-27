import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

# Environment Variables for database
POSTGRES_DB_NAME = os.environ['POSTGRES_DB_NAME']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASS = os.environ['POSTGRES_PASS']

# Environment Variables for AD connection
AD_SERVER = os.environ['AD_SERVER']
AD_USER = os.environ['AD_USER']
AD_PASSWORD = os.environ['AD_PASSWORD']
SEARCH_BASE = os.environ['SEARCH_BASE']