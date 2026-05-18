import json
from pathlib import Path

try:
    from config import SUCURSALES as SUCURSALES_DEFAULT
except ImportError:
    SUCURSALES_DEFAULT = {
        "Fusión": {"lat": 31.320189, "lon": -110.943909},
        "3B2": {"lat": 31.300544, "lon": -110.923907},
        "3B3": {"lat": 31.300544, "lon": -110.936193},
        "3B5": {"lat": 31.289624, "lon": -110.931254},
        "3B6": {"lat": 31.294967, "lon": -110.915074},
        "3B7": {"lat": 31.309213, "lon": -110.930617},
        "3B9": {"lat": 31.329842, "lon": -110.943361},
        "3B10": {"lat": 31.30125, "lon": -110.937966},
    }

DATA_DIR = Path(__file__).parent / "data"
FOTOS_DIR = DATA_DIR / "fotos"
CHECADOS_FOTOS_DIR = DATA_DIR / "fotos_checados"
EMPLEADOS_FILE = DATA_DIR / "empleados.json"
SUCURSALES_FILE = DATA_DIR / "sucursales.json"
ADMINISTRADORES_FILE = DATA_DIR / "administradores.json"
REGISTROS_FILE = DATA_DIR / "registros.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def load_empleados():
    _ensure_data_dir()
    if not EMPLEADOS_FILE.exists():
        return []
    with open(EMPLEADOS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_empleados(empleados):
    _ensure_data_dir()
    with open(EMPLEADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(empleados, f, ensure_ascii=False, indent=2)


def load_sucursales():
    _ensure_data_dir()
    if not SUCURSALES_FILE.exists():
        save_sucursales(dict(SUCURSALES_DEFAULT))
        return dict(SUCURSALES_DEFAULT)
    with open(SUCURSALES_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_sucursales(sucursales):
    _ensure_data_dir()
    with open(SUCURSALES_FILE, "w", encoding="utf-8") as f:
        json.dump(sucursales, f, ensure_ascii=False, indent=2)


def load_administradores():
    _ensure_data_dir()
    if not ADMINISTRADORES_FILE.exists():
        return []
    with open(ADMINISTRADORES_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_administradores(administradores):
    _ensure_data_dir()
    with open(ADMINISTRADORES_FILE, "w", encoding="utf-8") as f:
        json.dump(administradores, f, ensure_ascii=False, indent=2)


def load_registros():
    _ensure_data_dir()
    if not REGISTROS_FILE.exists():
        return []
    with open(REGISTROS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_registros(registros):
    _ensure_data_dir()
    with open(REGISTROS_FILE, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)


def agregar_registro(registro):
    registros = load_registros()
    registros.append(registro)
    save_registros(registros)
    return registro


def guardar_foto_referencia(empleado_id, image_bytes):
    FOTOS_DIR.mkdir(parents=True, exist_ok=True)
    (FOTOS_DIR / f"{empleado_id}.jpg").write_bytes(image_bytes)


def tiene_foto_referencia(empleado_id):
    return (FOTOS_DIR / f"{empleado_id}.jpg").exists()


def guardar_foto_checado(registro_id, image_bytes):
    CHECADOS_FOTOS_DIR.mkdir(parents=True, exist_ok=True)
    (CHECADOS_FOTOS_DIR / f"{registro_id}.jpg").write_bytes(image_bytes)
