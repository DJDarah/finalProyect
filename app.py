import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import openai
from datetime import datetime

# 📌 Obtener API Keys desde Streamlit Secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
WEATHER_API_KEY = st.secrets["WEATHER_API_KEY"]

# Inicializar cliente OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Load Data
@st.cache_data
def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

landmarks_path = "landmarks_embeddings.json"
municipalities_path = "municipalities_embeddings.json"
landmarks_data = load_json(landmarks_path)
municipalities_data = load_json(municipalities_path)

# Categorizar ubicaciones
def categorize_locations(data):
    categories = {"Beaches": [], "Nature": [], "Historical Sites": [], "Food & Culture": [], "Festivals & Events": []}
    for item in data.values():
        category = item.get('row', {}).get('Category', 'Other')
        name = item.get('row', {}).get('Name', 'Unknown')
        municipality = item.get('row', {}).get('Municipality', 'Unknown')
        if "beach" in category.lower():
            categories["Beaches"].append(f"{name} ({municipality})")
        elif "nature" in category.lower():
            categories["Nature"].append(f"{name} ({municipality})")
        elif "historical" in category.lower():
            categories["Historical Sites"].append(f"{name} ({municipality})")
        elif "food" in category.lower():
            categories["Food & Culture"].append(f"{name} ({municipality})")
        elif "festival" in category.lower():
            categories["Festivals & Events"].append(f"{name} ({municipality})")
    return categories

location_categories = categorize_locations(landmarks_data)

# Obtener información del clima
def find_weather_forecast(date, location):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={location}&days=3"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        forecast = data.get('forecast', {}).get('forecastday', [])[0]
        if forecast:
            return forecast.get('day', {}).get('condition', {}).get('text', 'Unknown')
    return "Weather data not available"

# Generar respuestas con OpenAI
def generate_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a travel planner for Puerto Rico."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Generar itinerario con OpenAI
def generate_itinerary(visit_list, travel_date):
    prompt = f"Generate a travel itinerary for the following locations in Puerto Rico on {travel_date}: {', '.join(visit_list)}. Include recommendations for food, activities, and travel tips."
    return generate_response(prompt)

# Streamlit UI
st.title("🌍 Puerto Rico Travel Planner")

# Selección de fecha
date_selected = st.date_input("Select your travel date", datetime.today())

# Selección de intereses
selected_interests = st.multiselect("Select your interests", list(location_categories.keys()))

# Sugerencia de ubicaciones
if st.button("Suggest Locations"):
    suggested_locations = []
    for interest in selected_interests:
        suggested_locations.extend(location_categories.get(interest, []))
    st.write("### Suggested Locations:")
    for loc in suggested_locations:
        st.write(f"- {loc}")

# Consultar información de una ubicación
location_query = st.text_input("Ask about a specific location")
if st.button("Get Information") and location_query:
    info = generate_response(f"Provide detailed travel information about {location_query} in Puerto Rico.")
    weather = find_weather_forecast(date_selected, location_query)
    st.write("### Location Information:")
    st.write(info)
    st.write("### Weather Forecast:")
    st.write(weather)

# Lista de ubicaciones a visitar
visit_list = []
if st.button("Lock Locations"):
    for loc in suggested_locations:
        if st.checkbox(f"Lock {loc}"):
            visit_list.append(loc)
    st.write("### Your Locked Visit List:")
    st.write(visit_list)

# Generar itinerario
if st.button("Generate Itinerary") and visit_list:
    itinerary = generate_itinerary(visit_list, date_selected)
    st.write("### Your Travel Itinerary:")
    st.write(itinerary)
