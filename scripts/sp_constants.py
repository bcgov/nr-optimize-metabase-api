import os
import dotenv

envPath = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

# Environment variables for SP_login.py - government email (username) & IDIR Password
USER_NAME = os.environ["USER_NAME"]
PASSWORD = os.environ["PASSWORD"]
