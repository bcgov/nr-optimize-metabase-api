import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

BUCKET_NAME = os.environ['BUCKET_NAME']
BUCKET_USER = os.environ['BUCKET_USER']
BUCKET_SECRET = os.environ['BUCKET_SECRET']

# Environment Variables for update_quarterly_reporting.py - government email (username) & IDIR Password
LDAP_EMAIL = os.environ['LDAP_EMAIL']
LDAP_PASSWORD = os.environ['LDAP_PASSWORD']
