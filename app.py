import streamlit as st
import os

# Streamlit Cloud Secrets
if "STREAMLIT_RUNTIME" in os.environ:
    import os.path
    has_secrets = os.path.exists(".streamlit/secrets.toml") or os.path.exists(os.path.expanduser("~/.streamlit/secrets.toml"))
    if has_secrets:
        try:
            for key,value in st.secrets.items():
                os.environ[key] = value
        except Exception:
            pass

from agent import travel_agent
from datetime import date

st.title("AI Travel Recommendation Agent")

# Travel inputs

st.subheader("Travel Details")

# Takes natural language input, stores in user_query and sends it to the agent.
user_query= st.text_area(
    "Enter your travel plan",
    placeholder="I want to go from Ahmedabad to Mumbai from 23rd February to 26th February"
)

budget= st.number_input("Budget(INR)", min_value=500)
priority= st.selectbox("Priority",["time","budget"])

if st.button("Get Recommendation"):
    if not user_query:
        st.error("Please enter your travel plan.")
        st.stop()
    
    with st.spinner("Analyzing your trip and finding best options..."):
        result= travel_agent(
            user_query,
            budget,
            priority
        )
    st.success(result)