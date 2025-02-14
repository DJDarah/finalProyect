import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from geopy.distance import geodesic

# Load Data
@st.cache_data
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

landmarks_path = "landmarks_embeddings.json"
municipalities_path = "municipalities_embeddings.json"
landmarks_data = load_json(landmarks_path)
municipalities_data = load_json(municipalities_path)

# Wikipedia Data Extraction
def get_location_data(location_name):
    url = f"https://en.wikipedia.org/wiki/{location_name.replace(' ', '_')}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        summary = "Summary not available."
        for p in paragraphs:
            if "may refer to" not in p.text and len(p.text.strip()) > 30:
                summary = p.text.strip()
                break
        coords = soup.find(class_='geo-dec')
        coordinates = coords.text.strip() if coords else "Coordinates unavailable"
        return {"location": location_name, "coordinates": coordinates, "summary": summary}
    return {"error": "Location not found"}

# Weather API
def find_weather_forecast(date, location):
    API_KEY = "62bb61858baf4e2db7d224858251002"
    url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={location}&days=3"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        forecast = data.get('forecast', {}).get('forecastday', [])[0]
        if forecast:
            return forecast.get('day', {}).get('condition', {}).get('text', 'Unknown')
    return "Weather data not available"

# Streamlit UI
st.title("🌍 Puerto Rico Travel Planner")

# Date Input
travel_date = st.date_input("Select your travel date")

# Interest Selection
categories = ["Beaches", "Nature", "Historical Sites", "Food & Culture", "Festivals & Events"]
selected_interests = st.multiselect("Select your interests", categories)

# Location Suggestions
if st.button("Suggest Locations"):
    suggested_locations = list(landmarks_data.keys())[:10]
    st.write("### Suggested Locations:")
    for loc in suggested_locations:
        st.write(f"- {loc}")

# Ask About Locations
location_query = st.text_input("Ask about a specific location")
if st.button("Get Information") and location_query:
    info = get_location_data(location_query)
    st.json(info)

# Visit List
visit_list = []
if st.button("Lock Locations"):
    for loc in suggested_locations:
        if st.checkbox(f"Lock {loc}"):
            visit_list.append(loc)
    st.write("### Your Locked Visit List:")
    st.write(visit_list)