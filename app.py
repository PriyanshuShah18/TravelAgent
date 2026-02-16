import streamlit as st
from agent import travel_agent
from datetime import date
#from ocr import extract_text_from_ticket

#st.write("App started")
st.title("AI Travel Recommendation Agent")

#input_type= st.radio("Choose Input Type",["Text","Ticket Image"])

#if input_type=="Text":
    #text= st.text_area("Enter travel request")

#elif input_type=="Ticket Image":
#image = st.file_uploader("Upload Ticket")
#if image:
#    text= extract_text_from_ticket(image)
#    st.write("Extracted text:",text)
# Travel inputs

st.subheader("Travel Details")

# Takes natural language input, stores in user_query and sends it to the agent.
user_query= st.text_area(
    "Enter your travel plan",
    placeholder="I want to go from Ahmedabad to Mumbai from 23rd February to 26th February"
)
#source= st.text_input("From (Source City)")
#destination= st.text_input("To (Destination City)")

#date_range= st.date_input(
#    "Select Travel Date(s)",
#    value=(date.today(), date.today()),
#    min_value= date.today()
#    )

budget= st.number_input("Budget (INR)", min_value=500)
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