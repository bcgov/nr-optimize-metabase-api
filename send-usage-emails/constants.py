import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

SMTP_SERVER = os.environ['SMTP_SERVER']
DEBUG_IDIR = os.environ['DEBUG_IDIR']
DEBUG_EMAIL = os.environ['DEBUG_EMAIL']
EMAIL_WHITELIST = os.environ['EMAIL_WHITELIST']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
POSTGRES_HOST = os.environ['POSTGRES_HOST']

LDAP_USER = os.environ['LDAP_USER']
LDAP_PASSWORD = None
if "LDAP_PASSWORD" in os.environ:
    LDAP_PASSWORD = os.environ['LDAP_PASSWORD']
