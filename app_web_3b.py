import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime
import os

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

# 2. DISEÑO Y ESTILOS PERSONALIZADOS
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 60px; font-weight: bold; font-size: 20px; border-radius: 15px; background-color: #E30613; color: white; }
    .stButton>button:hover { background-color: #ff1a1a; border: 2px solid white; }
    .main { background-color: #F4F7F6; }
    .pulse { height: 18px; width: 18px; background-color: #2ECC71; border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 12px rgba(46, 204, 113, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); } }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DEL LOGO (Verifica que el archivo esté en GitHub)
logo_path = "logo_3b.png"

# 4. MENÚ LATERAL
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.error("Logo no encontrado en GitHub")
    st.divider()
    menu = st.radio("SISTEMA DE CONTROL", ["📱 REGISTRO EMPLEADO", "🔐 PANEL ADMINISTRADOR"])

# ---------------------------------------------------------
# SECCIÓN 1: PORTAL DEL EMPLEADO (VISTA MÓVIL)
# ---------------------------------------------------------
if menu == "📱 REGISTRO EMPLEADO":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        st.title("Asistencia Las 3B")
        st.write("---")
        
        id_emp = st.text_input("🆔 ID de Empleado", placeholder="Ejemplo: 015")
        
        # Simulación de GPS (En producción aquí va el sensor del navegador)
        lat_gps, lon_gps = 31.320189, -110.943909 
        
        tienda_detectada = None
        for nombre, coords in SUCURSALES.items():
            dist = geodesic((lat_gps, lon_gps), (coords['lat'], coords['lon'])).meters
            if dist <= RADIO_PERMITIDO_METROS:
                tienda_detectada = nombre
                break

        if tienda_detectada:
            st.success(f"✅ UBICACIÓN: Sucursal {tienda_detectada}")
            if st.button("REGISTRAR ENTRADA / SALIDA"):
                if id_emp:
                    st.balloons()
                    hora = datetime.datetime.now().strftime('%I:%M %p')
                    st.success(f"¡Registro Exitoso!\nID: {id_emp}\nHora: {hora}")
                else:
                    st.warning("⚠️ Ingresa tu ID antes de checar.")
        else:
            st.error("❌ FUERA DE RANGO. Debes estar en la sucursal para checar.")

# ---------------------------------------------------------
# SECCIÓN 2: PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif menu == "🔐 PANEL ADMINISTRADOR":
    pass_admin = st.sidebar.text_input("Contraseña Maestro", type="password")
    
    if pass_admin == "3b_admin":
        st.title("⚙️ Administración General - Las 3B")
        
        tab1, tab2, tab3 = st.tabs(["📍 Mapa Real", "👥 Personal", "🗑️ Bajas"])
        
        with tab1:
            st.subheader("Monitoreo de Rutas en Nogales")
            m = folium.Map(location=[31.3050, -110.9300], zoom_start=13)
            for nombre, coords in SUCURSALES.items():
                folium.Circle([coords['lat'], coords['lon']], radius=20, color="#E30613", fill=True, opacity=0.4).add_to(m)
                folium.Marker([coords['lat'], coords['lon']], popup=f"Tienda {nombre}", icon=folium.Icon(color="red", icon="book")).add_to(m)
            
            # Marcador de empleado activo (Ejemplo)
            folium.Marker(
                location=[31.320189, -110.943909],
                icon=folium.DivIcon(html='<div class="pulse"></div>'),
                popup="Empleado: Andrés (En Fusión)"
            ).add_to(m)
            st_folium(m, width="100%", height=450)

        with tab2:
            st.subheader("👥 Gestión de Usuarios")
            with st.form("alta_usuario"):
                c1, c2, c3 = st.columns(3)
                nid = c1.text_input("ID Nuevo")
                nnom = c2.text_input("Nombre Completo")
                npass = c3.text_input("Clave Personal", type="password")
                if st.form_submit_button("Guardar Cambios"):
                    st.success(f"Empleado {nnom} actualizado en el sistema.")
            
            st.divider()
            st.write("### Lista de Empleados")
            df = pd.DataFrame({
                "ID": ["001", "015", "020"],
                "Nombre": ["Juan Pérez", "Andrés M.", "Roberto L."],
                "Estatus": ["Activo", "Activo", "Activo"]
            })
            st.table(df)

        with tab3:
            st.subheader("🗑️ Eliminar Acceso")
            lista = ["Selecciona...", "001 - Juan Pérez", "015 - Andrés M.", "020 - Roberto L."]
            target = st.selectbox("Selecciona a quién dar de baja:", lista)
            if st.button("ELIMINAR DEFINITIVAMENTE", type="secondary"):
                if target != "Selecciona...":
                    st.warning(f"Se ha revocado el acceso a {target}")
                else:
                    st.error("Selecciona un nombre válido.")
    else:
        st.warning("🔒 Acceso Restringido. Ingresa la clave en la barra lateral.")
