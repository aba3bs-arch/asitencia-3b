# --- Agrégalo al principio del archivo con los otros import ---
from streamlit_js_eval import get_geolocation

# --- Reemplaza la SECCIÓN 1 (PORTAL DEL EMPLEADO) con esto ---
if menu == "📱 REGISTRO EMPLEADO":
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        st.title("Asistencia Las 3B")
        
        id_emp = st.text_input("🆔 ID de Empleado", placeholder="Ejemplo: 015")
        
        # OBTENER UBICACIÓN REAL
        loc = get_geolocation()
        
        if loc:
            lat_gps = loc['coords']['latitude']
            lon_gps = loc['coords']['longitude']
            
            tienda_detectada = None
            for nombre, coords in SUCURSALES.items():
                dist = geodesic((lat_gps, lon_gps), (coords['lat'], coords['lon'])).meters
                if dist <= RADIO_PERMITIDO_METROS:
                    tienda_detectada = nombre
                    break

            if tienda_detectada:
                st.success(f"✅ UBICACIÓN: Sucursal {tienda_detectada}")
                if st.button("REGISTRAR ENTRADA / SALIDA"):
                    if id_emp:
                        st.balloons()
                        st.success(f"¡Registro Exitoso para ID {id_emp}!")
                    else:
                        st.warning("⚠️ Ingresa tu ID antes de checar.")
            else:
                st.error("❌ FUERA DE RANGO. No estás en ninguna sucursal.")
        else:
            st.warning("📡 Esperando señal de GPS... Asegúrate de dar permiso de ubicación en tu celular.")
