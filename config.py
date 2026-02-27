import os 

from dotenv import load_dotenv

load_dotenv()

def get_secret(key):
    return os.getenv(key)