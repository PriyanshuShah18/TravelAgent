from langchain_groq import ChatGroq
from tools import get_distance,estimate_cost,estimate_time_by_mode
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory
import traceback
import streamlit as st

groq_key=st.secrets["GROQ_API_KEY"]

llm= ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,                
)
 
def safe_get_distance(input_text):
    """
    Input format: 'source,destination'
    """
    try:
        source,destination= input_text.split(",")
        result= get_distance(source.strip(),destination.strip())
        return str(result)
    except Exception as e:
        return f"Distance tool failed.Error: {str(e)}"


def safe_estimate_cost(input_text):
    """
    Input format: distance_km,start_date
    """
    try:
        distance_km,start_date= input_text.split(",")
        distance= float(distance_km.strip())
        result= estimate_cost(distance_km, start_date.strip())
        return str(result)
    except Exception as e:
        return f"Cost tool failed. Error: {str(e)}"


def safe_estimate_time(input_text):
    """
    Input format: distance_km,duration_min
    """
    try:
        distance_km,duration_min=map(float,input_text.split(","))
        result= estimate_time_by_mode(distance_km,duration_min)
        return str(result)
    except Exception as e:
        return f"Time tool failed. Error: {str(e)}"

# DEFINE TOOLS FOR AGENT

tools=[
    Tool(
        name="GetDistance",
        func=safe_get_distance,
        description="Use this to get distance and road duration.Input format: source,destination"
    ),
    Tool(
        name="EstimateCost",
        func=safe_estimate_cost,
        description="Use this to estimate cost for bus,train and flight.Input : distance_km,start_date"

    ),
    Tool(
        name="EstimateTime",
        func=safe_estimate_time,
        description="Use this to estimate travel time per mode.Input: distance_km,duration_min"
    )
]

# MEMORY
memory= ConversationBufferMemory(memory_key="chat_history",return_messages=True)

# REACT AGENT

agent= initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True
)

# MAIN FUNCTION

def travel_agent(travel_data):
    source=travel_data["source"]
    destination=travel_data["destination"]
    budget= travel_data["budget"]
    priority= travel_data["priority"]
    start_date= travel_data["start_date"]
    end_date= travel_data("end_date")
    trip_type= travel_data.get("trip_type")

    query= f"""
    Plan the best travel option.

    Source: {source}
    Destination: {destination}
    Travel Start Date: {start_date}
    Trip Type: {trip_type}
    Return Date: {end_date if end_date else "Not Applicable"}
    
    Budget: {budget}
    Priority: {priority}

    If round trip:
    - Consider return journey cost.
    - Calculate total travel cost.


    Important:
    1. Consider travel date while estimating cost.
    2. Weekend or near-term bookings may affect pricing.
    3. Use tools to calculate distance, time and cost.
    4. Choose best option based on priority and budget.
    5. Explain clearly.
    """

    response= agent.run(query)

    return response