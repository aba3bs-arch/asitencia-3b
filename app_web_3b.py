import hashlib
import uuid
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from geopy.distance import geodesic
import pandas as pd
import datetime

from config import RADIO_PERMITIDO_METROS
from storage import (
    load_empleados,
    save_empleados,
    load_sucursales,
    save_sucursales,
    load_administradores,
    save_administradores,
    load_registros,
    save_registros,
    agregar_registro,
)
from sheets import sheets_configurado, enviar_registro, enviar_registros
from auth import hash_pin, pantalla_login_empleado, buscar_empleado
from storage import guardar_foto_referencia, guardar_foto_checado


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


def get_registros():
    if "registros" not in st.session_state:
        st.session_state.registros = load_registros()
    return st.session_state.registros


def refresh_registros():
    st.session_state.registros = load_registros()


def nombre_empleado(empleado_id):
    for emp in get_empleados():
        if emp["id"] == empleado_id:
            return emp["nombre"]
    return empleado_id


def siguiente_tipo(empleado_id):
    del_empleado = [r for r in get_registros() if r["empleado_id"] == empleado_id]
    if not del_empleado:
        return "entrada"
    ultimo = max(del_empleado, key=lambda r: r["datetime"])
    return "salida" if ultimo["tipo"] == "entrada" else "entrada"


def registros_del_dia(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    return [r for r in get_registros() if r["fecha"] == fecha]


def registrar_checado(empleado_id, tienda, lat, lon, metodo_auth=None, foto_bytes=None):
    ahora = datetime.datetime.now()
    tipo = siguiente_tipo(empleado_id)
    registro = {
        "id": str(uuid.uuid4()),
        "fecha": ahora.date().isoformat(),
        "hora": ahora.strftime("%H:%M:%S"),
        "datetime": ahora.isoformat(),
        "empleado_id": empleado_id,
        "empleado_nombre": nombre_empleado(empleado_id),
        "tipo": tipo,
        "tienda": tienda,
        "lat": lat,
        "lon": lon,
        "metodo_auth": metodo_auth or "",
        "sheets_synced": False,
    }
    if foto_bytes:
        guardar_foto_checado(registro["id"], foto_bytes)
        registro["tiene_foto"] = True
    agregar_registro(registro)
    refresh_registros()

    if sheets_configurado():
        ok, err = enviar_registro(registro)
        if ok:
            registros = load_registros()
            for r in registros:
                if r["id"] == registro["id"]:
                    r["sheets_synced"] = True
            save_registros(registros)
            refresh_registros()
            registro["sheets_synced"] = True
        else:
            registro["sheets_error"] = err

    return registro


def sincronizar_pendientes_sheets():
    pendientes = [r for r in get_registros() if not r.get("sheets_synced")]
    if not pendientes:
        return 0, None
    count, err = enviar_registros(pendientes)
    if err:
        return 0, err
    registros = load_registros()
    ids_ok = {p["id"] for p in pendientes[:count]}
    for r in registros:
        if r["id"] in ids_ok:
            r["sheets_synced"] = True
    save_registros(registros)
    refresh_registros()
    return count, None


def get_administradores():
    if "administradores" not in st.session_state:
        st.session_state.administradores = load_administradores()
    return st.session_state.administradores


def refresh_administradores():
    st.session_state.administradores = load_administradores()


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def password_inicial():
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError, AttributeError):
        return "3b_admin"


def init_administradores():
    admins = load_administradores()
    if not admins:
        admins = [{
            "usuario": "admin",
            "nombre": "Administrador principal",
            "password_hash": hash_password(password_inicial()),
            "activo": True,
        }]
        save_administradores(admins)
        refresh_administradores()
    return admins


def admin_logueado():
    return st.session_state.get("admin_usuario")


def login_admin(usuario, password):
    init_administradores()
    usuario = usuario.strip().lower()
    for adm in get_administradores():
        if adm["usuario"] == usuario and adm.get("activo", True):
            if hash_password(password) == adm["password_hash"]:
                st.session_state.admin_usuario = adm["usuario"]
                st.session_state.admin_nombre = adm["nombre"]
                return True
    return False


def logout_admin():
    st.session_state.pop("admin_usuario", None)
    st.session_state.pop("admin_nombre", None)


def sucursal_mas_cercana(lat, lon, sucursales):
    mejor = None
    for nombre, coords in sucursales.items():
        dist = geodesic((lat, lon), (coords["lat"], coords["lon"])).meters
        if mejor is None or dist < mejor[1]:
            mejor = (nombre, dist)
    return mejor


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

    if "empleado_autenticado" not in st.session_state:
        st.session_state.empleado_autenticado = None

    id_autenticado = pantalla_login_empleado(get_empleados)
    if not id_autenticado:
        st.stop()

    id_str = id_autenticado
    st.success(f"Hola, **{nombre_empleado(id_str)}**")
    if st.button("Cerrar sesión", key="logout_emp"):
        for key in ("empleado_autenticado", "metodo_auth_usado", "foto_login_bytes"):
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    sucursales = get_sucursales()
    if not sucursales:
        st.error("No hay sucursales configuradas. Contacta al administrador.")
        st.stop()

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
            tipo_siguiente = siguiente_tipo(id_str)
            st.info(f"Próximo registro: **{tipo_siguiente.upper()}**")
            if st.button(f"REGISTRAR {tipo_siguiente.upper()}"):
                foto_bytes = st.session_state.pop("foto_login_bytes", None)
                reg = registrar_checado(
                    id_str,
                    tienda_detectada,
                    lat_gps,
                    lon_gps,
                    metodo_auth=st.session_state.get("metodo_auth_usado"),
                    foto_bytes=foto_bytes,
                )
                st.balloons()
                msg = f"**{reg['tipo'].upper()}** registrada a las {reg['hora']} — {reg['tienda']}"
                if reg.get("sheets_synced"):
                    msg += " (guardado en Google Sheets)"
                elif reg.get("sheets_error"):
                    msg += f" — Sheets pendiente: {reg['sheets_error']}"
                st.success(msg)
        else:
            st.error(
                f"❌ FUERA DE RANGO. Estás a **{dist_cercana:.0f} m** de {nombre_cercana} "
                f"(máximo permitido: {RADIO_PERMITIDO_METROS} m)."
            )

# ---------------------------------------------------------
# PANEL ADMINISTRADOR
# ---------------------------------------------------------
elif menu == "PANEL ADMINISTRADOR":
    init_administradores()

    st.sidebar.subheader("Acceso administrador")
    if not admin_logueado():
        usuario_login = st.sidebar.text_input("Usuario")
        clave_login = st.sidebar.text_input("Contraseña", type="password")
        if st.sidebar.button("Iniciar sesión", type="primary"):
            if login_admin(usuario_login, clave_login):
                st.rerun()
            else:
                st.sidebar.error("Usuario o contraseña incorrectos.")
        st.warning("Inicia sesión con tu usuario de administrador.")
        st.caption(
            "Primer acceso: usuario **admin** y la contraseña definida en Secrets "
            "(o `3b_admin` en local)."
        )
        st.stop()

    st.sidebar.success(f"Sesión: **{st.session_state.admin_nombre}**")
    if st.sidebar.button("Cerrar sesión"):
        logout_admin()
        st.rerun()

    tab_mon, tab_rep, tab_emp, tab_suc, tab_adm = st.tabs(
        ["Monitoreo", "Reporte diario", "Empleados", "Sucursales", "Administradores"]
    )

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

        hoy_mapa = registros_del_dia()
        for reg in hoy_mapa:
            folium.Marker(
                location=[reg["lat"], reg["lon"]],
                icon=folium.DivIcon(html='<div class="pulse"></div>'),
                popup=(
                    f"{reg['empleado_nombre']} — {reg['tipo'].upper()} "
                    f"@ {reg['tienda']} ({reg['hora']})"
                ),
            ).add_to(m)

        st_folium(m, width="100%", height=500)
        st.caption(f"Marcadores del día: {len(hoy_mapa)} registro(s).")

    with tab_rep:
        hoy = datetime.date.today()
        st.subheader(f"Reporte del {hoy.strftime('%d/%m/%Y')}")
        registros_hoy = registros_del_dia(hoy.isoformat())

        if not registros_hoy:
            st.info("No hay entradas ni salidas registradas hoy.")
        else:
            entradas = sum(1 for r in registros_hoy if r["tipo"] == "entrada")
            salidas = sum(1 for r in registros_hoy if r["tipo"] == "salida")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total registros", len(registros_hoy))
            c2.metric("Entradas", entradas)
            c3.metric("Salidas", salidas)

            df = pd.DataFrame(registros_hoy).sort_values("datetime", ascending=False)
            df_show = df[["hora", "empleado_id", "empleado_nombre", "tipo", "tienda"]].copy()
            df_show.columns = ["Hora", "ID", "Nombre", "Tipo", "Sucursal"]
            df_show["Tipo"] = df_show["Tipo"].str.upper()
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            csv = df_show.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Descargar CSV del día",
                csv,
                file_name=f"asistencia_{hoy.isoformat()}.csv",
                mime="text/csv",
            )

        st.divider()
        st.subheader("Google Sheets")
        if sheets_configurado():
            pendientes = [r for r in get_registros() if not r.get("sheets_synced")]
            st.caption(f"Registros pendientes de sincronizar: **{len(pendientes)}**")
            if st.button("Sincronizar pendientes con Google Sheets", type="primary"):
                count, err = sincronizar_pendientes_sheets()
                if err:
                    st.error(f"Error al sincronizar: {err}")
                elif count == 0:
                    st.info("No hay registros pendientes.")
                else:
                    st.success(f"Se enviaron **{count}** registro(s) a Google Sheets.")
                    st.rerun()
        else:
            st.warning(
                "Google Sheets no configurado. Agrega `gcp_service_account` y "
                "`GOOGLE_SHEET_ID` en Secrets (ver `.streamlit/secrets.toml.example`)."
            )

    # --- Empleados ---
    with tab_emp:
        st.subheader("Registrar empleado")
        col1, col2 = st.columns(2)
        with col1:
            nuevo_id = st.text_input("ID de empleado", placeholder="Ej: 001", key="new_emp_id")
        with col2:
            nuevo_nombre = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez", key="new_emp_nom")

        metodo_auth = st.selectbox(
            "Método de acceso",
            ["pin", "foto", "huella"],
            format_func=lambda x: {"pin": "PIN", "foto": "Foto", "huella": "Huella / Face ID"}[x],
            key="new_emp_metodo",
        )

        nuevo_pin = ""
        foto_referencia = None
        if metodo_auth == "pin":
            nuevo_pin = st.text_input("PIN (4-8 dígitos)", type="password", max_chars=8, key="new_emp_pin")
        elif metodo_auth == "foto":
            foto_referencia = st.camera_input("Foto de referencia del empleado", key="new_emp_foto")
        else:
            st.caption("El empleado registrará su huella en el primer acceso desde su celular.")

        if st.button("Guardar empleado", type="primary", key="btn_save_emp"):
            nuevo_id = nuevo_id.strip()
            nuevo_nombre = nuevo_nombre.strip()
            if not nuevo_id or not nuevo_nombre:
                st.error("ID y nombre son obligatorios.")
            elif metodo_auth == "pin" and (not nuevo_pin or len(nuevo_pin) < 4):
                st.error("El PIN debe tener entre 4 y 8 dígitos.")
            elif metodo_auth == "foto" and foto_referencia is None:
                st.error("Toma la foto de referencia del empleado.")
            else:
                empleados = get_empleados()
                if any(e["id"] == nuevo_id for e in empleados):
                    st.error(f"Ya existe un empleado con ID **{nuevo_id}**.")
                else:
                    emp_nuevo = {
                        "id": nuevo_id,
                        "nombre": nuevo_nombre,
                        "activo": True,
                        "metodo_auth": metodo_auth,
                    }
                    if metodo_auth == "pin":
                        emp_nuevo["pin_hash"] = hash_pin(nuevo_pin)
                    if metodo_auth == "huella":
                        emp_nuevo["huella_registrada"] = False
                    empleados.append(emp_nuevo)
                    save_empleados(empleados)
                    if metodo_auth == "foto" and foto_referencia:
                        guardar_foto_referencia(nuevo_id, foto_referencia.getvalue())
                    refresh_empleados()
                    st.success(f"Empleado **{nuevo_nombre}** registrado ({metodo_auth.upper()}).")
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
                metodo = emp.get("metodo_auth", "pin").upper()
                c1.write(f"**{emp['id']}**")
                c2.write(f"{emp['nombre']} — _{estado}_ — {metodo}")
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

    # --- Administradores ---
    with tab_adm:
        st.subheader("Registrar administrador")
        with st.form("form_admin", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nuevo_usuario = st.text_input("Usuario", placeholder="Ej: maria.garcia")
            with c2:
                nuevo_nombre_adm = st.text_input("Nombre completo", placeholder="Ej: María García")
            c3, c4 = st.columns(2)
            with c3:
                nueva_clave = st.text_input("Contraseña", type="password")
            with c4:
                confirmar_clave = st.text_input("Confirmar contraseña", type="password")
            guardar_adm = st.form_submit_button("Guardar administrador", type="primary")

        if guardar_adm:
            nuevo_usuario = nuevo_usuario.strip().lower()
            nuevo_nombre_adm = nuevo_nombre_adm.strip()
            if not nuevo_usuario or not nuevo_nombre_adm:
                st.error("Usuario y nombre son obligatorios.")
            elif len(nueva_clave) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            elif nueva_clave != confirmar_clave:
                st.error("Las contraseñas no coinciden.")
            else:
                admins = get_administradores()
                if any(a["usuario"] == nuevo_usuario for a in admins):
                    st.error(f"Ya existe el usuario **{nuevo_usuario}**.")
                else:
                    admins.append({
                        "usuario": nuevo_usuario,
                        "nombre": nuevo_nombre_adm,
                        "password_hash": hash_password(nueva_clave),
                        "activo": True,
                    })
                    save_administradores(admins)
                    refresh_administradores()
                    st.success(f"Administrador **{nuevo_nombre_adm}** registrado.")
                    st.rerun()

        st.divider()
        st.subheader("Administradores del sistema")
        admins = get_administradores()
        for adm in admins:
            c1, c2, c3 = st.columns([2, 3, 1])
            estado = "Activo" if adm.get("activo", True) else "Inactivo"
            c1.write(f"**{adm['usuario']}**")
            c2.write(f"{adm['nombre']} — _{estado}_")
            es_yo = adm["usuario"] == admin_logueado()
            if c3.button("Eliminar", key=f"del_adm_{adm['usuario']}", disabled=es_yo):
                if len(admins) <= 1:
                    st.error("Debe existir al menos un administrador.")
                else:
                    admins = [a for a in admins if a["usuario"] != adm["usuario"]]
                    save_administradores(admins)
                    refresh_administradores()
                    st.rerun()
            if es_yo:
                c3.caption("Tú")
