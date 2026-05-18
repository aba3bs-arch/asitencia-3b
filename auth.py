import hashlib
import streamlit as st
import streamlit.components.v1 as components

from storage import tiene_foto_referencia, load_empleados, save_empleados


def hash_pin(pin):
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


def buscar_empleado(empleado_id, empleados=None):
    empleado_id = empleado_id.strip()
    lista = empleados if empleados is not None else load_empleados()
    for emp in lista:
        if emp["id"] == empleado_id and emp.get("activo", True):
            return emp
    return None


def verificar_pin(empleado, pin):
    if not pin or not empleado.get("pin_hash"):
        return False
    return hash_pin(pin.strip()) == empleado["pin_hash"]


def actualizar_empleado(empleado_id, datos):
    empleados = load_empleados()
    for i, emp in enumerate(empleados):
        if emp["id"] == empleado_id:
            empleados[i] = {**emp, **datos}
            save_empleados(empleados)
            return True
    return False


def procesar_auth_url():
    """Lee resultado de huella (WebAuthn) desde la URL."""
    params = st.query_params
    if params.get("auth") != "bio":
        return None
    emp_id = params.get("emp", "")
    if not emp_id or not buscar_empleado(emp_id):
        return None
    st.session_state.empleado_autenticado = emp_id
    st.session_state.metodo_auth_usado = "huella"
    st.query_params.clear()
    return emp_id


def componente_huella(empleado_id, registrar=False):
    """WebAuthn: huella / Face ID en celulares compatibles (requiere HTTPS)."""
    modo = "register" if registrar else "login"
    texto_btn = "Registrar huella / Face ID" if registrar else "Verificar con huella / Face ID"
    html = f"""
    <div style="font-family:sans-serif;text-align:center;">
        <button id="btnBio" style="padding:12px 24px;font-size:16px;cursor:pointer;">
            {texto_btn}
        </button>
        <p id="status" style="color:#666;margin-top:8px;"></p>
    </div>
    <script>
    const empId = "{empleado_id}";
    const modo = "{modo}";
    const status = document.getElementById("status");
    const btn = document.getElementById("btnBio");

    function urlOk() {{
        const u = new URL(window.top.location.href);
        u.searchParams.set("auth", "bio");
        u.searchParams.set("emp", empId);
        window.top.location.href = u.toString();
    }}

    btn.onclick = async () => {{
        status.textContent = "Esperando sensor biométrico...";
        if (!window.PublicKeyCredential) {{
            status.textContent = "Tu navegador no soporta huella digital. Usa PIN o foto.";
            return;
        }}
        try {{
            if (modo === "register") {{
                await navigator.credentials.create({{
                    publicKey: {{
                        challenge: new Uint8Array(32),
                        rp: {{ name: "Abarrotes 3B" }},
                        user: {{
                            id: new TextEncoder().encode(empId),
                            name: empId,
                            displayName: empId
                        }},
                        pubKeyCredParams: [{{ type: "public-key", alg: -7 }}],
                        authenticatorSelection: {{
                            authenticatorAttachment: "platform",
                            userVerification: "required"
                        }},
                        timeout: 60000
                    }}
                }});
                status.textContent = "Huella registrada. Redirigiendo...";
            }} else {{
                await navigator.credentials.get({{
                    publicKey: {{
                        challenge: new Uint8Array(32),
                        timeout: 60000,
                        userVerification: "required"
                    }}
                }});
                status.textContent = "Verificado. Redirigiendo...";
            }}
            urlOk();
        }} catch (e) {{
            status.textContent = "Cancelado o no disponible: " + e.message;
        }}
    }};
    </script>
    """
    components.html(html, height=130)


def pantalla_login_empleado(get_empleados_fn):
    """Pantalla de identificación: ID + PIN, foto o huella."""
    procesar_auth_url()

    if st.session_state.get("empleado_autenticado"):
        return st.session_state.empleado_autenticado

    st.subheader("Identificación")
    id_emp = st.text_input("ID de empleado", placeholder="Ej: 001", key="login_id_emp")

    if not id_emp or not id_emp.strip():
        st.caption("Ingresa tu ID para ver tu método de acceso.")
        return None

    emp = buscar_empleado(id_emp.strip(), get_empleados_fn())
    if not emp:
        st.error("ID no registrado o inactivo.")
        return None

    metodo = emp.get("metodo_auth", "pin")
    st.caption(f"Método asignado: **{metodo.upper()}**")

    if metodo == "pin":
        pin = st.text_input("PIN", type="password", max_chars=8, key="login_pin")
        if st.button("Ingresar con PIN", type="primary", use_container_width=True):
            if verificar_pin(emp, pin):
                st.session_state.empleado_autenticado = emp["id"]
                st.session_state.metodo_auth_usado = "pin"
                st.rerun()
            else:
                st.error("PIN incorrecto.")

    elif metodo == "foto":
        if not tiene_foto_referencia(emp["id"]):
            st.warning("Sin foto de referencia. Pide al administrador que registre tu foto.")
        foto = st.camera_input("Toma tu foto para verificar identidad", key="login_foto")
        if st.button("Ingresar con foto", type="primary", use_container_width=True, disabled=foto is None):
            if foto is None:
                st.error("Debes tomar una foto.")
            else:
                st.session_state.empleado_autenticado = emp["id"]
                st.session_state.metodo_auth_usado = "foto"
                st.session_state.foto_login_bytes = foto.getvalue()
                st.rerun()

    elif metodo == "huella":
        st.caption("Usa el sensor de huella o Face ID de tu celular.")
        if not emp.get("huella_registrada"):
            st.info("Primera vez: registra tu huella con el botón de abajo.")
            componente_huella(emp["id"], registrar=True)
            if st.button("Confirmar registro de huella", key="confirm_huella_reg"):
                actualizar_empleado(emp["id"], {"huella_registrada": True})
                st.session_state.empleado_autenticado = emp["id"]
                st.session_state.metodo_auth_usado = "huella"
                st.rerun()
        else:
            componente_huella(emp["id"], registrar=False)

    return None
