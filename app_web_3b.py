import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime
import os
from streamlit_js_eval import get_geolocation

# 1. CONFIGURACIÓN DE SUCURSALES (NOGALES)
try:
    from config import SUCURSALES, RADIO_PERMITIDO_METROS
except:
    SUCURSALES = {
        "Fusión": {"lat": 31.320189, "lon": -110.943909},
        "3B7": {"lat": 31.309213, "lon": -110.930617},
        "3B10": {"lat": 31.301250, "lon": -110.937966}
    }
    RADIO_PERMITIDO_METROS = 20

st.set_page_config(page_title="Abarrotes Las 3B", layout="wide", page_icon="📖")

# 2. ESTILOS
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 60px; font-weight: bold; font-size: 20px; border-radius: 15px; background-color: #E30613; color: white; }
    .pulse { height: 18px; width: 18px; background-color: #2ECC71; border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 12px rgba(46, 204, 113, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); } }
    </style>
    """, unsafe_allow_html=True)

# 3. LOGO Y MENÚ LATERAL (Aquí definimos 'menu')
logo_path = "logo_3b.png"

with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.divider()
    menu = st.radio("SISTEMA DE CONTROL", ["📱 REGISTRO EMPLEADO", "🔐 PANEL ADMINISTRADOR"])

# ---------------------------------------------------------
# SECCIÓN 1: PORTAL DEL EMPLEADO (GPS REAL)
# ---------------------------------------------------------
if menu == "📱 REGISTRO EMPLEADO":
    st.title("Asistencia Las 3B")
    id_emp = st.text_input("🆔 ID de Empleado", placeholder="Ejemplo: 015")
    
    # OBTENER UBICACIÓN REAL DESDE EL NAVEGADOR
    loc = get_geolocation()
    
    if loc:
        lat_gps = loc['coords']['latitude']
        lon_gps = loc['coords']['longitude']
        
        tienda_detectada = None
        for nombre, coords in SUCURSALES.items():
            dist = geodesic((lat_gps, lon_gps), (coords['lat'], coords['lon'])).meters
            if dist <= RADIO_PERMITIDO_METROS:
                tienda_detectada = nombre
                break

        if tienda_detectada:
            st.success(f"✅ UBICACIÓN CONFIRMADA: Sucursal {tienda_detectada}")
            if st.button("REGISTRAR ENTRADA / SALIDA"):
                if id_emp:
                    st.balloons()
                    st.success(f"¡Registro Guardado para ID {id_emp}!")
                else:
                    st.warning("⚠️ Ingresa tu ID antes de checar.")
        else:
            st.error("❌ FUERA DE RANGO. No estás en ninguna sucursal.")
    else:
        st.warning("📡 Buscando señal de GPS... Por favor, permite el acceso a tu ubicación en el celular.")

# ---------------------------------------------------------
# SECCIÓN 2: PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif menu == "🔐 PANEL ADMINISTRADOR":
    pass_admin = st.sidebar.text_input("Contraseña Maestro", type="password")
    
    if pass_admin == "3b_admin":
        st.title("⚙️ Administración Las 3B")
        tab1, tab2, tab3 = st.tabs(["📍 Mapa Real", "👥 Personal", "🗑️ Bajas"])
        
        with tab1:
            m = folium.Map(location=[31.3050, -110.9300], zoom_start=13)
            for nombre, coords in SUCURSALES.items():
                folium.Marker([coords['lat'], coords['lon']], popup=nombre, icon=folium.Icon(color="red", icon="book")).add_to(m)
            st_folium(m, width="100%", height=450)

        with tab2:
            st.subheader("Gestión de Usuarios")
            with st.form("alta"):
                c1, c2 = st.columns(2)
                nid = c1.text_input("ID")
                nnom = c2.text_input("Nombre")
                if st.form_submit_button("Guardar"):
                    st.success("Empleado guardado.")

        with tab3:
            st.subheader("Dar de Baja")
            target = st.selectbox("Selecciona:", ["Selecciona...", "Empleado Ejemplo"])
            if st.button("ELIMINAR"):
                st.warning("Acción realizada.")
    else:
        st.warning("🔒 Ingresa la contraseña en la barra lateral.")
