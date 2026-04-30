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

# Usando tus credenciales guardadas en Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- COORDINADAS DE NOGALES ---
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

# --- FUNCIONES DE BASE DE DATOS ---
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

def eliminar_datos(tabla, columna_id, valor_id):
    supabase.table(tabla).delete().eq(columna_id, valor_id).execute()

# --- CARGA AUTOMÁTICA DE TIENDAS ---
try:
    df_suc_check = obtener_datos("sucursales")
    if df_suc_check.empty:
        for t in TIENDAS_INICIALES:
            guardar_datos("sucursales", t)
except:
    pass

# --- INTERFAZ LATERAL ---
with st.sidebar:
    st.title("Abarrotes Las 3B")
    menu = st.radio("MENÚ", ["📱 REGISTRO", "🔐 ADMIN"])

# --- MÓDULO DE REGISTRO ---
if menu == "📱 REGISTRO":
    st.header("📍 Control de Asistencia")
    id_emp = st.text_input("🆔 ID de Empleado")
    
    loc = get_geolocation()
    
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        df_suc = obtener_datos("sucursales")
        
        # Mapa centrado en tu posición
        m = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker([lat, lon], tooltip="Tú estás aquí", icon=folium.Icon(color="blue", icon="user")).add_to(m)
        
        tienda_cercana = None
        for _, suc in df_suc.iterrows():
            dist = geodesic((lat, lon), (suc['latitud'], suc['longitud'])).meters
            folium.Marker([suc['latitud'], suc['longitud']], 
                          popup=f"Tienda: {suc['nombre']}", 
                          icon=folium.Icon(color="red", icon="shopping-cart")).add_to(m)
            
            if dist <= 120: # Rango de tolerancia
                tienda_cercana = suc['nombre']

        st_folium(m, width="100%", height=400)

        if tienda_cercana:
            st.success(f"📍 Estás en: **{tienda_cercana}**")
            if st.button("✅ REGISTRAR ASISTENCIA"):
                if id_emp:
                    datos = {
                        "empleado_id": id_emp,
                        "tienda": tienda_cercana,
                        "fecha": str(datetime.date.today()),
                        "hora": datetime.datetime.now().strftime("%H:%M:%S")
                    }
                    if guardar_datos("registros", datos):
                        st.balloons()
                        st.success("¡Asistencia registrada correctamente!")
                else:
                    st.warning("Por favor, ingresa tu ID.")
        else:
            st.error("No se detectó ninguna sucursal cercana. Acércate a la tienda.")
    else:
        st.info("Esperando señal de GPS... Asegúrate de permitir el acceso a tu ubicación.")

# --- MÓDULO DE ADMINISTRACIÓN (COMPLETO) ---
elif menu == "🔐 ADMIN":
    password = st.sidebar.text_input("Clave de Acceso", type="password")
    if password == "3b_admin":
        st.header("⚙️ Panel de Administración")
        tab1, tab2, tab3 = st.tabs(["📊 Reportes", "👥 Personal", "📍 Sucursales"])
        
        with tab1:
            st.subheader("Historial de Asistencias")
            df_reg = obtener_datos("registros")
            if not df_reg.empty:
                st.dataframe(df_reg.sort_values(by="fecha", ascending=False), use_container_width=True)
            else:
                st.info("Aún no hay registros de asistencia.")

        with tab2:
            st.subheader("Gestión de Empleados")
            with st.expander("➕ Registrar Nuevo Empleado"):
                id_e = st.text_input("ID del Empleado")
                nom_e = st.text_input("Nombre Completo")
                if st.button("Guardar Empleado"):
                    if id_e and nom_e:
                        if guardar_datos("empleados", {"id": id_e, "nombre": nom_e}):
                            st.rerun()
            
            df_e = obtener_datos("empleados")
            for _, row in df_e.iterrows():
                c1, c2, c3 = st.columns([2, 5, 1])
                c1.write(f"`{row['id']}`")
                c2.write(row['nombre'])
                if c3.button("🗑️", key=f"del_e_{row['id']}"):
                    eliminar_datos("empleados", "id", row['id'])
                    st.rerun()

        with tab3:
            st.subheader("Gestión de Sucursales")
            with st.expander("➕ Agregar Nueva Tienda"):
                nom_t = st.text_input("Nombre de Sucursal")
                lat_t = st.number_input("Latitud", format="%.6f")
                lon_t = st.number_input("Longitud", format="%.6f")
                if st.button("Guardar Sucursal"):
                    if guardar_datos("sucursales", {"nombre": nom_t, "latitud": lat_t, "longitud": lon_t}):
                        st.rerun()
            
            df_t = obtener_datos("sucursales")
            for _, row in df_t.iterrows():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                c1.write(f"**{row['nombre']}**")
                c2.write(row['latitud'])
                c3.write(row['longitud'])
                if c4.button("🗑️", key=f"del_t_{row['nombre']}"):
                    eliminar_datos("sucursales", "nombre", row['nombre'])
                    st.rerun()
    else:
        st.warning("Introduce la clave en la barra lateral para ver la administración.")
