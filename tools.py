import requests
from datetime import datetime
import os
import re
import statistics

MAPPLS_API_KEY= os.getenv("MAPPLS_API_KEY")
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

    response= requests.post(url,json=payload,headers=headers,timeout=10)

    if response.status_code != 200:
        return ""
    
    response= response.json()

    snippets =[]

    if "organic" in response:
        for result in response["organic"][:3]:
            snippets.append(result.get("snippet",""))

    return " ".join(snippets) if snippets else "No relevant results found."
 
def get_live_fares(source,destination,start_date):
    """
    Uses Serper search to extract approximate live fares.
    Returns dict of live fares if found.
    """

    if not SERPER_API_KEY:
        return None
    
    try:
        formatted_date= datetime.strptime(start_date,"%Y-%m-%d").strftime("%d %B %Y")
    except:
        formatted_date= start_date


    fares= {}

    modes= ["flight","train","bus"]

    for mode in modes:
        try:
            query= f"{source} to {destination} {mode} ticket price on {formatted_date} in INR"

            search_text = search_with_serper(query)

            # Extract prices from text
            price_matches= re.findall(r"(?:₹|Rs\.?|INR)\s?(\d{3,6})",search_text)

            if price_matches:
                # Take first detected price
                prices= [int(p) for p in price_matches]

                # Remove unrealistic prices
                prices= [p for p in prices if 300 <= p <= 50000]

                if prices:
                    median_price= int(statistics.median(prices))
                    fares[mode]= median_price
        except Exception:
            continue
    return fares if fares else None

def geocode_place(place):
    """
    Converts a city/place name into (longitude, latitude)
    
    Primary : Mappls Geocoding
    Fallback : OpenStreetMap Nominatim (FREE, no API key).
    """
    # MAPPLS Geocoding
    if MAPPLS_API_KEY:
        try:
            url=f"https://apis.mappls.com/advancedmaps/v1/{MAPPLS_API_KEY}/place/geocode"

            params= {
                "address": place
            }

            response= requests.get(url,params=params,timeout=10)

            if response.status_code== 200:
                data= response.json()

                if data.get("copResults") and len(data["copResults"]) > 0:
                    location= data["copResults"][0]


                    lat= float(location["latitude"])
                    lon=float(location["longitude"])
                    

                    return lon,lat
        except Exception as e:
            print("Mappls failed, fallback")
            print(str(e))

             
    
    # OpenStreetMap Nominatim (FREE)

    try:
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
    except Exception as e:
        raise Exception(f"All geocoding providers failed: {str(e)}")



def get_distance(source, destination):
    """
    Returns real-time distance and duration between two places
    Primary : Mappls
    Fallback: OSRM (Open Source Routing Machine).
    """

    # MAPPLS
    try:
        src_lon,src_lat = geocode_place(source)
        dst_lon, dst_lat = geocode_place(destination)
    except Exception as e:
        raise Exception(f"Geocoding failed : {str(e)}")
    
    if MAPPLS_API_KEY:
        try:
            url=f"https://apis.mappls.com/advancedmaps/v1/{MAPPLS_API_KEY}/route"
    
            params={
                "start": f"{src_lat},{src_lon}",
                "end": f"{dst_lat},{dst_lon}",
                "profile": "driving",
                "alternatives":"false"
            }

            response= requests.get(url,params=params, timeout=10)

            print("Mappls Status:", response.status_code)
            print("Mappls Response:",response.text)

            if response.status_code == 200:
                data= response.json()

                if data.get("routes"):
                    route = data["routes"][0]

                    return{
                        "distance_km": route["distance"]/1000,
                        "duration_min":route["duration"]/60,
                        "provider":"Mappls"
                    }
        except Exception as e:
            print("Mappls failed,switching to OSRM fallback")
            print(str(e))
    # OSRM Fallback
    try:
        url = (
            f"https://router.project-osrm.org/route/v1/driving/"
            f"{src_lon},{src_lat};{dst_lon},{dst_lat}"
        )

        response = requests.get(url,timeout=10).json()

        if response.get("code") != "Ok":
            raise Exception(f"Routing failed: {response}")

        route = response["routes"][0]

        return {
            "distance_km": route["distance"] / 1000,
            "duration_min": route["duration"] / 60,
            "provider":"OSRM"
        }
    except Exception as e:
        raise Exception(f"All routing providers failed: {str(e)}")

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

def estimate_cost(distance_km,start_date,trip_type="oneway",source=None,destination=None):
    """
    Dynamically estimates cost based on distance.
    """
    live_fares=None
    if source and destination:
        live_fares= get_live_fares(source,destination,start_date)

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
    try:
        travel_date= datetime.strptime(start_date,"%Y-%m-%d")
    except:
        travel_date= datetime.today()
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

    costs={
        "bus": round(bus_cost*demand_factor,0),
        "train": round(train_cost*demand_factor,0),
        "flight": round(flight_cost*demand_factor,0)
    }
    if live_fares:
        for mode in live_fares:
            costs[mode]= live_fares[mode]

    if trip_type== "round":
        costs= {mode: price * 2 for mode, price in costs.items()}
    
    return costs


'''
return {
        "bus": round(distance_km * 1.8,0),
        "train": round(distance_km * 1.5,0),
        "flight": round(max(3000,distance_km * 4.5),0)}
'''        