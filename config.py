import os 

from dotenv import load_dotenv

load_dotenv()

def get_secret(key):
    if key in os.environ:
        return os.environ.get(key)
    if key in st.secrets:
        return st.secrets[key]
    return None