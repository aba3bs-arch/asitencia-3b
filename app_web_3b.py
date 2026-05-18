import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from geopy.distance import geodesic
import pandas as pd
import datetime

from config import RADIO_PERMITIDO_METROS
from storage import load_empleados, save_empleados, load_sucursales, save_sucursales

if "registros" not in st.session_state:
    st.session_state.registros = []


def get_sucursales():
    if "sucursales" not in st.session_state:
        st.session_state.sucursales = load_sucursales()
    return st.session_state.sucursales


def get_empleados():
    if "empleados" not in st.session_state:
        st.session_state.empleados = load_empleados()
    return st.session_state.empleados


def refresh_sucursales():
    st.session_state.sucursales = load_sucursales()


def refresh_empleados():
    st.session_state.empleados = load_empleados()


def sucursal_mas_cercana(lat, lon, sucursales):
    mejor = None
    for nombre, coords in sucursales.items():
        dist = geodesic((lat, lon), (coords["lat"], coords["lon"])).meters
        if mejor is None or dist < mejor[1]:
            mejor = (nombre, dist)
    return mejor


def admin_password():
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError, AttributeError):
        return "3b_admin"


def parse_coord(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def coords_desde_ubicacion(location):
    if not location or location == "No Location Info" or not isinstance(location, dict):
        return None, None
    return parse_coord(location.get("latitude")), parse_coord(location.get("longitude"))


def empleado_valido(id_emp):
    empleados = get_empleados()
    if not empleados:
        return False, "No hay empleados registrados. El administrador debe dar de alta empleados primero."
    ids = {e["id"] for e in empleados if e.get("activo", True)}
    if id_emp not in ids:
        return False, f"El ID **{id_emp}** no está registrado o está inactivo."
    return True, None


def centro_mapa(sucursales):
    if not sucursales:
        return [31.3050, -110.9300]
    lats = [c["lat"] for c in sucursales.values()]
    lons = [c["lon"] for c in sucursales.values()]
    return [sum(lats) / len(lats), sum(lons) / len(lons)]


st.set_page_config(page_title="Sistema Abarrotes 3B", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 60px; font-weight: bold; font-size: 20px; }
    .pulse { height: 15px; width: 15px; background-color: #2ECC71; border-radius: 50%;
             display: inline-block; animation: pulse 1.5s infinite; }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

menu = st.sidebar.radio("MENÚ", ["REGISTRO EMPLEADO", "PANEL ADMINISTRADOR"])

# ---------------------------------------------------------
# REGISTRO EMPLEADO
# ---------------------------------------------------------
if menu == "REGISTRO EMPLEADO":
    st.image("https://logodownload.org/wp-content/uploads/2019/07/3b-logo.png", width=150)
    st.title("Control de Asistencia")

    sucursales = get_sucursales()
    if not sucursales:
        st.error("No hay sucursales configuradas. Contacta al administrador.")
        st.stop()

    empleados = get_empleados()
    if empleados:
        opciones = {e["id"]: f"{e['id']} — {e['nombre']}" for e in empleados if e.get("activo", True)}
        id_emp = st.selectbox("Selecciona tu ID de empleado", options=list(opciones.keys()),
                              format_func=lambda x: opciones[x])
    else:
        st.warning("Aún no hay empleados registrados.")
        id_emp = st.text_input("Ingresa tu ID de Empleado")

    st.info("Pulsa **Obtener ubicación** y acepta el permiso de GPS en tu navegador o celular.")
    location = streamlit_geolocation()

    if not location or location == "No Location Info":
        st.warning("Aún no hay ubicación. Usa el botón de arriba para activar el GPS.")
    elif not isinstance(location, dict) or "latitude" not in location:
        st.error("No se pudo leer el GPS. Revisa los permisos de ubicación e intenta de nuevo.")
    else:
        lat_gps, lon_gps = coords_desde_ubicacion(location)
        precision = parse_coord(location.get("accuracy"))

        if lat_gps is None or lon_gps is None:
            st.error("Coordenadas inválidas. Vuelve a pulsar **Obtener ubicación**.")
            st.stop()

        nombre_cercana, dist_cercana = sucursal_mas_cercana(lat_gps, lon_gps, sucursales)
        tienda_detectada = nombre_cercana if dist_cercana <= RADIO_PERMITIDO_METROS else None

        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"Coordenadas: {lat_gps:.6f}, {lon_gps:.6f}")
        with col2:
            if precision is not None:
                st.caption(f"Precisión GPS: ±{precision:.0f} m")

        if tienda_detectada:
            st.success(f"📍 Dentro de rango — Sucursal **{tienda_detectada}** ({dist_cercana:.0f} m)")
            if st.button("REGISTRAR ENTRADA/SALIDA", disabled=not str(id_emp).strip()):
                id_str = str(id_emp).strip()
                ok, msg = empleado_valido(id_str)
                if not ok:
                    st.error(msg)
                else:
                    hora = datetime.datetime.now().strftime("%H:%M:%S")
                    st.session_state.registros.append({
                        "empleado": id_str,
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
# PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif menu == "PANEL ADMINISTRADOR":
    password = st.sidebar.text_input("Contraseña Admin", type="password")
    if not password or password != admin_password():
        st.warning("Ingresa la contraseña para acceder al panel.")
        st.stop()

    tab_mon, tab_emp, tab_suc = st.tabs(["Monitoreo", "Empleados", "Sucursales"])

    # --- Monitoreo ---
    with tab_mon:
        st.title("📍 Monitoreo Abarrotes 3B")
        sucursales = get_sucursales()
        centro = centro_mapa(sucursales)

        m = folium.Map(location=centro, zoom_start=13)
        for nombre, coords in sucursales.items():
            folium.Circle(
                [coords["lat"], coords["lon"]],
                radius=RADIO_PERMITIDO_METROS,
                color="red",
                fill=True,
                popup=nombre,
            ).add_to(m)
            folium.Marker([coords["lat"], coords["lon"]], popup=nombre).add_to(m)

        for reg in st.session_state.registros:
            folium.Marker(
                location=[reg["lat"], reg["lon"]],
                icon=folium.DivIcon(html='<div class="pulse"></div>'),
                popup=f"{reg['empleado']} — {reg['tienda']} ({reg['hora']})",
            ).add_to(m)

        st_folium(m, width="100%", height=500)

        st.subheader("Historial de hoy")
        if st.session_state.registros:
            df = pd.DataFrame(st.session_state.registros)[["empleado", "tienda", "hora"]]
            df.columns = ["Empleado", "Tienda", "Hora"]
            st.table(df)
        else:
            st.caption("Sin registros en esta sesión.")

    # --- Empleados ---
    with tab_emp:
        st.subheader("Registrar empleado")
        with st.form("form_empleado", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_id = st.text_input("ID de empleado", placeholder="Ej: 001")
            with col2:
                nuevo_nombre = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez")
            guardar_emp = st.form_submit_button("Guardar empleado", type="primary")

        if guardar_emp:
            nuevo_id = nuevo_id.strip()
            nuevo_nombre = nuevo_nombre.strip()
            if not nuevo_id or not nuevo_nombre:
                st.error("ID y nombre son obligatorios.")
            else:
                empleados = get_empleados()
                if any(e["id"] == nuevo_id for e in empleados):
                    st.error(f"Ya existe un empleado con ID **{nuevo_id}**.")
                else:
                    empleados.append({"id": nuevo_id, "nombre": nuevo_nombre, "activo": True})
                    save_empleados(empleados)
                    refresh_empleados()
                    st.success(f"Empleado **{nuevo_nombre}** registrado.")
                    st.rerun()

        st.divider()
        st.subheader("Empleados registrados")
        empleados = get_empleados()
        if not empleados:
            st.info("No hay empleados. Registra el primero arriba.")
        else:
            for emp in empleados:
                c1, c2, c3 = st.columns([2, 3, 1])
                estado = "Activo" if emp.get("activo", True) else "Inactivo"
                c1.write(f"**{emp['id']}**")
                c2.write(f"{emp['nombre']} — _{estado}_")
                if c3.button("Eliminar", key=f"del_emp_{emp['id']}"):
                    empleados = [e for e in empleados if e["id"] != emp["id"]]
                    save_empleados(empleados)
                    refresh_empleados()
                    st.rerun()

    # --- Sucursales ---
    with tab_suc:
        st.subheader("Registrar sucursal")
        st.caption("Párate en la entrada de la tienda y captura la ubicación GPS.")

        nombre_suc = st.text_input("Nombre de la sucursal", placeholder="Ej: 3B11", key="nombre_nueva_suc")
        st.info("Pulsa **Obtener ubicación** estando en el local.")
        location_suc = streamlit_geolocation()

        lat_suc, lon_suc = coords_desde_ubicacion(location_suc)
        if lat_suc is not None and lon_suc is not None:
            st.caption(f"Ubicación capturada: {lat_suc:.6f}, {lon_suc:.6f}")

        if st.button("Guardar sucursal", type="primary", key="btn_guardar_suc"):
            nombre_suc = nombre_suc.strip()
            if not nombre_suc:
                st.error("Escribe el nombre de la sucursal.")
            elif lat_suc is None or lon_suc is None:
                st.error("Primero obtén la ubicación GPS con el botón de arriba.")
            else:
                sucursales = get_sucursales()
                if nombre_suc in sucursales:
                    st.error(f"Ya existe la sucursal **{nombre_suc}**.")
                else:
                    sucursales[nombre_suc] = {"lat": lat_suc, "lon": lon_suc}
                    save_sucursales(sucursales)
                    refresh_sucursales()
                    st.success(f"Sucursal **{nombre_suc}** guardada.")
                    st.rerun()

        st.divider()
        st.subheader("Sucursales registradas")
        sucursales = get_sucursales()
        if not sucursales:
            st.info("No hay sucursales registradas.")
        else:
            for nombre, coords in sucursales.items():
                c1, c2, c3 = st.columns([2, 4, 1])
                c1.write(f"**{nombre}**")
                c2.caption(f"{coords['lat']:.6f}, {coords['lon']:.6f}")
                if c3.button("Eliminar", key=f"del_suc_{nombre}"):
                    del sucursales[nombre]
                    save_sucursales(sucursales)
                    refresh_sucursales()
                    st.rerun()
