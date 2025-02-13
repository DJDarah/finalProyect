import streamlit as st
import os
import json
import random
import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from nltk.tokenize import sent_tokenize
import nltk

# Descargar nltk tokenizer si es necesario
nltk.download('punkt')

# Configuración de la aplicación
st.set_page_config(page_title="Puerto Rico Travel Assistant", layout="wide")

st.title("🌍 Puerto Rico Travel Assistant")

# Carpetas donde están los TXT de municipios y landmarks
municipalities_folder = r"C:\Users\harid\Downloads\municipalities\municipalities"
landmarks_folder = r"C:\Users\harid\Downloads\landmarks\landmarks"

# Función para limpiar texto y extraer contenido legible
def clean_text(raw_text):
    soup = BeautifulSoup(raw_text, "html.parser")
    text = soup.get_text(separator=" ").strip()
    return " ".join(text.split()[:50])  # Mantiene solo las primeras 50 palabras como resumen

# Función para extraer coordenadas usando Geopy
def get_coordinates(location_name):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(location_name + ", Puerto Rico")
    if location:
        return location.latitude, location.longitude
    return None, None

# Función para procesar archivos TXT en una carpeta
def process_files(folder_path):
    extracted_data = []
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and filename.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as file:
                    raw_content = file.read()
                    cleaned_content = clean_text(raw_content)

                # Extraer coordenadas basadas en el nombre del archivo
                location_name = os.path.splitext(filename)[0]  # Quitar extensión .txt
                latitude, longitude = get_coordinates(location_name)

                extracted_data.append({
                    "name": location_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "summary": cleaned_content
                })
    return extracted_data

# Procesar municipios y landmarks
municipalities = process_files(municipalities_folder)
landmarks = process_files(landmarks_folder)

# Interfaz de usuario en Streamlit
st.sidebar.header("Choose an Option")
option = st.sidebar.selectbox("Select a feature:", ["Chatbot", "Find Weather", "Explore Places"])

if option == "Chatbot":
    st.write("### Ask the Travel Assistant about Puerto Rico!")
    user_query = st.text_input("Enter your question:")

    if "selected_places" not in st.session_state:
        st.session_state.selected_places = []

    def add_place(place):
        if place not in st.session_state.selected_places:
            st.session_state.selected_places.append(place)

    if st.button("Submit"):
        if user_query:
            category = user_query.lower()
            suggestions = []
            
            for place in landmarks + municipalities:
                if category in place["summary"].lower():
                    suggestions.append(place)

            if suggestions:
                st.write("Here are some recommended places:")
                for place in suggestions[:5]:  # Muestra hasta 5 lugares
                    st.write(f"- {place['name']} ({place['latitude']}, {place['longitude']})")
                    st.button(f"Add {place['name']} to visit list", key=f"add_{place['name']}", on_click=add_place, args=(place["name"],))

    st.write("### Your selected places to visit:")
    st.write(" - " + "\n - ".join(st.session_state.selected_places))

elif option == "Find Weather":
    st.write("### Get Weather Forecast")
    location = st.text_input("Enter a location:")
    date = st.date_input("Select a date:")
    if st.button("Get Forecast"):
        API_KEY = "62bb61858baf4e2db7d224858251002"  # Replace with actual API Key
        BASE_URL = "http://api.weatherapi.com/v1/forecast.json"
        params = {"key": API_KEY, "q": location, "dt": date, "days": 1}
        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if "forecast" in data:
                forecast = data["forecast"]["forecastday"][0]["day"]
                weather_info = {
                    "Location": location,
                    "Date": str(date),
                    "Condition": forecast["condition"]["text"],
                    "Max Temp": forecast["maxtemp_c"],
                    "Min Temp": forecast["mintemp_c"],
                    "Humidity": forecast["avghumidity"],
                    "Wind Speed": forecast["maxwind_kph"]
                }
                st.json(weather_info)
            else:
                st.error("Weather data not found.")
        except requests.exceptions.RequestException:
            st.error("API error. Try again later.")

elif option == "Explore Places":
    st.write("### Explore Popular Locations")
    user_interest = st.selectbox("Choose your interest:", ["All"] + [p["name"] for p in landmarks + municipalities])
    if st.button("Find Locations"):
        results = [p for p in landmarks + municipalities if user_interest in p["name"] or user_interest == "All"]
        if results:
            st.write("Here are some great places:")
            for place in results:
                st.write(f"- {place['name']} ({place['latitude']}, {place['longitude']})")
                st.write(f"  {place['summary']}")
        else:
            st.write("No places found for this category.")

