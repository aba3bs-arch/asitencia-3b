import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime

# 1. MANTENER TUS IMPORTACIONES Y CONFIGURACIÓN
try:
    from config import SUCURSALES, RADIO_PERMITIDO_METROS
except:
    # Por si falla el archivo config, que no se detenga la web
    SUCURSALES = {"Fusión": {"lat": 31.320189, "lon": -110.943909}}
    RADIO_PERMITIDO_METROS = 20

st.set_page_config(page_title="Sistema Abarrotes 3B", layout="wide")

# 2. ESTILOS CORREGIDOS (unsafe_allow_html)
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 60px; font-weight: bold; font-size: 20px; }
    .pulse { height: 15px; width: 15px; background-color: #2ECC71; border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); } }
    </style>
    """, unsafe_allow_html=True)

# 3. MENÚ LATERAL
menu = st.sidebar.radio("MENÚ", ["REGISTRO EMPLEADO", "PANEL ADMINISTRADOR"])

if menu == "REGISTRO EMPLEADO":
    st.title("🛒 Control de Asistencia")
    id_emp = st.text_input("Ingresa tu ID de Empleado")
    
    # Aquí iría la lógica del botón de registro que ya tenías...
    st.info("Página de registro activa.")

elif menu == "PANEL ADMINISTRADOR":
    password = st.sidebar.text_input("Contraseña Maestro", type="password")
    
    if password == "3b_admin":
        st.title("⚙️ Administración de Sistema 3B")
        
        # PESTAÑAS
        tab_mapa, tab_usuarios, tab_seguridad = st.tabs(["📍 Mapa en Vivo", "👥 Gestión de Usuarios", "🔐 Seguridad"])
        
        with tab_mapa:
            st.subheader("Monitoreo de Sucursales")
            m = folium.Map(location=[31.3050, -110.9300], zoom_start=13)
            for nombre, coords in SUCURSALES.items():
                folium.Circle([coords['lat'], coords['lon']], radius=20, color="red", fill=True).add_to(m)
                folium.Marker([coords['lat'], coords['lon']], popup=nombre).add_to(m)
            st_folium(m, width="100%", height=400)

        with tab_usuarios:
            st.subheader("Editar Usuarios y Empleados")
            with st.form("nuevo_usuario"):
                col1, col2, col3 = st.columns(3)
                nuevo_id = col1.text_input("ID de Empleado")
                nuevo_nombre = col2.text_input("Nombre Completo")
                nueva_pass = col3.text_input("Contraseña Individual", type="password")
                if st.form_submit_button("Guardar Cambios"):
                    st.success(f"Usuario {nuevo_nombre} actualizado.")
            
            st.write("### Lista de Personal Activo")
            df_usuarios = pd.DataFrame({
                "ID": ["001", "015"],
                "Nombre": ["Juan Pérez", "Andrés M."],
                "Estatus": ["Activo", "Activo"]
            })
            st.dataframe(df_usuarios, use_container_width=True)

        with tab_seguridad:
            st.subheader("Configuración de Acceso")
            st.text_input("Nueva Contraseña Maestro", type="password")
            st.button("Actualizar Llave Maestro")
    else:
        st.warning("🔒 Acceso restringido.")
