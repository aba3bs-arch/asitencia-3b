import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime

# IMPORTAMOS TUS SUCURSALES DE NOGALES
from config import SUCURSALES, RADIO_PERMITIDO_METROS

st.set_page_config(page_title="Sistema Abarrotes 3B", layout="wide")

# --- ESTILOS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 60px; font-weight: bold; font-size: 20px; }
    .pulse { height: 15px; width: 15px; background-color: #2ECC71; border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); } }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("MENÚ", ["REGISTRO EMPLEADO", "PANEL ADMINISTRADOR"])

# ---------------------------------------------------------
# SECCIÓN 1: PORTAL DEL EMPLEADO
# ---------------------------------------------------------
if menu == "REGISTRO EMPLEADO":
    st.image("https://logodownload.org/wp-content/uploads/2019/07/3b-logo.png", width=150)
    st.title("Control de Asistencia")
    
    id_emp = st.text_input("Ingresa tu ID de Empleado")
    
    # BOTÓN PARA OBTENER UBICACIÓN (En Web, Streamlit usa JS para esto)
    st.info("Nota: Debes permitir el acceso a tu ubicación en el navegador.")
    
    # SIMULACIÓN DE GPS (En una web real se usa un componente de GPS)
    # Por ahora usaremos 'Fusión' como ejemplo de que el GPS te detectó ahí
    lat_gps, lon_gps = 31.320189, -110.943909 
    
    tienda_detectada = None
    for nombre, coords in SUCURSALES.items():
        dist = geodesic((lat_gps, lon_gps), (coords['lat'], coords['lon'])).meters
        if dist <= RADIO_PERMITIDO_METROS:
            tienda_detectada = nombre
            break

    if tienda_detectada:
        st.success(f"📍 Detectado en: Sucursal {tienda_detectada}")
        if st.button("REGISTRAR ENTRADA/SALIDA"):
            st.balloons()
            st.success(f"Registro exitoso a las {datetime.datetime.now().strftime('%H:%M:%S')}")
            # AQUÍ SE GUARDARÍA EN TU GOOGLE SHEETS O FIREBASE
    else:
        st.error("❌ FUERA DE RANGO. No puedes checar si no estás en la sucursal.")

# ---------------------------------------------------------
# SECCIÓN 2: PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif menu == "PANEL ADMINISTRADOR":
    password = st.sidebar.text_input("Contraseña Admin", type="password")
    if password == "3b_admin": # Cambia tu contraseña aquí
        st.title("📍 Monitoreo Real Abarrotes 3B")
        
        # Mapa
        m = folium.Map(location=[31.3050, -110.9300], zoom_start=13)
        for nombre, coords in SUCURSALES.items():
            folium.Circle([coords['lat'], coords['lon']], radius=20, color="red", fill=True).add_to(m)
            folium.Marker([coords['lat'], coords['lon']], popup=nombre).add_to(m)
        
        # Punto parpadeante del empleado activo
        folium.Marker(
            location=[31.320189, -110.943909],
            icon=folium.DivIcon(html='<div class="pulse"></div>'),
            popup="Empleado: Andrés (En Fusión)"
        ).add_to(m)
        
        st_folium(m, width="100%", height=500)
        
        st.subheader("Historial de Hoy")
        # Aquí cargaríamos los datos de tu Google Sheet
        df = pd.DataFrame({"Empleado": ["Andrés"], "Tienda": ["Fusión"], "Hora": ["19:05 PM"]})
        st.table(df)
    else:
        st.warning("Ingresa la contraseña para ver el mapa.")
