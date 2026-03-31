# AI Travel Recommendation Agent

An intelligent Travel Planner powered by **LangChain**, the **Model Context Protocol (MCP)**, and **Groq LLM (Llama 3)**.

This application allows users to input their travel plans in natural language (e.g., "I want to go from Ahmedabad to Mumbai from 23rd February to 26th February"). It automatically extracts trip details, calculates distances, fetches fares, and determines the best travel option based on the user's constraints (budget vs. time priority).

## Features

* **Natural Language Input**: Automatically parses unstructured travel requests into structured `source`, `destination`, and `dates` using LLM Structured Output.
* **Model Context Protocol (MCP) Server**: Integrates a local MCP server to isolate and execute external tools reliably.
* **Agentic Tool Use**: 
  * **Routing & Distance:** Calculates precise driving distances dynamically using the **Mappls API** (with an open-source OSRM fallback).
  * **Cost Estimation & Live Fares:** Uses the **Serper API** to fetch live real-world ticket prices, and falls back to a custom dynamic pricing algorithm (considering distance, mode, and date-based surges).
  *  **Time Estimation:** Realistically estimates trip duration for Flights, Trains, and Buses.
  * **Web Search:** Checks for real-time travel disruptions, weather issues, or event-based surges.
* **Smart Decision Making**: The Llama 3 Agent evaluates all calculated factors (Cost, Duration, Disruptions) against the user's defined strict budget and prioritizes the response accordingly.

## Architecture

* **Frontend**: Streamlit
* **LLM**: Groq (`llama-3.3-70b-versatile`)
* **Orchestrator**: LangChain (Agents & MultiServerMCPClient)
* **Tooling Protocol**: FastMCP (STDIO transport)
* **External APIs**: Mappls (Geocoding/Routing), Serper (Google Search)

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/travel-agent.git
   cd travel-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables**
   Create a `.env` file in the root directory and add the following API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   LANGCHAIN_API_KEY=your_langchain_api_key_here
   MAPPLS_API_KEY=your_mappls_api_key_here
   SERPER_API_KEY=your_serper_dev_api_key_here
   ```
   *(Alternatively, you can manage these via Streamlit's `secrets.toml`)*

## Usage

Start the Streamlit web application:

```bash
streamlit run app.py
```

The app will launch at `http://localhost:8501`. 
1. Enter your travel query.
2. Set your maximum Budget (in INR).
3. Select your Priority (Time or Budget).
4. Click **Get Recommendation** and let the AI find the optimal travel plan!

## How It Works

1. `app.py` receives the user request and passes it to the generic `travel_agent()`.
2. `agent.py` establishes a `MultiServerMCPClient` connected natively via `stdio` to the MCP Server (`mcp_server.py`).
3. The prompt is validated and converted into structured details.
4. The LangChain agent utilizes the exposed MCP tools (`get_distance_tool`, `estimate_cost_tool`, `estimate_time_tool`, `web_search_tool`) autonomously.
5. The LLM processes the returned numerical constraints and outputs a user-friendly recommendation heavily anchored in actual tool results.
