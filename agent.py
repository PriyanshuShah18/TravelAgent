from langchain_groq import ChatGroq
from tools import get_distance,estimate_cost,estimate_time_by_mode
import re


llm= ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0
)

def travel_agent(travel_data):
    source= travel_data["source"]
    destination= travel_data["destination"]
    budget= travel_data["budget"]
    priority=travel_data["priority"]

    # Tool Call
    distance_data= get_distance(source,destination)
    
    distance_km= round(distance_data["distance_km"],2)
    duration_min= round(distance_data["duration_min"],1)

    costs= estimate_cost(distance_km)

    # Mode Specific Time Model

    times= estimate_time_by_mode(distance_km,duration_min)

    options_text=[]

    for mode, cost in costs.items():
        if cost <= budget:
            option_line=(
                f"{mode.capitalize()} | "
                f"Cost: {int(cost)} ₹ | "
                f"Estimated Time: {round(times[mode],1)} minutes"
            )
            options_text.append(option_line)
    if not options_text:
        return "No travel options available within your budget."


    prompt= f"""
    You are a travel planning AI Agent.

    Source : {source}
    Destination : {destination}

    Computed distance between the cities : {distance_km} km.
    Estimated time : {duration_min} minutes.

    Available Travel options:
    {chr(10).join(options_text)}

    User priority: {priority}
    User's Budget : {budget} ₹


    IMPORTANT:
    - Do NOT show internal reasoning.
    - Do NOT include <think> tags.
    - Provide only the final recommendation and explanation.
    - Clearly mention the distance in your explanation.
    """

    response= llm.invoke(prompt)
    response_text= response.content # Extract actual string

    # Extract <think> tags
    think_match= re.search(r"<think>(.*?)</think>",response_text, re.DOTALL)

    if think_match:
        reasoning = think_match.group(1).strip()
        print("\n LLM INTERNAL REASONING")
        print(reasoning)
        print("END REASONING\n")

        clean_response = re.sub(r"<think>.*?</think>","",response_text,flags=re.DOTALL).strip()

    else:
        clean_response= response_text

    return clean_response