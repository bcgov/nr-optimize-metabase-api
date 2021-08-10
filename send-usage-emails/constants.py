import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

SMTP_SERVER = os.environ['SMTP_SERVER']
USE_DEBUG_IDIR = os.environ['USE_DEBUG_IDIR']
DEBUG_IDIR = os.environ['DEBUG_IDIR']
