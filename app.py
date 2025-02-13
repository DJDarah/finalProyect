import streamlit as st
import os
import json
import requests
import re
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

# Inicializa el geolocalizador con user-agent para evitar errores 403
geolocator = Nominatim(user_agent="geoapiExercises", timeout=10)


# 🔹 Función para limpiar HTML y texto innecesario
def clean_text(text):
    soup = BeautifulSoup(text, "html.parser")
    cleaned_text = soup.get_text()
    cleaned_text = re.sub(r"\n+", " ", cleaned_text)  # Remueve saltos de línea repetidos
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()  # Remueve espacios extra
    return cleaned_text


# 🔹 Función para extraer un resumen sin `nltk`
def extract_summary(text, max_words=25):
    words = text.split()
    return " ".join(words[:max_words]) + "..." if len(words) > max_words else text


# 🔹 Función para obtener coordenadas de un lugar (Evita errores 403)
def get_coordinates(location_name):
    try:
        location = geolocator.geocode(f"{location_name}, Puerto Rico")
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception:
        return None, None


# 🔹 Función para procesar los archivos de municipios y landmarks
def process_files(folder_path):
    extracted_data = []
    if not os.path.exists(folder_path):
        return extracted_data

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                raw_content = file.read()
                cleaned_content = clean_text(raw_content)

            location_name = os.path.splitext(filename)[0]  # Extrae el nombre sin extensión
            latitude, longitude = get_coordinates(location_name)
            summary = extract_summary(cleaned_content)

            extracted_data.append({
                "name": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "summary": summary
            })

    return extracted_data


# 🔹 Cargar los archivos desde la carpeta
municipalities_folder = "municipalities"
landmarks_folder = "landmarks"

municipalities = process_files(municipalities_folder)
landmarks = process_files(landmarks_folder)

# 🔹 Estructura del JSON final
data = {
    "municipalities": municipalities,
    "landmarks": landmarks
}

# 🔹 Guardar los resultados en un JSON
output_file = "processed_data.json"
with open(output_file, "w", encoding="utf-8") as json_file:
    json.dump(data, json_file, indent=4)

# 🔹 INTERFAZ EN STREAMLIT
st.title("Puerto Rico Travel Data")

# Mostrar Municipios
st.header("Municipalities")
for item in municipalities:
    st.write(f"**{item['name']}** - {item['summary']}")
    st.write(f"📍 Lat: {item['latitude']}, Lon: {item['longitude']}")

# Mostrar Landmarks
st.header("Landmarks")
for item in landmarks:
    st.write(f"**{item['name']}** - {item['summary']}")
    st.write(f"📍 Lat: {item['latitude']}, Lon: {item['longitude']}")

st.success(f"Data processed and saved to {output_file} ✅")
