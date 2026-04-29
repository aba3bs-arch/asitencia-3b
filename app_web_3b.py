import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime
import os
from streamlit_js_eval import get_geolocation
from streamlit_gsheets import GSheetsConnection # IMPORT CORREGIDO

# CONFIGURACIÓN
st.set_page_config(page_title="Abarrotes Las 3B", layout="wide", page_icon="📖")
conn = st.connection("gsheets", type=GSheetsConnection)

# CARGAR SUCURSALES DESDE GOOGLE
try:
    df_s = conn.read(worksheet="Sucursales")
    SUCURSALES = {r['Nombre']: {'lat': r['Latitud'], 'lon': r['Longitud']} for _, r in df_s.iterrows()}
except:
    SUCURSALES = {"Fusión": {"lat": 31.320189, "lon": -110.943909}}

# ESTILOS Y LOGO
logo_path = "logo_3b.png"
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    menu = st.radio("MENÚ", ["📱 REGISTRO", "🔐 ADMIN"])

# LÓGICA DE REGISTRO
if menu == "📱 REGISTRO":
    st.title("Asistencia Las 3B")
    id_emp = st.text_input("🆔 ID de Empleado")
    loc = get_geolocation()
    
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        tienda = next((n for n, c in SUCURSALES.items() if geodesic((lat, lon), (c['lat'], c['lon'])).meters <= 40), None)

        if tienda:
            st.success(f"📍 En sucursal: {tienda}")
            if st.button("REGISTRAR"):
                if id_emp:
                    now = datetime.datetime.now()
                    nuevo = pd.DataFrame([{"Fecha": now.strftime("%Y-%m-%d"), "Hora": now.strftime("%H:%M:%S"), "ID": id_emp, "Tienda": tienda}])
                    df_r = conn.read(worksheet="Registros")
                    conn.update(worksheet="Registros", data=pd.concat([df_r, nuevo], ignore_index=True))
                    st.balloons(); st.success("✅ Registro Exitoso")
        else: st.error("❌ Fuera de rango")

# LÓGICA DE ADMIN
elif menu == "🔐 ADMIN":
    if st.sidebar.text_input("Clave", type="password") == "3b_admin":
        tab1, tab2 = st.tabs(["👥 Personal", "🏪 Tiendas"])
        with tab1:
            st.write("### Gestión de Empleados")
            # Aquí puedes ver y editar tu lista de Google Sheets
            st.dataframe(conn.read(worksheet="Empleados"), use_container_width=True)
