import streamlit as st
import os
import openai
import requests
import json
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from bs4 import BeautifulSoup
from datetime import datetime

# Cargar API Keys desde variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Definir modelo optimizado
LLM_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"

# Directorio de datos
BASE_DATA_DIR = "data"
LANDMARK_DIR = os.path.join(BASE_DATA_DIR, "landmarks")
MUNICIPALITIES_DIR = os.path.join(BASE_DATA_DIR, "municipalities")

# Cargar y limpiar textos de múltiples directorios
def load_cleaned_texts(directories, max_files=30):
    texts = []
    for directory in directories:
        if not os.path.exists(directory):
            continue
        files = sorted(os.listdir(directory))[:max_files]
        for filename in files:
            with open(os.path.join(directory, filename), "r", encoding="utf-8") as file:
                raw_html = file.read()
                soup = BeautifulSoup(raw_html, "html.parser")
                text = soup.get_text(separator=" ").strip()
                cleaned_text = " ".join(text.split())
                texts.append(cleaned_text)
    return texts

# Cargar datos
landmarks = load_cleaned_texts([LANDMARK_DIR, MUNICIPALITIES_DIR])

# Cargar datos solo si el índice no existe
VECTOR_DB_PATH = "vector_store/faiss_index"

def get_vector_store():
    if os.path.exists(VECTOR_DB_PATH):
        return FAISS.load_local(VECTOR_DB_PATH, OpenAIEmbeddings(model=EMBEDDING_MODEL))
    else:
        if not landmarks:
            st.error("No landmark or municipality data found. Please check your data directory.")
            st.stop()
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        vector_store = FAISS.from_texts(landmarks, embeddings)
        vector_store.save_local(VECTOR_DB_PATH)
        return vector_store

vector_store = get_vector_store()
retriever = vector_store.as_retriever()

# Definir prompt para el chatbot
prompt_template = PromptTemplate(
    template="""
    You are a travel assistant specialized in Puerto Rico tourism.
    The user wants to visit places for {days} days.
    Suggest a detailed itinerary based on available landmarks and municipalities.
    
    Based on the following information:
    {context}
    
    Question: {query}
    """,
    input_variables=["days", "query", "context"]
)

# Crear la cadena de consulta con RetrievalQA
qa_chain = RetrievalQA(retriever=retriever)

# Obtener datos del clima
def get_weather(location):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={location}&days=3"
    response = requests.get(url)
    if response.status_code == 200:
        weather = response.json()
        forecast = weather.get("forecast", {}).get("forecastday", [])[0]
        if forecast:
            return {
                "location": weather.get("location", {}).get("name", "Unknown"),
                "temperature": forecast.get("day", {}).get("avgtemp_c", "N/A"),
                "condition": forecast.get("day", {}).get("condition", {}).get("text", "N/A"),
                "humidity": forecast.get("day", {}).get("avghumidity", "N/A"),
                "wind": forecast.get("day", {}).get("maxwind_kph", "N/A")
            }
    return {"error": "Could not fetch weather data."}

# Obtener coordenadas desde JSON
def get_coordinates(location):
    for directory in [LANDMARK_DIR, MUNICIPALITIES_DIR]:
        if not os.path.exists(directory):
            continue
        files = os.listdir(directory)
        for filename in files:
            with open(os.path.join(directory, filename), "r", encoding="utf-8") as file:
                data = json.load(file)
                for item in data:
                    name = item.get("row", {}).get("Name", "").lower()
                    if name == location.lower():
                        return {
                            "latitude": item.get("row", {}).get("Latitude", "N/A"),
                            "longitude": item.get("row", {}).get("Longitude", "N/A")
                        }
    return {"latitude": "N/A", "longitude": "N/A"}

# Interfaz con Streamlit
st.title("Puerto Rico Travel Planner")

# Entrada del usuario
days = st.number_input("How many days will you travel?", min_value=1, max_value=30, step=1)
interest = st.text_input("Enter your travel interest (e.g., beaches, history, hiking):")

if st.button("Get Itinerary"):
    query = f"I am interested in {interest} and have {days} days."
    itinerary = qa_chain.invoke({"query": query, "days": days})
    
    if "result" in itinerary:
        st.write("### Suggested Itinerary:")
        st.write(itinerary["result"])
        
        st.write("### Weather Forecast:")
        locations = itinerary["result"].split("\n")
        weather_reports = {loc: get_weather(loc) for loc in locations if loc.strip()}
        st.json(weather_reports)
        
        st.write("### Coordinates:")
        coordinates_reports = {loc: get_coordinates(loc) for loc in locations if loc.strip()}
        st.json(coordinates_reports)

    else:
        st.error("No itinerary could be generated. Please try again with different inputs.")
