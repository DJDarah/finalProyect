import streamlit as st
import json
import random
import requests
from bs4 import BeautifulSoup
from geopy.distance import geodesic
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings

# Load the embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Sample data for Puerto Rico landmarks
landmarks = {
    "beach": ["Flamenco Beach", "Playa Buyé", "Crash Boat Beach"],
    "history": ["El Morro", "San Cristóbal Fort", "Casa Blanca Museum"],
    "nature": ["El Yunque National Forest", "Cueva Ventana", "Toro Verde Adventure Park"],
    "culture": ["Paseo de la Princesa", "La Placita de Santurce", "Ponce Museum of Art"]
}

st.set_page_config(page_title="Puerto Rico Travel Assistant", layout="wide")

st.title("🌍 Puerto Rico Travel Assistant")

st.sidebar.header("Choose an Option")
option = st.sidebar.selectbox("Select a feature:", ["Chatbot", "Find Weather", "Explore Places"])

if option == "Chatbot":
    st.write("### Ask the Travel Assistant about Puerto Rico!")
    user_query = st.text_input("Enter your question:")

    # Inicializar la variable de sesión para almacenar lugares seleccionados solo si no existe
    if "selected_places" not in st.session_state:
        st.session_state.selected_places = []

    # Función para agregar lugares sin perder el estado
    def add_place(place):
        if place not in st.session_state.selected_places:
            st.session_state.selected_places.append(place)

    if st.button("Submit"):
        if user_query:
            category = user_query.lower()
            if category in landmarks:
                suggestions = random.sample(landmarks[category], min(2, len(landmarks[category])))

                st.write(f"Here are some recommended places for {category}:")
                
                # Mostrar botones correctamente con callbacks
                for place in suggestions:
                    st.button(f"Add {place} to visit list", key=f"add_{place}", on_click=add_place, args=(place,))

    # Mostrar la lista de lugares seleccionados SIEMPRE
    st.write("### Your selected places to visit:")
    st.write(st.session_state.selected_places)



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
    user_interest = st.selectbox("Choose your interest:", list(landmarks.keys()))
    if st.button("Find Locations"):
        results = landmarks.get(user_interest, [])
        if results:
            st.write(f"Here are some great places for {user_interest}:")
            for place in results:
                st.write(f"- {place}")
        else:
            st.write("No places found for this category.")
