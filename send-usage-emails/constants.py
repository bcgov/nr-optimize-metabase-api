import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

    """Sample .env file contents
    SMTP_SERVER=apps.smtp.gov.bc.ca
    (DEBUG is synonymous with ADMIN, and gets report/error emails)
    DEBUG_IDIR=jsmith
    DEBUG_EMAIL=john.smith@gov.bc.ca
    EMAIL_SENDLIST=recipient1@gov.bc.ca,recipient2@gov.bc.ca,recipient3@gov.bc.ca
    (Email Sendlist alternative format for Outlook:)
    EMAIL_SENDLIST=smith, john FLNR:EX <recipient1@gov.bc.ca>; smith, jane IIT:EX <recipient2@gov.bc.ca>
    EMAIL_OMITLIST=do-not-send1@gov.bc.ca,do-not-send2@gov.bc.ca

    POSTGRES_USER=database_user
    POSTGRES_PASSWORD=database_password
    POSTGRES_HOST=localhost

    LDAP_USER=AD username
    LDAP_PASSWORD=AD password

    (On Windows machines:)
    GRAPH_FILE_PATH=graph.png
    GOLD_STAR_FILE_PATH=send-usage-emails/gold-star.png
    (On Linux machines:)
    GRAPH_FILE_PATH=/tmp/graph.png
    GOLD_STAR_FILE_PATH=gold-star.png
    """

SMTP_SERVER = os.environ['SMTP_SERVER']
DEBUG_IDIR = os.environ['DEBUG_IDIR']
DEBUG_EMAIL = os.environ['DEBUG_EMAIL']

EMAIL_SENDLIST = os.environ['EMAIL_SENDLIST']
EMAIL_OMITLIST = os.environ['EMAIL_OMITLIST']

POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
POSTGRES_HOST = os.environ['POSTGRES_HOST']

LDAP_USER = os.environ['LDAP_USER']
LDAP_PASSWORD = os.environ['LDAP_PASSWORD']

GRAPH_FILE_PATH = os.environ['GRAPH_FILE_PATH']
GOLD_STAR_FILE_PATH = os.environ['GOLD_STAR_FILE_PATH']
