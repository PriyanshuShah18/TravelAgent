import os 

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

def get_secret(key: str):
    # Try environment variable first to avoid triggering Streamlit warnings
    val = os.getenv(key)
    if val is not None:
        return val

    try:
        import streamlit as st
        
        # Guard against accessing st.secrets when secrets.toml doesn't exist
        # to prevent the UI from displaying "No secrets found" warning.
        has_secrets = os.path.exists(".streamlit/secrets.toml") or os.path.exists(os.path.expanduser("~/.streamlit/secrets.toml"))
        
        if has_secrets:
            if key in st.secrets:
                return st.secrets[key]
    except Exception:
        pass # Not running in streamlit or no secrets found

    return None