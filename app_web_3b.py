import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime
from streamlit_js_eval import get_geolocation
from supabase import create_client

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Abarrotes Las 3B - Asistencia", layout="wide")

# 2. CONEXIÓN A SUPABASE (Usa los Secrets que ya configuramos)
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("Error en las llaves de conexión de Supabase. Revisa los Secrets.")
    st.stop()

# 3. CARGAR DATOS DE SUCURSALES DESDE SUPABASE
@st.cache_data(ttl=600)
def cargar_sucursales():
    try:
        res = supabase.table("sucursales").select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty:
            return {"Fusión": {"lat": 31.320189, "lon": -110.943909}}
        return {r['nombre']: {'lat': r['latitud'], 'lon': r['longitud']} for _, r in df.iterrows()}
    except:
        # Sucursal por defecto si la tabla está vacía
        return {"Fusión": {"lat": 31.320189, "lon": -110.943909}}

SUCURSALES = cargar_sucursales()

# 4. INTERFAZ DE USUARIO
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1162/1162283.png", width=100) # Icono genérico de tienda
    st.title("Abarrotes Las 3B")
    menu = st.radio("MENÚ", ["📱 REGISTRO", "🔐 ADMIN"])

# --- MÓDULO DE REGISTRO ---
if menu == "📱 REGISTRO":
    st.header("Registro de Asistencia")
    id_emp = st.text_input("🆔 Ingrese su ID de Empleado")
    
    st.info("Obteniendo ubicación GPS... Por favor espere.")
    loc = get_geolocation()
    
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        
        # Verificar si está cerca de alguna sucursal (rango 60 metros)
        tienda_cercana = None
        for nombre, coords in SUCURSALES.items():
            distancia = geodesic((lat, lon), (coords['lat'], coords['lon'])).meters
            if distancia <= 60:
                tienda_cercana = nombre
                break

        if tienda_cercana:
            st.success(f"📍 Estás en la sucursal: **{tienda_cercana}**")
            if st.button("✅ REGISTRAR ENTRADA/SALIDA"):
                if id_emp:
                    nuevo_registro = {
                        "fecha": str(datetime.date.today()),
                        "hora": datetime.datetime.now().strftime("%H:%M:%S"),
                        "empleado_id": id_emp,
                        "tienda": tienda_cercana
                    }
                    try:
                        supabase.table("registros").insert(nuevo_registro).execute()
                        st.balloons()
                        st.success(f"¡Registro exitoso! Hola {id_emp}, se guardó tu asistencia en {tienda_cercana}.")
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
                else:
                    st.warning("⚠️ Por favor ingresa tu ID de empleado.")
        else:
            st.error("❌ No te encuentras dentro de ninguna sucursal de Abarrotes Las 3B.")
            # Mapa para que el usuario vea dónde está
            m = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker([lat, lon], popup="Tu ubicación", icon=folium.Icon(color='red')).add_to(m)
            st_folium(m, width=700, height=300)
    else:
        st.warning("📡 Para registrarte, debes permitir el acceso al GPS de tu celular.")

# --- MÓDULO DE ADMINISTRACIÓN ---
elif menu == "🔐 ADMIN":
    password = st.sidebar.text_input("Contraseña Admin", type="password")
    if password == "3b_admin":
        st.header("Panel de Control")
        
        # Ver Registros
        res_r = supabase.table("registros").select("*").order("fecha", desc=True).execute()
        df_reg = pd.DataFrame(res_r.data)
        
        if not df_reg.empty:
            st.write("### Registros de Asistencia Recientes")
            st.dataframe(df_reg, use_container_width=True)
            
            # Botón para descargar reporte
            csv = df_reg.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte CSV", csv, "reporte_3b.csv", "text/csv")
        else:
            st.info("Aún no hay registros en la base de datos.")
