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

# Conexión segura
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- FUNCIONES DE BASE DE DATOS ---
def obtener_datos(tabla):
    try:
        res = supabase.table(tabla).select("*").execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

def guardar_datos(tabla, datos):
    try:
        supabase.table(tabla).upsert(datos).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def eliminar_datos(tabla, columna_id, valor_id):
    try:
        supabase.table(tabla).delete().eq(columna_id, valor_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False

# --- INTERFAZ LATERAL ---
with st.sidebar:
    try:
        # Referencia exacta al archivo solicitado
        st.image("logo_3b_2.png", use_container_width=True)
    except:
        st.info("Sube 'logo_3b_2.png' para verlo aquí")
    
    st.title("Abarrotes Las 3B")
    opcion_principal = st.radio("IR A:", ["📱 REGISTRO", "🔐 ADMIN"])
    st.markdown("---")
    
    password_correcta = False
    admin_seccion = "📊 Reportes"
    
    if opcion_principal == "🔐 ADMIN":
        pwd = st.text_input("Clave de Acceso", type="password")
        if pwd == "3b_admin":
            password_correcta = True
            st.success("Acceso Autorizado")
            admin_seccion = st.radio("CONTROL:", ["📊 Reportes", "👥 Personal", "📍 Sucursales"])
        elif pwd:
            st.error("Clave incorrecta")

# --- LADO DERECHO (CONTENIDO PRINCIPAL) ---

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
                    if dist <= 120: 
                        tienda_cercana = suc['nombre']
            
            st_folium(m, width="100%", height=300)

            if tienda_cercana and foto and id_emp:
                st.success(f"📍 Estás en: **{tienda_cercana}**")
                if st.button("✅ FINALIZAR REGISTRO"):
                    datos = {
                        "empleado_id": id_emp,
                        "tienda": tienda_cercana,
                        "fecha": str(datetime.date.today()),
                        "hora": datetime.datetime.now().strftime("%H:%M:%S")
                    }
                    if guardar_datos("registros", datos):
                        st.balloons()
                        st.success("¡Registro completado!")
            elif not foto:
                st.info("Toma la foto para habilitar el registro.")
            elif not tienda_cercana:
                st.error("No estás cerca de una sucursal.")
        else:
            st.warning("Buscando GPS...")

elif opcion_principal == "🔐 ADMIN" and password_correcta:
    
    if admin_seccion == "📊 Reportes":
        st.header("Historial de Asistencias")
        df_reg = obtener_datos("registros")
        if not df_reg.empty:
            # Ordenar solo si la columna existe
            if 'fecha' in df_reg.columns:
                df_reg = df_reg.sort_values(by="fecha", ascending=False)
            st.dataframe(df_reg, use_container_width=True)
        else:
            st.info("Aún no hay registros de asistencia.")

    elif admin_seccion == "👥 Personal":
        col_form, col_lista = st.columns([1, 2])
        with col_form:
            st.subheader("➕ Nuevo Empleado")
            id_e = st.text_input("ID")
            nom_e = st.text_input("Nombre")
            if st.button("Guardar"):
                if id_e and nom_e:
                    if guardar_datos("empleados", {"id": id_e, "nombre": nom_e}): st.rerun()
        
        with col_lista:
            st.subheader("👥 Personal Registrado")
            df_e = obtener_datos("empleados")
            if not df_e.empty:
                for _, row in df_e.iterrows():
                    c1, c2, c3 = st.columns([1, 3, 1])
                    c1.write(f"`{row.get('id', 'N/A')}`")
                    c2.write(row.get('nombre', 'Sin Nombre'))
                    if c3.button("🗑️", key=f"del_emp_{row.get('id')}"):
                        eliminar_datos("empleados", "id", row['id'])
                        st.rerun()
            else:
                st.write("No hay empleados en la base de datos.")

    elif admin_seccion == "📍 Sucursales":
        col_f, col_m = st.columns([1, 2])
        with col_f:
            st.subheader("➕ Nueva Tienda")
            n_t = st.text_input("Nombre Tienda")
            la_t = st.number_input("Lat", format="%.6f")
            lo_t = st.number_input("Lon", format="%.6f")
            if st.button("Agregar Sucursal"):
                if n_t:
                    if guardar_datos("sucursales", {"nombre": n_t, "latitud": la_t, "longitud": lo_t}): st.rerun()
        
        with col_m:
            st.subheader("📍 Mapa de Sucursales")
            df_s = obtener_datos("sucursales")
            if not df_s.empty:
                m_adm = folium.Map(location=[31.30, -110.93], zoom_start=13)
                for _, s in df_s.iterrows():
                    folium.Marker([s['latitud'], s['longitud']], popup=s['nombre']).add_to(m_adm)
                st_folium(m_adm, width="100%", height=350)
            else:
                st.info("No hay sucursales registradas.")
