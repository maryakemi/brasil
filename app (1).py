
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from time import sleep
from io import BytesIO

st.set_page_config(page_title="Mapa de Inmuebles", layout="wide")

# Subir archivo Excel
archivo = pd.read_csv('Lista_imoveis_SP.csv', encoding='latin1', sep=';')
archivo.drop('Descrição', axis=1, inplace=True)
archivo.drop(' N° do imóvel', axis=1, inplace=True)
archivo.drop('Valor de avaliação', axis=1, inplace=True)
archivo = archivo.rename(columns={
    'Endereço': 'Endereco',
    'Bairro': 'Bairro',
    'Cidade': 'Cidade',
    'UF': 'UF',
    'Preço': 'Precio',
    'Desconto': 'Porcentaje de ahorro',
    'Link de acesso': 'Enlace'})

# Crear columna de dirección completa
archivo['Direccion'] = archivo['Endereco'] + ', ' + archivo['Bairro'] + ', ' + archivo['Cidade'] + ' - ' + archivo['UF'] + ', Brasil'

archivo.drop('UF', axis=1, inplace=True)
archivo.drop('Cidade', axis=1, inplace=True)
archivo.drop('Bairro', axis=1, inplace=True)
archivo.drop('Endereco', axis=1, inplace=True)
archivo.drop('Modalidade de venda', axis=1, inplace=True)
archivo.dropna(inplace=True)
# archivo.to_excel('imoveis_RJ_limpio.xlsx', index=False)

archivo["Precio"] = archivo["Precio"].astype(str)  # aseguramos que sea string
archivo["Precio"] = (
    archivo["Precio"]
    .str.replace(".", "", regex=False)        # quita puntos miles
    .str.replace(",", ".", regex=False)       # cambia coma decimal a punto
)
# Convertimos ya limpio a numérico
archivo["Precio"] = pd.to_numeric(archivo["Precio"], errors="coerce")
archivo = archivo[archivo['Porcentaje de ahorro'] >= 30]
print(f"Número de propiedades después del filtrado: {len(archivo)}")



# Verificar columnas
columnas_esperadas = {"Direccion", "Precio", "Enlace", "Porcentaje de ahorro"}
if not columnas_esperadas.issubset(archivo.columns):
    raise ValueError("❌ El archivo debe tener las columnas: Direccion, Precio, Enlace, Porcentaje de ahorro")

# --- Filtros definidos por el usuario ---
# precio_max = 1000000  # Puedes cambiar esto
# ahorro_min = 40        # Puedes cambiar esto
#
# archivo[
#     (archivo['Precio'] <= precio_max) &
#     (archivo['Porcentaje de ahorro'] >= ahorro_min)
# ]

# --- Geocodificación mejorada ---
geolocator = Nominatim(user_agent="app_mapa_inmuebles")
latitudes = []
longitudes = []

total = len(archivo)
for i, direccion in enumerate(archivo["Direccion"], start=1):
    print(f"🔄 Geocodificando ({i}/{total}): {direccion[:50]}...")
    location = None

    # Intento 1: dirección completa
    try:
        location = geolocator.geocode(direccion)
        sleep(1)
    except:
        pass

    # Intento 2: parte simplificada
    if not location:
        try:
            partes = direccion.split(",")
            if len(partes) >= 3:
                direccion_simplificada = partes[-3].strip() + ", " + partes[-2].strip() + ", Brasil"
                location = geolocator.geocode(direccion_simplificada)
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

# --- Crear el mapa ---
if not archivo.empty:
    lat_init = archivo["Latitud"].iloc[0]
    lon_init = archivo["Longitud"].iloc[0]
    mapa = folium.Map(location=[lat_init, lon_init], zoom_start=12)

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
        ).add_to(mapa)

    # Guardar HTML
    mapa.save(f"mapa_inmuebles{total}.html")
    print("✅ Mapa guardado como 'mapa_inmuebles.html'.")

    no_geolocalizadas = sum(pd.isna(latitudes))  # o longitudes, es igual
    print(f"\n🔚 Proceso finalizado.")
    print(f"📍 Direcciones totales: {total}")
    print(f"✅ Georreferenciadas: {total - no_geolocalizadas}")
    print(f"❌ No georreferenciadas: {no_geolocalizadas}")
else:
    print("⚠️ No se encontraron direcciones válidas.")