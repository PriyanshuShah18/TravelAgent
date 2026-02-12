import streamlit as st
from agent import travel_agent
#from ocr import extract_text_from_ticket

#st.write("App started")
st.title("AI Travel Recommendation Agent")

#input_type= st.radio("Choose Input Type",["Text","Ticket Image"])

#if input_type=="Text":
    #text= st.text_area("Enter travel request")

#elif input_type=="Ticket Image":
'''image = st.file_uploader("Upload Ticket")
if image:
    text= extract_text_from_ticket(image)
    st.write("Extracted text:",text)'''
# Travel inputs

st.subheader("Travel Details")
source= st.text_input("From (Source City)")
destination= st.text_input("To (Destination City)")

budget= st.number_input("Budget (INR)", min_value=500)
priority= st.selectbox("Priority",["time","budget"])

if st.button("Get Recommendation"):

    if not source or not destination:
        st.error("Please enter both source and destination")
    else:
        travel_data={
            "source":source,
            "destination":destination,
            "budget":budget,
            "priority": priority
        }


    result= travel_agent(travel_data)
    st.success(result)