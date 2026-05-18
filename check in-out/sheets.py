import streamlit as st

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = [
    "ID", "Fecha", "Hora", "Empleado ID", "Nombre",
    "Tipo", "Sucursal", "Latitud", "Longitud",
]


def sheets_configurado():
    try:
        return (
            "gcp_service_account" in st.secrets
            and "GOOGLE_SHEET_ID" in st.secrets
        )
    except (FileNotFoundError, AttributeError):
        return False


def _cliente():
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def _hoja():
    import gspread

    gc = _cliente()
    libro = gc.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
    nombre_hoja = st.secrets.get("GOOGLE_SHEET_TAB", "Asistencia")
    try:
        return libro.worksheet(nombre_hoja)
    except gspread.exceptions.WorksheetNotFound:
        return libro.add_worksheet(title=nombre_hoja, rows=1000, cols=10)


def _asegurar_encabezados(ws):
    if not ws.row_values(1):
        ws.append_row(HEADERS, value_input_option="USER_ENTERED")


def fila_desde_registro(reg):
    return [
        reg["id"],
        reg["fecha"],
        reg["hora"],
        reg["empleado_id"],
        reg.get("empleado_nombre", ""),
        reg["tipo"],
        reg["tienda"],
        reg["lat"],
        reg["lon"],
    ]


def enviar_registro(reg):
    if not sheets_configurado():
        return False, "Google Sheets no está configurado en Secrets."
    try:
        ws = _hoja()
        _asegurar_encabezados(ws)
        ws.append_row(fila_desde_registro(reg), value_input_option="USER_ENTERED")
        return True, None
    except Exception as e:
        return False, str(e)


def enviar_registros(registros):
    if not sheets_configurado():
        return 0, "Google Sheets no está configurado en Secrets."
    try:
        ws = _hoja()
        _asegurar_encabezados(ws)
        filas = [fila_desde_registro(r) for r in registros]
        if filas:
            ws.append_rows(filas, value_input_option="USER_ENTERED")
        return len(filas), None
    except Exception as e:
        return 0, str(e)
