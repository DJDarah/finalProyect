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
        category = item.get('row', {}).get('Category', 'Other').lower()
        name = item.get('row', {}).get('Name', 'Unknown')
        municipality = item.get('row', {}).get('Municipality', 'Unknown')
        latitude = item.get('row', {}).get('Latitude', 'N/A')
        longitude = item.get('row', {}).get('Longitude', 'N/A')
        description = item.get('row', {}).get('Description', 'N/A')
        
        location_data = {"name": name, "municipality": municipality, "latitude": latitude, "longitude": longitude, "description": description}
        
        if "beach" in category:
            categories["Beaches"].append(location_data)
        elif "nature" in category:
            categories["Nature"].append(location_data)
        elif "historical" in category:
            categories["Historical Sites"].append(location_data)
        elif "food" in category:
            categories["Food & Culture"].append(location_data)
        elif "festival" in category:
            categories["Festivals & Events"].append(location_data)
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

# Obtener información de ubicación
def get_location_data(location_name):
    url = f"https://en.wikipedia.org/wiki/{location_name.replace(' ', '_')}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        summary = "Summary not available."
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            if "may refer to" not in p.text and len(p.text.strip()) > 30:
                summary = p.text.strip()
                break

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
suggested_locations = []
if st.button("Suggest Locations"):
    for interest in selected_interests:
        suggested_locations.extend(location_categories.get(interest, []))
    st.write("### Suggested Locations:")
    for loc in suggested_locations:
        st.write(f"- {loc['name']} ({loc['municipality']})")

# Consultar información de una ubicación
location_query = st.text_input("Ask about a specific location")
if st.button("Get Information") and location_query:
    info = get_location_data(location_query)
    weather = find_weather_forecast(date_selected, location_query)
    st.write("### Location Information:")
    st.json(info)
    st.write("### Weather Forecast:")
    st.write(weather)

# Lista de ubicaciones a visitar
visit_list = []
if st.button("Lock Locations"):
    for loc in suggested_locations:
        if st.checkbox(f"Lock {loc['name']} ({loc['municipality']})"):
            visit_list.append(loc['name'])
    st.write("### Your Locked Visit List:")
    st.write(visit_list)

# Generar itinerario
if st.button("Generate Itinerary") and visit_list:
    itinerary = generate_itinerary(visit_list, date_selected)
    st.write("### Your Travel Itinerary:")
    st.write(itinerary)
