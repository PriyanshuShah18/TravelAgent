from langchain_groq import ChatGroq # Groq LLM Wrapper
from tools import get_distance,estimate_cost,estimate_time_by_mode,search_with_serper

from langchain.agents import create_agent
from langchain_core.tools import tool

import traceback      # Debugging

import json     # Parse structured LLM output
import re       # Extract JSON via regex
import os
from langsmith import Client

# Pydantic
from pydantic import BaseModel
from typing import Optional

import logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

from config import get_secret

LANGCHAIN_API_KEY= get_secret("LANGCHAIN_API_KEY")
GROQ_API_KEY= get_secret("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment or secrets.")

if LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_TRACING_V2"]= "true"
    os.environ["LANGCHAIN_PROJECT"]="travel-agent"


llm= ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,        # Deterministic Reasoning        
    groq_api_key=GROQ_API_KEY                #groq_key
)




# DEFINE TOOLS FOR AGENT

# Description is very important as the LLM reads this desc to decide which tool to call.
# This is how tool selection works.
@tool
def get_distance_tool(source: str, destination: str) -> dict:
    """
    Get road distance and duration between two cities.
    Returns distance_km, duration_min, and provider.
    """
    return get_distance(source,destination)

@tool
def estimate_time_tool(distance_km: float) -> dict:
    """
    Estimate travel time in minutes for bus, train, and flight.
    """
    return estimate_time_by_mode(distance_km,0)

@tool
def estimate_cost_tool(
    distance_km: float,
    start_date: str,
    source: str,
    destination: str,
    trip_type: str
) -> dict:
    """
    Estimate travel cost for bus, train and flight.
    """
    return estimate_cost(
        distance_km,
        start_date,
        trip_type=trip_type,
        source=source,
        destination=destination
    )
@tool
def web_search_tool(query: str) -> str:
    """
    Search live travel disruptions, weather, or strike information.
    """
    return search_with_serper(query)

tools=[
    get_distance_tool,
    estimate_time_tool,
    estimate_cost_tool,
    web_search_tool
]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""
You are a travel planning assistant.

Rules:
- Always use tools when numerical data is required.
- Never guess distance,time or cost.
- You MUST NOT modify, invent or compute new Values.
- Always mention distance in final answer.
- Choose best option based on user priority.

After computing everything, explain your reasoning in 2-3 lines.
Do not expose hidden chain-of-thought.

- DO NOT EXPLICITLY MENTION 'TOOL' IN THE OUTPUT.
"""
)

# MEMORY
#memory= ConversationBufferMemory(memory_key="chat_history",return_messages=True)

# MAIN FUNCTION

class TravelDetails(BaseModel):
    source: str
    destination: str
    start_date: str
    end_date: Optional[str] = None

    class Config:
        extra = "forbid"  # Prevents LLM from adding extra keys.

structured_llm= llm.with_structured_output(TravelDetails)

def extract_travel_details(user_query):
    """
    Uses structured output to safely extract travel details.
    No regex.
    No manual JSON parsing.
    Fully schema enforced.
    """
    
    prompt= f"""
Extract the following from the user query.

If year is not mentioned, assume 2026.

User Query:
{user_query}
"""
    try:
        details= structured_llm.invoke(prompt)
        return details.model_dump()  # Returns the same Dictionary Structure.
    except Exception as e:
        raise ValueError(f"Failed to extract structured travel details: {str(e)}")

def travel_agent(user_query,budget,priority):
    details= extract_travel_details(user_query)

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
1. Get Distance
2. Estimate Time
3. Estimate Cost
4. Check:
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
11. If the Budget is Lower than the Cost return Try Searching for Discounts.
11. Always Mention the Distance in the final output.
12. Always mention time in Hours.
13. Choose best option based on tool results.
14. DO NOT EXPLICITLY MENTION THE USE OF 'TOOL' IN THE OUTPUT.
15. Explain clearly.
"""
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": query}
        ]
    })

    return response["messages"][-1].content
