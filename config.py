import os 

from dotenv import load_dotenv

load_dotenv()

def get_secret(key):
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