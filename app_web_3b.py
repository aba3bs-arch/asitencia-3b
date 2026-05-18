import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from geopy.distance import geodesic
import pandas as pd
import datetime

from config import SUCURSALES, RADIO_PERMITIDO_METROS

if "registros" not in st.session_state:
    st.session_state.registros = []


def sucursal_mas_cercana(lat, lon):
    """Devuelve (nombre, distancia_metros) de la sucursal más cercana."""
    mejor = None
    for nombre, coords in SUCURSALES.items():
        dist = geodesic((lat, lon), (coords["lat"], coords["lon"])).meters
        if mejor is None or dist < mejor[1]:
            mejor = (nombre, dist)
    return mejor


def admin_password():
    """Contraseña desde secrets (nube) o valor local por defecto."""
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError, AttributeError):
        return "3b_admin"

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

    st.info("Pulsa **Obtener ubicación** y acepta el permiso de GPS en tu navegador o celular.")
    location = streamlit_geolocation()

    if not location or location == "No Location Info":
        st.warning("Aún no hay ubicación. Usa el botón de arriba para activar el GPS.")
    elif not isinstance(location, dict) or "latitude" not in location:
        st.error("No se pudo leer el GPS. Revisa los permisos de ubicación e intenta de nuevo.")
    else:
        lat_gps = location["latitude"]
        lon_gps = location["longitude"]
        precision = location.get("accuracy")

        nombre_cercana, dist_cercana = sucursal_mas_cercana(lat_gps, lon_gps)
        tienda_detectada = nombre_cercana if dist_cercana <= RADIO_PERMITIDO_METROS else None

        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"Coordenadas: {lat_gps:.6f}, {lon_gps:.6f}")
        with col2:
            if precision is not None:
                st.caption(f"Precisión GPS: ±{precision:.0f} m")

        if tienda_detectada:
            st.success(f"📍 Dentro de rango — Sucursal **{tienda_detectada}** ({dist_cercana:.0f} m)")
            if st.button("REGISTRAR ENTRADA/SALIDA", disabled=not id_emp.strip()):
                if not id_emp.strip():
                    st.error("Ingresa tu ID de empleado.")
                else:
                    hora = datetime.datetime.now().strftime("%H:%M:%S")
                    st.session_state.registros.append({
                        "empleado": id_emp.strip(),
                        "tienda": tienda_detectada,
                        "hora": hora,
                        "lat": lat_gps,
                        "lon": lon_gps,
                    })
                    st.balloons()
                    st.success(f"Registro exitoso a las {hora}")
        else:
            st.error(
                f"❌ FUERA DE RANGO. Estás a **{dist_cercana:.0f} m** de {nombre_cercana} "
                f"(máximo permitido: {RADIO_PERMITIDO_METROS} m)."
            )

# ---------------------------------------------------------
# SECCIÓN 2: PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif menu == "PANEL ADMINISTRADOR":
    password = st.sidebar.text_input("Contraseña Admin", type="password")
    if password and password == admin_password():
        st.title("📍 Monitoreo Real Abarrotes 3B")
        
        # Mapa
        m = folium.Map(location=[31.3050, -110.9300], zoom_start=13)
        for nombre, coords in SUCURSALES.items():
            folium.Circle([coords['lat'], coords['lon']], radius=20, color="red", fill=True).add_to(m)
            folium.Marker([coords['lat'], coords['lon']], popup=nombre).add_to(m)
        
        for reg in st.session_state.registros:
            folium.Marker(
                location=[reg["lat"], reg["lon"]],
                icon=folium.DivIcon(html='<div class="pulse"></div>'),
                popup=f"{reg['empleado']} — {reg['tienda']} ({reg['hora']})",
            ).add_to(m)
        
        st_folium(m, width="100%", height=500)
        
        st.subheader("Historial de Hoy")
        if st.session_state.registros:
            df = pd.DataFrame(st.session_state.registros)[["empleado", "tienda", "hora"]]
            df.columns = ["Empleado", "Tienda", "Hora"]
            st.table(df)
        else:
            st.caption("Sin registros aún. Los checados del portal empleado aparecerán aquí.")
    else:
        st.warning("Ingresa la contraseña para ver el mapa.")