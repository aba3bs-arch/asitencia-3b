import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd
import datetime
from streamlit_js_eval import get_geolocation
from supabase import create_client

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Abarrotes Las 3B", layout="wide")

# Conexión con tus Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

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

# --- INTERFAZ LATERAL (MENÚ) ---
with st.sidebar:
    st.title("🛒 Abarrotes Las 3B")
    opcion_principal = st.radio("IR A:", ["📱 REGISTRO", "🔐 ADMIN"])
    
    st.markdown("---")
    
    # Si estamos en ADMIN, mostrar los botones debajo del Login
    admin_seccion = "Reportes"
    if opcion_principal == "🔐 ADMIN":
        password = st.text_input("Clave de Acceso", type="password")
        if password == "3b_admin":
            st.success("Acceso Autorizado")
            admin_seccion = st.radio("CONTROL DE TIENDA:", ["📊 Reportes", "👥 Personal", "📍 Sucursales"])
        else:
            st.info("Introduce la clave para ver opciones")

# --- LADO DERECHO (CONTENIDO PRINCIPAL) ---

# CASO 1: PANTALLA DE REGISTRO PARA EMPLEADOS
if opcion_principal == "📱 REGISTRO":
    st.header("📍 Registro de Asistencia")
    col_mapa, col_info = st.columns([2, 1])
    
    with col_info:
        id_emp = st.text_input("🆔 ID de Empleado")
        loc = get_geolocation()
    
    with col_mapa:
        if loc:
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            df_suc = obtener_datos("sucursales")
            
            m = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker([lat, lon], tooltip="Tú", icon=folium.Icon(color="blue")).add_to(m)
            
            tienda_cercana = None
            for _, suc in df_suc.iterrows():
                dist = geodesic((lat, lon), (suc['latitud'], suc['longitud'])).meters
                folium.Marker([suc['latitud'], suc['longitud']], popup=suc['nombre'], icon=folium.Icon(color="red")).add_to(m)
                if dist <= 120: tienda_cercana = suc['nombre']

            st_folium(m, width="100%", height=400)
            
            if tienda_cercana:
                st.success(f"Estás en: **{tienda_cercana}**")
                if st.button("✅ REGISTRAR AHORA"):
                    if id_emp:
                        datos = {"empleado_id": id_emp, "tienda": tienda_cercana, "fecha": str(datetime.date.today()), "hora": datetime.datetime.now().strftime("%H:%M:%S")}
                        if guardar_datos("registros", datos): st.balloons()
            else:
                st.error("Fuera de rango de las sucursales.")
        else:
            st.warning("Buscando GPS...")

# CASO 2: PANTALLA DE ADMINISTRACIÓN (CONTENIDO DERECHO)
elif opcion_principal == "🔐 ADMIN" and 'password' in locals() and password == "3b_admin":
    
    if admin_seccion == "📊 Reportes":
        st.header("Historial de Asistencias")
        df_reg = obtener_datos("registros")
        st.dataframe(df_reg.sort_values(by="fecha", ascending=False), use_container_width=True)

    elif admin_seccion == "👥 Personal":
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("➕ Nuevo")
            id_e = st.text_input("ID")
            nom_e = st.text_input("Nombre")
            if st.button("Guardar"):
                if guardar_datos("empleados", {"id": id_e, "nombre": nom_e}): st.rerun()
        
        with col2:
            st.subheader("👥 Empleados Activos")
            df_e = obtener_datos("empleados")
            # Lista en línea
            for _, row in df_e.iterrows():
                c_id, c_nom, c_del = st.columns([1, 3, 1])
                c_id.write(f"`{row['id']}`")
                c_nom.write(row['nombre'])
                if c_del.button("🗑️", key=f"del_{row['id']}"):
                    eliminar_datos("empleados", "id", row['id'])
                    st.rerun()

    elif admin_seccion == "📍 Sucursales":
        col_form, col_map = st.columns([1, 2])
        with col_form:
            st.subheader("➕ Nueva Tienda")
            n_t = st.text_input("Nombre")
            la_t = st.number_input("Lat", format="%.6f")
            lo_t = st.number_input("Lon", format="%.6f")
            if st.button("Agregar"):
                if guardar_datos("sucursales", {"nombre": n_t, "latitud": la_t, "longitud": lo_t}): st.rerun()
        
        with col_map:
            st.subheader("📍 Mapa de Rutas")
            df_s = obtener_datos("sucursales")
            if not df_s.empty:
                m_admin = folium.Map(location=[31.30, -110.93], zoom_start=13)
                for _, s in df_s.iterrows():
                    folium.Marker([s['latitud'], s['longitud']], popup=s['nombre']).add_to(m_admin)
                st_folium(m_admin, width="100%", height=400)
