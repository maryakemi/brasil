import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from streamlit_folium import folium_static
from time import sleep

st.set_page_config(page_title="Mapa de Inmuebles", layout="wide")

st.title("🏠 Mapa de Inmuebles con Ahorro")

# Subir archivo
archivo_cargado = st.file_uploader("📤 Sube tu archivo CSV de inmuebles", type=["csv"])

if archivo_cargado is not None:
    archivo = pd.read_csv(archivo_cargado, encoding='latin1', sep=';')

    # Limpieza y renombre
    columnas_a_eliminar = ['Descrição', ' N° do imóvel', 'Valor de avaliação', 'Modalidade de venda']
    archivo.drop(columns=[col for col in columnas_a_eliminar if col in archivo.columns], inplace=True)

    archivo = archivo.rename(columns={
        'Endereço': 'Endereco',
        'Bairro': 'Bairro',
        'Cidade': 'Cidade',
        'UF': 'UF',
        'Preço': 'Precio',
        'Desconto': 'Porcentaje de ahorro',
        'Link de acceso': 'Enlace'
    })

    archivo["Direccion"] = archivo['Endereco'] + ', ' + archivo['Bairro'] + ', ' + archivo['Cidade'] + ' - ' + archivo['UF'] + ', Brasil'

    # Eliminar columnas no necesarias
    archivo.drop(columns=['Endereco', 'Bairro', 'Cidade', 'UF'], inplace=True)
    archivo.dropna(inplace=True)

    # Convertir precio a numérico
    archivo["Precio"] = (
        archivo["Precio"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    archivo["Precio"] = pd.to_numeric(archivo["Precio"], errors="coerce")

    # Filtrar por porcentaje de ahorro
    ahorro_min = st.slider("📉 Porcentaje mínimo de ahorro", 0, 100, 30)
    archivo = archivo[archivo['Porcentaje de ahorro'] >= ahorro_min]

    # Geocodificación
    st.info("🔍 Geocodificando direcciones, por favor espera...")

    geolocator = Nominatim(user_agent="app_mapa_inmuebles")
    latitudes = []
    longitudes = []

    for i, direccion in enumerate(archivo["Direccion"], start=1):
        location = None
        try:
            location = geolocator.geocode(direccion)
            sleep(1)
        except:
            pass

        if not location:
            try:
                partes = direccion.split(",")
                if len(partes) >= 3:
                    direccion_simple = partes[-3].strip() + ", " + partes[-2].strip() + ", Brasil"
                    location = geolocator.geocode(direccion_simple)
                    sleep(1)
            except:
                pass

        if location:
            latitudes.append(location.latitude)
            longitudes.append(location.longitude)
        else:
            latitudes.append(None)
            longitudes.append(None)

    archivo["Latitud"] = latitudes
    archivo["Longitud"] = longitudes
    archivo.dropna(subset=["Latitud", "Longitud"], inplace=True)

    # Mapa con Folium
    st.subheader("🗺️ Mapa de propiedades geolocalizadas")
    if not archivo.empty:
        mapa = folium.Map(location=[archivo["Latitud"].mean(), archivo["Longitud"].mean()], zoom_start=11)
        marker_cluster = MarkerCluster().add_to(mapa)

        for _, row in archivo.iterrows():
            popup = folium.Popup(
                f"<b>Dirección:</b> {row['Direccion']}<br>"
                f"<b>Precio:</b> €{row['Precio']:,.2f}<br>"
                f"<b>Ahorro:</b> {row['Porcentaje de ahorro']}%<br>"
                f"<a href='{row['Enlace']}' target='_blank'>Ver propiedad</a>",
                max_width=300
            )
            folium.Marker(
                location=[row["Latitud"], row["Longitud"]],
                popup=popup,
                icon=folium.Icon(color="blue", icon="home")
            ).add_to(marker_cluster)

        folium_static(mapa)

        st.success(f"✅ Total propiedades mostradas: {len(archivo)}")
    else:
        st.warning("⚠️ No se encontraron propiedades geolocalizadas.")
