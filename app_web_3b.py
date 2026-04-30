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

# --- FUNCIONES DE GESTIÓN (BASE DE DATOS) ---
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

# --- INTERFAZ PRINCIPAL ---
with st.sidebar:
    st.title("Abarrotes Las 3B")
    menu = st.radio("MENÚ", ["📱 REGISTRO", "🔐 ADMIN"])

# --- MÓDULO DE REGISTRO ---
if menu == "📱 REGISTRO":
    st.header("Control de Asistencia")
    id_emp = st.text_input("🆔 ID de Empleado")
    
    st.info("Obteniendo ubicación GPS...")
    loc = get_geolocation()
    
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        df_suc = obtener_datos("sucursales")
        
        tienda_cercana = None
        if not df_suc.empty:
            for _, suc in df_suc.iterrows():
                dist = geodesic((lat, lon), (suc['latitud'], suc['longitud'])).meters
                if dist <= 60:
                    tienda_cercana = suc['nombre']
                    break

        if tienda_cercana:
            st.success(f"📍 Ubicación confirmada: **{tienda_cercana}**")
            if st.button("✅ REGISTRAR ASISTENCIA"):
                if id_emp:
                    datos_reg = {
                        "fecha": str(datetime.date.today()),
                        "hora": datetime.datetime.now().strftime("%H:%M:%S"),
                        "empleado_id": id_emp,
                        "tienda": tienda_cercana
                    }
                    if guardar_datos("registros", datos_reg):
                        st.balloons()
                        st.success("¡Registro guardado correctamente!")
                else:
                    st.warning("Escribe tu ID de empleado.")
        else:
            st.error("No estás en una sucursal autorizada.")
    else:
        st.warning("Activa el GPS para checar.")

# --- MÓDULO DE ADMINISTRACIÓN ---
elif menu == "🔐 ADMIN":
    password = st.sidebar.text_input("Clave Admin", type="password")
    if password == "3b_admin":
        tab1, tab2, tab3 = st.tabs(["📊 Reportes", "👥 Personal", "📍 Sucursales"])
        
        # TAB 1: REPORTES
        with tab1:
            st.subheader("Historial de Asistencias")
            df_reg = obtener_datos("registros")
            st.dataframe(df_reg, use_container_width=True)

        # TAB 2: GESTIÓN DE PERSONAL
        with tab2:
            st.subheader("Control de Empleados")
            with st.expander("➕ Agregar/Editar Empleado"):
                id_e = st.text_input("ID")
                nom_e = st.text_input("Nombre")
                if st.button("Guardar Empleado"):
                    if guardar_datos("empleados", {"id": id_e, "nombre": nom_e}):
                        st.rerun()
            
            df_e = obtener_datos("empleados")
            for _, row in df_e.iterrows():
                c1, c2, c3 = st.columns([2, 4, 1])
                c1.write(row['id'])
                c2.write(row['nombre'])
                if c3.button("🗑️", key=f"del_e_{row['id']}"):
                    eliminar_datos("empleados", "id", row['id'])
                    st.rerun()

        # TAB 3: GESTIÓN DE SUCURSALES (NUEVA OPCIÓN)
        with tab3:
            st.subheader("Configuración de Tiendas")
            with st.expander("➕ Agregar Nueva Tienda"):
                nom_t = st.text_input("Nombre de la Tienda")
                lat_t = st.number_input("Latitud", format="%.6f")
                lon_t = st.number_input("Longitud", format="%.6f")
                st.caption("Tip: Abre Google Maps, deja presionado el lugar y copia los números.")
                if st.button("Guardar Tienda"):
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
