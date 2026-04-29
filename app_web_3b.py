import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime
import os
from streamlit_js_eval import get_geolocation
from library.st_gsheets_connection import GSheetsConnection

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Abarrotes Las 3B", layout="wide", page_icon="📖")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Cargar sucursales desde Google Sheets en lugar de código fijo
try:
    df_sucursales = conn.read(worksheet="Sucursales")
    SUCURSALES_DICT = {row['Nombre']: {'lat': row['Latitud'], 'lon': row['Longitud']} for _, row in df_sucursales.iterrows()}
except:
    # Si la hoja está vacía, ponemos una por defecto para que no truene
    SUCURSALES_DICT = {"Fusión": {"lat": 31.320189, "lon": -110.943909}}

RADIO_PERMITIDO_METROS = 30 # Aumenté un poco el margen para el GPS

# 2. ESTILOS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .btn-registro { height: 60px; font-size: 20px; background-color: #E30613; color: white; }
    .pulse { height: 18px; width: 18px; background-color: #2ECC71; border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 12px rgba(46, 204, 113, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); } }
    </style>
    """, unsafe_allow_html=True)

# 3. LOGO Y MENÚ
logo_path = "logo_3b.png"
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.divider()
    menu = st.radio("SISTEMA DE CONTROL", ["📱 REGISTRO EMPLEADO", "🔐 PANEL ADMINISTRADOR"])

# ---------------------------------------------------------
# SECCIÓN 1: PORTAL DEL EMPLEADO
# ---------------------------------------------------------
if menu == "📱 REGISTRO EMPLEADO":
    st.title("Asistencia Las 3B")
    id_emp = st.text_input("🆔 ID de Empleado", placeholder="Ej. 015")
    loc = get_geolocation()
    
    if loc:
        lat_gps, lon_gps = loc['coords']['latitude'], loc['coords']['longitude']
        tienda_actual = next((n for n, c in SUCURSALES_DICT.items() if geodesic((lat_gps, lon_gps), (c['lat'], c['lon'])).meters <= RADIO_PERMITIDO_METROS), None)

        if tienda_actual:
            st.success(f"📍 Detectado en: {tienda_actual}")
            if st.button("REGISTRAR ENTRADA / SALIDA"):
                if id_emp:
                    now = datetime.datetime.now()
                    nuevo_reg = pd.DataFrame([{"Fecha": now.strftime("%Y-%m-%d"), "Hora": now.strftime("%H:%M:%S"), "ID": id_emp, "Tienda": tienda_actual}])
                    df_r = conn.read(worksheet="Registros")
                    conn.update(worksheet="Registros", data=pd.concat([df_r, nuevo_reg], ignore_index=True))
                    st.balloons(); st.success("✅ Registro guardado.")
                else: st.warning("⚠️ Ingresa tu ID.")
        else: st.error("❌ FUERA DE RANGO. No estás cerca de ninguna sucursal registrada.")
    else: st.warning("📡 Buscando GPS... Activa tu ubicación.")

# ---------------------------------------------------------
# SECCIÓN 2: PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif menu == "🔐 PANEL ADMINISTRADOR":
    if st.sidebar.text_input("Contraseña Maestro", type="password") == "3b_admin":
        st.title("⚙️ Administración General")
        tab_mapa, tab_personal, tab_tiendas = st.tabs(["📍 Mapa", "👥 Personal", "🏪 Sucursales"])

        with tab_mapa:
            m = folium.Map(location=[31.3050, -110.9300], zoom_start=13)
            for n, c in SUCURSALES_DICT.items():
                folium.Marker([c['lat'], c['lon']], popup=n, icon=folium.Icon(color="red", icon="shopping-cart")).add_to(m)
            st_folium(m, width="100%", height=400)

        with tab_personal:
            st.subheader("Gestión de Empleados")
            # (Aquí va la lógica de agregar/eliminar empleados que ya teníamos)
            df_u = conn.read(worksheet="Empleados")
            with st.expander("➕ Agregar Empleado"):
                with st.form("f_u"):
                    nid, nnom = st.text_input("ID"), st.text_input("Nombre")
                    if st.form_submit_button("Guardar"):
                        conn.update(worksheet="Empleados", data=pd.concat([df_u, pd.DataFrame([{"ID": nid, "Nombre": nnom}])], ignore_index=True))
                        st.rerun()
            st.dataframe(df_u, use_container_width=True)

        with tab_tiendas:
            st.subheader("🏪 Control de Sucursales")
            st.info("Aquí puedes agregar las coordenadas de tus nuevos locales en Nogales.")
            
            with st.expander("➕ Agregar Nueva Sucursal"):
                with st.form("f_s"):
                    s_nom = st.text_input("Nombre de la Tienda (Ej. 3B 24 de Febrero)")
                    col_lat, col_lon = st.columns(2)
                    s_lat = col_lat.number_input("Latitud", format="%.6f", value=31.320189)
                    s_lon = col_lon.number_input("Longitud", format="%.6f", value=-110.943909)
                    if st.form_submit_button("Registrar Tienda"):
                        df_s = conn.read(worksheet="Sucursales")
                        conn.update(worksheet="Sucursales", data=pd.concat([df_s, pd.DataFrame([{"Nombre": s_nom, "Latitud": s_lat, "Longitud": s_lon}])], ignore_index=True))
                        st.success(f"Tienda {s_nom} agregada."); st.rerun()
            
            st.divider()
            st.write("### Sucursales Activas")
            df_list_s = conn.read(worksheet="Sucursales")
            for i, r in df_list_s.iterrows():
                c_i, c_b = st.columns([4, 1])
                c_i.write(f"**{r['Nombre']}** ({r['Latitud']}, {r['Longitud']})")
                if c_b.button("🗑️", key=f"del_s_{i}"):
                    conn.update(worksheet="Sucursales", data=df_list_s.drop(i))
                    st.rerun()
    else:
        st.warning("🔒 Acceso Restringido.")
