import requests
from datetime import datetime
import os

# FREE GEOCODING USING OPENSTREETMAP

SERPER_API_KEY= os.getenv("SERPER_API_KEY")

def search_with_serper(query):
    """
    Uses Google Serper API to fetch real-time web results.
    Returns top snippets.
    """
    url = "https://google.serper.dev/search"

    headers ={
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    payload={
        "q": query
    }

    response= requests.post(url,json=payload,headers=headers).json()

    snippets =[]

    if "organic" in response:
        for result in response["organic"][:3]:
            snippets.append(result.get("snippet",""))

    return " ".join(snippets) if snippets else "No relevant results found."
 
def geocode_place(place):
    """
    Converts a city/place name into (longitude, latitude)
    using OpenStreetMap Nominatim (FREE, no API key).
    """
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place, # City Name
        "format": "json",   # JSON Response
        "limit": 1  # Only first Result.
    }

    headers = {
        "User-Agent": "travel-ai-agent"  # REQUIRED by Nominatim usage policy
    }

    response = requests.get(url, params=params, headers=headers).json()

    if not response:
        raise Exception(f"Geocoding failed for {place}")

    lon = float(response[0]["lon"])
    lat = float(response[0]["lat"])

    return lon, lat



# FREE ROUTING USING OSRM PUBLIC SERVER

def get_distance(source, destination):
    """
    Returns real-time distance and duration between two places
    using OSRM (Open Source Routing Machine).
    """

    src_lon, src_lat = geocode_place(source)
    dst_lon, dst_lat = geocode_place(destination)

    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{src_lon},{src_lat};{dst_lon},{dst_lat}"
    )

    response = requests.get(url).json()

    if response.get("code") != "Ok":
        raise Exception(f"Routing failed: {response}")

    route = response["routes"][0]

    return {
        "distance_km": route["distance"] / 1000,
        "duration_min": route["duration"] / 60
    }

# MODE-SPECIFIC TIME ESTIMATION

def estimate_time_by_mode(distance_km,duration_min):
    """
    Estimates realistic travel time per mode.
    """

    # Average realistic speeds in India
    bus=42
    train=60
    flight=830

    airport_overhead=50 #minutes

    bus_time= (distance_km/bus)*60
    train_time=  (distance_km/train)*60
    flight_time= (distance_km/flight)*60 + airport_overhead

    return{
        "bus": round(bus_time,1),    # Uses road time
        "train": round(train_time,1),    # Approx 20% faster than bus
        "flight": round(flight_time,1) # Flying speed + airport overhead
    }



# COST ESTIMATION (BUSINESS LOGIC)

def estimate_cost(distance_km,start_date,trip_type="oneway"):
    """
    Dynamically estimates cost based on distance.
    """
    # BUS PRICING
    if distance_km <= 400:
        bus_rate= 2.8
    elif distance_km <= 800:
        bus_rate = 2.4
    else:
        bus_rate= 2.1
    bus_cost= distance_km * bus_rate
    
    # TRAIN PRICING
    if distance_km <= 400:
        train_rate =1.6
    elif distance_km <=800:
        train_rate=1.4
    else:
        train_rate=1.8      # AC class longer routes cost more

    train_cost= distance_km * train_rate

    # FLIGHT PRICING
    if distance_km <= 600:
        flight_rate= 6
        base_fare = 2500
    elif distance_km <= 1200:
        flight_rate= 5.2
        base_fare= 3500
    else:
        flight_rate= 4.8
        base_fare= 4500
    
    flight_cost= max(base_fare,distance_km*flight_rate)

    # Date Based Demand

    travel_date= datetime.strptime(start_date,"%Y-%m-%d")
    today= datetime.today()
    days_until_travel= (travel_date-today).days     # Calculates booking window.

    demand_factor= 1.0

    # Near departure -> Price surge

    if days_until_travel<7:
        demand_factor += 0.25
    elif days_until_travel<15:
        demand_factor += 0.15

    if travel_date.weekday() >= 5:
        demand_factor += 0.10


    if trip_type== "round":
        costs= {mode: price * 2 for mode, price in costs.items()}
    

    return {
        "bus": round(bus_cost*demand_factor,0),
        "train": round(train_cost* demand_factor,0),
        "flight": round(flight_cost* demand_factor,0)
    }

    
    return costs


'''
return {
        "bus": round(distance_km * 1.8,0),
        "train": round(distance_km * 1.5,0),
        "flight": round(max(3000,distance_km * 4.5),0)}
'''        