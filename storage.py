import json
from pathlib import Path

from config import SUCURSALES as SUCURSALES_DEFAULT

DATA_DIR = Path(__file__).parent / "data"
EMPLEADOS_FILE = DATA_DIR / "empleados.json"
SUCURSALES_FILE = DATA_DIR / "sucursales.json"


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
