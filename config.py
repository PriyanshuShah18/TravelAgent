import os 

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

def get_secret(key: str):
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass # Not running in streamlit

    return os.getenv(key)


'''
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

def get_secret(key):
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]

    except:
        pass

    return os.getenv(key)
'''