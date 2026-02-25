from mcp.server.fastmcp import FastMCP
from config import get_secret

from tools import(
    get_distance,
    estimate_cost,
    estimate_time_by_mode,
    search_with_serper
)

mcp= FastMCP("travel-agent")

# Register Tools

@mcp.tool()
def get_distance_tool(source:str,destination:str):
    """
    Return distance and duration between two cities.
    """
    return get_distance(source,destination)

@mcp.tool()
def estimate_cost_tool(
    distance_km:float,
    start_date: str,
    source: str,
    destination: str,
    trip_type: str
):
    """
    Estimate total travel cost for bus,train and flight.
    """
    return estimate_cost(
        distance_km,
        start_date,
        trip_type=trip_type,
        source=source,
        destination=destination
    )

@mcp.tool()
def estimate_time_tool(distance_km:float):
    """
    Estimate travel time per transport mode.
    """
    return estimate_time_by_mode(distance_km,0)

@mcp.tool()
def web_search_tool(query:str):
    """
    Search for live travel disruptions or events.
    """
    return search_with_serper(query)

# Run MCP Server

if __name__ == "__main__":
    print("Starting MCP Server...")
    mcp.run()

