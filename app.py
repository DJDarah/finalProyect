import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import openai
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

# 📌 Cargar claves API desde GitHub Secrets o entorno local
load_dotenv(find_dotenv())  # Carga las claves desde .env si existe
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
openai.api_key = OPENAI_API_KEY

# Load Data
@st.cache_data
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

landmarks_path = "landmarks_embeddings.json"
municipalities_path = "municipalities_embeddings.json"
landmarks_data = load_json(landmarks_path)
municipalities_data = load_json(municipalities_path)

# Wikipedia Data Extraction (Improved)
def get_location_data(location_name):
    url = f"https://en.wikipedia.org/wiki/{location_name.replace(' ', '_')}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get first valid summary paragraph (avoiding disambiguation)
        summary = "Summary not available."
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            if "may refer to" not in p.text and len(p.text.strip()) > 30:
                summary = p.text.strip()
                break

        # Get coordinates from Wikipedia infobox (more reliable than geo-dec class)
        coordinates = "Coordinates unavailable"
        infobox = soup.find(class_="infobox")
        if infobox:
            for row in infobox.find_all("tr"):
                if "Coordinates" in row.text:
                    coord_tag = row.find("span", class_="geo-dec")
                    if coord_tag:
                        coordinates = coord_tag.text.strip()
                    break
        
        return {"location": location_name, "coordinates": coordinates, "summary": summary}
    
    return {"error": "Location not found"}

# Weather API
def find_weather_forecast(date, location):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={location}&days=3"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        forecast = data.get('forecast', {}).get('forecastday', [])[0]
        if forecast:
            return forecast.get('day', {}).get('condition', {}).get('text', 'Unknown')
    return "Weather data not available"

# Generate Itinerary using OpenAI
def generate_itinerary(visit_list, travel_date):
    prompt = f"Generate a travel itinerary for the following locations in Puerto Rico on {travel_date}: {', '.join(visit_list)}. Include recommendations for food, activities, and travel tips."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a travel planner for Puerto Rico."},
                  {"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

# Streamlit UI
st.title("🌍 Puerto Rico Travel Planner")

# Date Input
travel_date = st.date_input("Select your travel date", datetime.today())

# Interest Selection
categories = ["Beaches", "Nature", "Historical Sites", "Food & Culture", "Festivals & Events"]
selected_interests = st.multiselect("Select your interests", categories)

# Location Suggestions
if st.button("Suggest Locations"):
    suggested_locations = [item.get("row", {}).get("Name", "Unknown") for item in landmarks_data.values()][:10]
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

# Generate Itinerary
if st.button("Generate Itinerary") and visit_list:
    itinerary = generate_itinerary(visit_list, travel_date)
    st.write("### Your Travel Itinerary:")
    st.write(itinerary)
