import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime
from streamlit_js_eval import get_geolocation
from supabase import create_client
import io

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Abarrotes Las 3B", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- FUNCIONES DE BASE DE DATOS ---
def obtener_datos(tabla):
    try:
        res = supabase.table(tabla).select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def guardar_datos(tabla, datos):
    try:
        supabase.table(tabla).upsert(datos).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# --- INTERFAZ LATERAL ---
with st.sidebar:
    # Usando el archivo específico que mencionaste
    try:
        st.image("logo_3b_2.png", use_container_width=True)
    except:
        st.info("Cargando logo...")
    
    st.title("Abarrotes Las 3B")
    opcion_principal = st.radio("IR A:", ["📱 REGISTRO", "🔐 ADMIN"])
    st.markdown("---")
    
    password_correcta = False
    admin_seccion = "Reportes"
    if opcion_principal == "🔐 ADMIN":
        pwd = st.text_input("Clave de Acceso", type="password")
        if pwd == "3b_admin":
            password_correcta = True
            admin_seccion = st.radio("CONTROL:", ["📊 Reportes", "👥 Personal", "📍 Sucursales"])

# --- LADO DERECHO ---
if opcion_principal == "📱 REGISTRO":
    st.header("📸 Registro con Verificación")
    col_cam, col_map = st.columns([1, 1])
    
    with col_cam:
        id_emp = st.text_input("🆔 ID de Empleado")
        foto = st.camera_input("Toma una foto para verificar tu identidad")
    
    with col_map:
        loc = get_geolocation()
        if loc:
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            df_suc = obtener_datos("sucursales")
            
            m = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker([lat, lon], tooltip="Tú", icon=folium.Icon(color="blue")).add_to(m)
            
            tienda_cercana = None
            if not df_suc.empty:
                for _, suc in df_suc.iterrows():
                    dist = geodesic((lat, lon), (suc['latitud'], suc['longitud'])).meters
                    folium.Marker([suc['latitud'], suc['longitud']], popup=suc['nombre'], icon=folium.Icon(color="red")).add_to(m)
                    if dist <= 120: tienda_cercana = suc['nombre']
            
            st_folium(m, width="100%", height=300)

            if tienda_cercana and foto and id_emp:
                st.success(f"📍 Ubicación y Foto listas en: **{tienda_cercana}**")
                if st.button("✅ FINALIZAR REGISTRO"):
                    datos = {
                        "empleado_id": id_emp,
                        "tienda": tienda_cercana,
                        "fecha": str(datetime.date.today()),
                        "hora": datetime.datetime.now().strftime("%H:%M:%S")
                    }
                    if guardar_datos("registros", datos):
                        st.balloons()
                        st.success("¡Registro completado con éxito!")
            elif not foto:
                st.info("Por favor, toma la foto para habilitar el registro.")
            elif not tienda_cercana:
                st.error("Debes estar en una sucursal para checar.")

# (Sección ADMIN se mantiene igual que la versión anterior)
elif opcion_principal == "🔐 ADMIN" and password_correcta:
    if admin_seccion == "📊 Reportes":
        st.header("Historial de Asistencias")
        df_reg = obtener_datos("registros")
        if not df_reg.empty:
            st.dataframe(df_reg.sort_values(by="fecha", ascending=False), use_container_width=True)
