from langchain_groq import ChatGroq
from tools import get_distance,estimate_cost,estimate_time_by_mode
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory
import traceback
import streamlit as st
import json
import re


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
        distance_km= float(distance_km.strip())
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

def extract_travel_detials(user_query):
    extraction_prompt= f"""
    Extract the following details from the user query:

    - Source city
    - Destination City
    - Start Date (convert to YYYY-MM-DD format)
    - End Date (if mentioned,otherwise null)

    Return ONLY valid JSON like:
    {{
        "source":"...",
        "destination":"...",
        "start_date":"YYYY-MM-DD",
        "end_date":"YYYY-MM-DD or null",
    }}

    Query:
    {user_query}
    """

    response= llm.invoke(extraction_prompt)
    text= response.content

    json_match = re.search(r"\{.*\}",text,re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    else:
        raise Exception("Could not extract travel details.")

def travel_agent(user_query,budget,priority):
    details=extract_travel_details(user_query)

    source= details["source"]
    destination = details["destination"]
    start_date = details["start_date"]
    end_date = details.get("end_date")
    
    trip_type= "round" if end_date else "oneway"

    travel_data={
        "source":source,
        "destination":destination,
        "start_date":start_date,
        "end_date":end_date,
        "trip_type":trip_type,
        "budget":budget,
        "priority":priority
    }

    return travel_agent(travel_data)
  