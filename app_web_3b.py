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

# --- FUNCIONES DE GESTIÓN ---
def obtener_empleados():
    res = supabase.table("empleados").select("*").execute()
    return pd.DataFrame(res.data)

def guardar_empleado(id_e, nombre):
    supabase.table("empleados").upsert({"id": id_e, "nombre": nombre}).execute()

def eliminar_empleado(id_e):
    supabase.table("empleados").delete().eq("id", id_e).execute()

# --- INTERFAZ ---
with st.sidebar:
    st.title("Abarrotes Las 3B")
    menu = st.radio("MENÚ", ["📱 REGISTRO", "🔐 ADMIN"])

if menu == "📱 REGISTRO":
    st.header("Control de Asistencia")
    # Nota sobre biométricos: 
    # En la web, se recomienda usar el desbloqueo del propio teléfono del empleado
    id_emp = st.text_input("🆔 ID de Empleado")
    
    loc = get_geolocation()
    if loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        # Lógica de cercanía (mantenida del anterior)...
        st.success("GPS Activo")
        # Aquí se activaría el botón de registro si está en rango
    else:
        st.warning("Se requiere GPS y validación biométrica del dispositivo.")

elif menu == "🔐 ADMIN":
    password = st.sidebar.text_input("Clave Admin", type="password")
    if password == "3b_admin":
        tab1, tab2 = st.tabs(["📊 Reportes", "👥 Gestión de Personal"])
        
        with tab1:
            st.subheader("Registros de Asistencia")
            res_r = supabase.table("registros").select("*").execute()
            st.dataframe(pd.DataFrame(res_r.data))
            
        with tab2:
            st.subheader("Control de Usuarios")
            
            # Formulario para Crear/Editar
            with st.expander("➕ Agregar / Editar Empleado"):
                id_nuevo = st.text_input("ID del Empleado")
                nombre_nuevo = st.text_input("Nombre Completo")
                if st.button("Guardar Empleado"):
                    guardar_empleado(id_nuevo, nombre_nuevo)
                    st.success("Empleado actualizado")
                    st.rerun()

            # Tabla con opción de eliminar
            df_emp = obtener_empleados()
            if not df_emp.empty:
                for index, row in df_emp.iterrows():
                    col1, col2, col3 = st.columns([2, 4, 2])
                    col1.write(f"**{row['id']}**")
                    col2.write(row['nombre'])
                    if col3.button("Eliminar", key=f"del_{row['id']}"):
                        eliminar_empleado(row['id'])
                        st.error(f"Eliminado: {row['id']}")
                        st.rerun()
