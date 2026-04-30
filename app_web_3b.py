import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime
from streamlit_js_eval import get_geolocation
from supabase import create_client

# 1. CONFIGURACIÓN Y CONEXIÓN
st.set_page_config(page_title="Abarrotes Las 3B", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- CARGA INICIAL DE TIENDAS (NOGALES) ---
TIENDAS_INICIALES = [
    {"nombre": "Fusión", "latitud": 31.320189, "longitud": -110.943909},
    {"nombre": "3B2", "latitud": 31.300544, "longitud": -110.923907},
    {"nombre": "3B3", "latitud": 31.300544, "longitud": -110.936193},
    {"nombre": "3B5", "latitud": 31.289624, "longitud": -110.931254},
    {"nombre": "3B6", "latitud": 31.294967, "longitud": -110.915074},
    {"nombre": "3B7", "latitud": 31.309213, "longitud": -110.930617},
    {"nombre": "3B9", "latitud": 31.329842, "longitud": -110.943361},
    {"nombre": "3B10", "latitud": 31.301250, "longitud": -110.937966},
]

def obtener_datos(tabla):
    res = supabase.table(tabla).select("*").execute()
    return pd.DataFrame(res.data)

def guardar_datos(tabla, datos):
    try:
        supabase.table(tabla).upsert(datos).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# Inyectar tiendas si la tabla está vacía
df_suc_check = obtener_datos("sucursales")
if df_suc_check.empty:
    for t in TIENDAS_INICIALES:
        guardar_datos("sucursales", t)
    st.rerun()

# --- INTERFAZ ---
with st.sidebar:
    st.title("Abarrotes Las 3B")
    menu = st.radio("MENÚ", ["📱 REGISTRO", "🔐 ADMIN"])

if menu == "📱 REGISTRO":
    st.header("Control de Asistencia")
    id_emp = st.text_input("🆔 ID de Empleado")
    
    loc = get_geolocation()
    
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        df_suc = obtener_datos("sucursales")
        
        # MOSTRAR MAPA
        m = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker([lat, lon], tooltip="Tú estás aquí", icon=folium.Icon(color="blue")).add_to(m)
        
        tienda_cercana = None
        for _, suc in df_suc.iterrows():
            dist = geodesic((lat, lon), (suc['latitud'], suc['longitud'])).meters
            # Dibujar tiendas en el mapa
            folium.Marker([suc['latitud'], suc['longitud']], 
                          popup=f"Tienda: {suc['nombre']}", 
                          icon=folium.Icon(color="red")).add_to(m)
            
            if dist <= 100: # Rango de 100 metros
                tienda_cercana = suc['nombre']

        st_folium(m, width=700, height=450)

        if tienda_cercana:
            st.success(f"📍 Ubicación confirmada: **{tienda_cercana}**")
            if st.button("✅ REGISTRAR ASISTENCIA"):
                if id_emp:
                    res = guardar_datos("registros", {
                        "empleado_id": id_emp,
                        "tienda": tienda_cercana,
                        "fecha": str(datetime.date.today()),
                        "hora": datetime.datetime.now().strftime("%H:%M:%S")
                    })
                    if res: st.success("¡Registro guardado!"); st.balloons()
        else:
            st.error("No estás cerca de ninguna sucursal 3B.")
    else:
        st.warning("Esperando señal de GPS...")

elif menu == "🔐 ADMIN":
    # (El resto del código de administración se mantiene igual que el anterior)
    st.write("Panel de administración activo")
