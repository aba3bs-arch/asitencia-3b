import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime

# 1. CONFIGURACIÓN DE SUCURSALES (NOGALES)
try:
    from config import SUCURSALES, RADIO_PERMITIDO_METROS
except:
    # Respaldo en caso de que config.py no esté presente
    SUCURSALES = {
        "Fusión": {"lat": 31.320189, "lon": -110.943909},
        "3B7": {"lat": 31.309213, "lon": -110.930617},
        "3B10": {"lat": 31.301250, "lon": -110.937966}
    }
    RADIO_PERMITIDO_METROS = 20

st.set_page_config(page_title="Sistema Abarrotes 3B", layout="wide")

# 2. DISEÑO Y ESTILOS
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 60px; font-weight: bold; font-size: 20px; border-radius: 10px; }
    .main { background-color: #F4F7F6; }
    .pulse { height: 15px; width: 15px; background-color: #2ECC71; border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); } }
    </style>
    """, unsafe_allow_html=True)

# 3. MENÚ LATERAL
st.sidebar.image("https://logodownload.org/wp-content/uploads/2019/07/3b-logo.png", width=100)
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📱 REGISTRO EMPLEADO", "🔐 PANEL ADMINISTRADOR"])

# ---------------------------------------------------------
# SECCIÓN 1: PORTAL DEL EMPLEADO
# ---------------------------------------------------------
if menu == "📱 REGISTRO EMPLEADO":
    st.title("🛒 Control de Asistencia")
    st.write("Bienvenido al sistema de registro de **Abarrotes 3B**.")
    
    id_emp = st.text_input("Ingresa tu ID de Empleado", placeholder="Ej. 015")
    
    # Simulación de ubicación (Esto se conectará al sensor GPS del navegador)
    # Ejemplo: El empleado está en Sucursal Fusión
    lat_gps, lon_gps = 31.320189, -110.943909 
    
    tienda_detectada = None
    distancia_minima = 9999
    
    for nombre, coords in SUCURSALES.items():
        dist = geodesic((lat_gps, lon_gps), (coords['lat'], coords['lon'])).meters
        if dist <= RADIO_PERMITIDO_METROS:
            tienda_detectada = nombre
            distancia_minima = dist
            break

    if tienda_detectada:
        st.success(f"📍 UBICACIÓN CONFIRMADA: Sucursal {tienda_detectada}")
        st.info(f"Distancia a sucursal: {distancia_minima:.2f} metros")
        
        if st.button("REGISTRAR ENTRADA / SALIDA"):
            if id_emp:
                st.balloons()
                st.success(f"¡Hecho! Registro guardado para el ID {id_emp} a las {datetime.datetime.now().strftime('%H:%M:%S')}")
            else:
                st.warning("Por favor ingresa tu ID de empleado antes de registrar.")
    else:
        st.error("❌ FUERA DE RANGO. Debes estar en la tienda para poder checar.")
        st.write("Si crees que es un error, asegúrate de tener el GPS encendido.")

# ---------------------------------------------------------
# SECCIÓN 2: PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif menu == "🔐 PANEL ADMINISTRADOR":
    st.sidebar.divider()
    password = st.sidebar.text_input("Contraseña Maestro", type="password")
    
    if password == "3b_admin":
        st.title("⚙️ Administración General")
        
        tab_mapa, tab_usuarios, tab_seguridad = st.tabs([
            "📍 Monitoreo en Vivo", 
            "👥 Gestión de Personal", 
            "🔑 Seguridad"
        ])
        
        # TAB 1: MAPA
        with tab_mapa:
            st.subheader("Mapa de Sucursales y Personal")
            m = folium.Map(location=[31.3050, -110.9300], zoom_start=13)
            
            for nombre, coords in SUCURSALES.items():
                folium.Circle([coords['lat'], coords['lon']], radius=20, color="red", fill=True, opacity=0.3).add_to(m)
                folium.Marker([coords['lat'], coords['lon']], popup=f"Sucursal: {nombre}", icon=folium.Icon(color="red")).add_to(m)
            
            # Ejemplo de empleado activo en el mapa
            folium.Marker(
                location=[31.320189, -110.943909],
                icon=folium.DivIcon(html='<div class="pulse"></div>'),
                popup="Andrés (Activo en Fusión)"
            ).add_to(m)
            
            st_folium(m, width="100%", height=500)

        # TAB 2: GESTIÓN DE USUARIOS
        with tab_usuarios:
            col_alta, col_baja = st.columns(2)
            
            with col_alta:
                st.write("### ➕ Alta / Editar")
                with st.form("form_alta"):
                    new_id = st.text_input("ID Empleado")
                    new_name = st.text_input("Nombre Completo")
                    new_pass = st.text_input("Contraseña Personal", type="password")
                    if st.form_submit_button("Guardar Empleado"):
                        st.success(f"Empleado {new_name} guardado.")

            with col_baja:
                st.write("### 🗑️ Baja de Personal")
                # Lista de ejemplo
                empleados = ["Selecciona...", "001 - Juan Pérez", "015 - Andrés M.", "020 - Roberto L."]
                target = st.selectbox("Empleado a eliminar:", empleados)
                if st.button("ELIMINAR DEFINITIVAMENTE", type="secondary"):
                    if target != "Selecciona...":
                        st.warning(f"Se ha eliminado a {target}")
                    else:
                        st.error("Selecciona un empleado válido.")

            st.divider()
            st.write("### 📋 Lista de Personal Actual")
            df = pd.DataFrame({
                "ID": ["001", "015", "020"],
                "Nombre": ["Juan Pérez", "Andrés M.", "Roberto L."],
                "Estatus": ["Activo", "Activo", "Activo"]
            })
            st.table(df)

        # TAB 3: SEGURIDAD
        with tab_seguridad:
            st.subheader("Configuración de Acceso Maestro")
            st.text_input("Cambiar Contraseña de Administrador", type="password")
            if st.button("Actualizar Acceso"):
                st.success("La contraseña será actualizada en el próximo reinicio.")

    else:
        st.warning("🔒 Por favor, ingresa la contraseña en la barra lateral para acceder.")
