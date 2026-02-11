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
    groq_key=groq_key
                      
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
    Input format: distance_km
    """
    try:
        distance= float(input_text)
        result= estimate_cost(distance)
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
        description="Use this to estimate cost for bus,train and flight.Input : distance_km"

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

    query= f"""
    Plan the best travel option.

    Source: {source}
    Destination: {destination}
    Budget: {budget}
    Priority: {priority}

    Steps:
    1. Get distance using GetDistancetool.
    2. Estimate cost using EstimateCost.
    3. Estimate time using Estimation.
    4. Choose best option based on priority and budget.
    5. Explain clearly.
    """

    response= agent.run(query)

    return response