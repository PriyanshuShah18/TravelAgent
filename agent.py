from langchain_groq import ChatGroq # Groq LLM Wrapper
from tools import get_distance,estimate_cost,estimate_time_by_mode,search_with_serper


from langchain.agents import initialize_agent, Tool
# Tool wraps Python Functions so LLM can use them
# initialize_agent builds the reasoning loop (Reason+Act: ReAct agent)

from langchain.agents.agent_types import AgentType
# Selecting reasoning strategy

from langchain.memory import ConversationBufferMemory
# Agent remebers previous context.

import traceback      # Debugging
import streamlit as st  # access API key
import json     # Parse structured LLM output
import re       # Extract JSON via regex

import os
from langsmith import Client

os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"]= "true"
os.environ["LANGCHAIN_PROJECT"]="travel-agent"


groq_key=st.secrets["GROQ_API_KEY"]

llm= ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,        # Deterministic Reasoning        
    groq_api_key=groq_key
)
 
# The original functions return dictionaries but LangChain tools must return strings

def safe_search(input_text):
    try:
        return search_with_serper(input_text)
    except Exception as e:
        return f"Search failed: {str(e)}"


def safe_get_distance(input_text):
    """
    Input format: 'source,destination'
    """
    try:
        source,destination= input_text.split(",")
        result= get_distance(source.strip(),destination.strip())
        print("DEBUG DISTANCE:",result)
        return str(result)
    except Exception as e:
        return f"Distance tool failed.Error: {str(e)}"

def safe_estimate_cost(input_text):
    """
    Input format: distance_km,start_date,source,destination,trip_type
    """
    try:
        parts = [p.strip() for p in input_text.split(",")]

        if len(parts) != 5:
            return "Cost tool failed. Incorrect input format."

        distance_km= float(parts[0])
        start_date= parts[1]
        source= parts[2]
        destination= parts[3]
        trip_type= parts[4]
        
        result= estimate_cost(
            distance_km,
            start_date,
            trip_type=trip_type,
            source= source,
            destination=destination
            )
        return str(result)
    except Exception as e:
        return f"Cost tool failed. Error: {str(e)}"


def safe_estimate_time(input_text):
    """
    Input format: distance_km
    """
    try:
        distance_km=float(input_text.strip())
        result= estimate_time_by_mode(distance_km,0)
        return str(result)
    except Exception as e:
        return f"Time tool failed. Error: {str(e)}"

# DEFINE TOOLS FOR AGENT

# Description is very important as the LLM reads this desc to decide which tool to call.
# This is how tool selection works.
tools=[
    Tool(
        name="GetDistance",
        func=safe_get_distance,
        description="Use this to get distance and road duration.Input format: source,destination"
    ),
    Tool(
        name="EstimateCost",
        func=safe_estimate_cost,
        description="Use this to estimate cost for bus,train and flight.Input : distance_km,start_date,source,destination,trip_type"

    ),
    Tool(
        name="EstimateTime",
        func=safe_estimate_time,
        description="Use this to estimate travel time per mode.Input: distance_km"
    ),
    Tool(
        name="WebSearch",
        func=safe_search,
        description="Use this to search live travel conditions,disruptions,events or surge information."
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
    handle_parsing_errors=True,
    return_intermediate_steps= False
)

# MAIN FUNCTION

def extract_travel_details(user_query):
    extraction_prompt= f"""
    Extract the following details from the user query:

    - Source City
    - Destination City
    - Start Date (convert to YYYY-MM-DD format. ASSUME YYYY as 2026 if not mentioned explicitly.)
    - End Date (if mentioned,otherwise null)

    Return ONLY valid JSON like:
    {{
        "source":"...",
        "destination":"...",
        "start_date":"YYYY-MM-DD",
        "end_date":"YYYY-MM-DD or null"
    }}

    Query:
    {user_query}
    """

    response= llm.invoke(extraction_prompt)
    text= response.content

    try:
        return json.loads(text.strip())
    except:
        json_match = re.search(r"\{.*?\}",text,re.DOTALL)
        if json_match:
            return json.loads(json_match.group()) # Converts JSON string into Python Dictionary.
        else:
            raise Exception("Could not extract travel details.")

def travel_agent(user_query,budget,priority):
    details=extract_travel_details(user_query)

    source= details["source"]
    destination = details["destination"]
    start_date = details["start_date"]
    end_date = details.get("end_date")
    
    trip_type= "round" if end_date else "oneway"

    query= f"""
    Plan the best travel option.
    "Source": {source},
    "Destination": {destination},
    "Starting Date": {start_date},
    "Trip Type": {trip_type},
    "Return Date": {end_date if end_date else "Not Applicable"},

    "Budget": {budget},
    "Priority": {priority}
    
    If round trip:
    - Consider return journey cost.
    - Calculate total travel cost.

    Important:
    1. Use GetDistance Tool.
    2. Use EstimateTime Tool.
    3. Use EstimateCost tool with input format:
       distance_km,start_date,source,destination,trip_type
    4. Use WebSearch Tool to check:
    - Travel disruptions
    - Event-based surge
    - Weather
    - Strikes
    5. Do NOT EXPLICITLY Mention GetDistance,EstimateTime,EstimateCost,WebSearch in the final output.
    6. Adjust recommendation accordingly.
    7. You MUST strictly use the exact numeric values returned by tools.
    8. Do NOT manually calculate or assume travel time.
    9. DO NOT estimate duration from reasoning.
    10. Use only tool outputs for distance,duration and cost.
    11. Always Mention the Distance in the final output.
    12. Choose best option based on tool results.
    13. Explain clearly.
    """
    response = agent.run(query)

    return response
  