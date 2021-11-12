import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

    """Sample .env file contents
    SMTP_SERVER=apps.smtp.gov.bc.ca
    DEBUG_IDIR=jsmith
    DEBUG_EMAIL=john.smith@gov.bc.ca
    EMAIL_SENDLIST=recipient1@gov.bc.ca,recipient2@gov.bc.ca,recipient3@gov.bc.ca
    POSTGRES_USER=database_user
    POSTGRES_PASSWORD=database_password
    POSTGRES_HOST=localhost

    LDAP_USER=AD username
    LDAP_PASSWORD=AD password
    """


SMTP_SERVER = os.environ['SMTP_SERVER']
DEBUG_IDIR = os.environ['DEBUG_IDIR']
DEBUG_EMAIL = os.environ['DEBUG_EMAIL']
EMAIL_SENDLIST = os.environ['EMAIL_SENDLIST']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
POSTGRES_HOST = os.environ['POSTGRES_HOST']

LDAP_USER = os.environ['LDAP_USER']
LDAP_PASSWORD = os.environ['LDAP_PASSWORD']
