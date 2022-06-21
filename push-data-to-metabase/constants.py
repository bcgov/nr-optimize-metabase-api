import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

# Environment Variables for clean_h_drive.py - AD service account
LDAP_USER = os.environ['LDAP_USER']
LDAP_PASSWORD = os.environ['LDAP_PASSWORD']
