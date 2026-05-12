from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", os.getenv("TF_ENABLE_ONEDNN_OPTS", "0"))
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", os.getenv("TF_CPP_MIN_LOG_LEVEL", "2"))


ROOT_DIR = Path(__file__).resolve().parents[2]

SRC_DIR = ROOT_DIR / "src"

STORAGE_DIR = Path(
    os.getenv("STORAGE_DIR", str(ROOT_DIR / "storage"))
).resolve()

LOG_DIR = Path(
    os.getenv("LOG_DIR", str(ROOT_DIR / "logs"))
).resolve()

DATASET_DIR = STORAGE_DIR / "datasets"
MODEL_DIR = STORAGE_DIR / "models"
SCALER_DIR = STORAGE_DIR / "scalers"
FEATURE_DIR = STORAGE_DIR / "features"
REPORT_DIR = STORAGE_DIR / "reports"
TEMP_DIR = STORAGE_DIR / "temp"


APP_NAME = "Prediksi Jumlah Pengangguran Sulawesi Utara"
APP_SHORT_NAME = "Pengangguran LSTM"
APP_VERSION = "1.0.0"

PAGE_TITLE = "Prediksi Pengangguran Sulawesi Utara"
PAGE_ICON = "📊"
LAYOUT = "wide"


DEFAULT_SQLITE_PATH = STORAGE_DIR / "app.db"

_env_database_url = os.getenv("DATABASE_URL", "").strip()

if _env_database_url:
    DATABASE_URL = _env_database_url
else:
    DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
DEFAULT_ADMIN_FULL_NAME = os.getenv("DEFAULT_ADMIN_FULL_NAME", "Administrator")

AUTH_SECRET_KEY = os.getenv(
    "AUTH_SECRET_KEY",
    "default_secret_key_jangan_dipakai_di_production",
)

AUTH_TOKEN_EXPIRE_HOURS = int(os.getenv("AUTH_TOKEN_EXPIRE_HOURS", "12"))
AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "pengangguran_admin_token")

YEAR_COLUMN = "Tahun"
TARGET_COLUMN = "Total_Pengangguran"

ALLOWED_EXTENSIONS = [".xlsx", ".xls", ".csv"]
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))


WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "5"))
TRAIN_RATIO = float(os.getenv("TRAIN_RATIO", "0.8"))

LSTM_UNITS = int(os.getenv("LSTM_UNITS", "32"))
DROPOUT_RATE = float(os.getenv("DROPOUT_RATE", "0.2"))

EPOCHS = int(os.getenv("EPOCHS", "300"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "4"))
VALIDATION_SPLIT = float(os.getenv("VALIDATION_SPLIT", "0.2"))

EARLY_STOPPING_PATIENCE = int(os.getenv("EARLY_STOPPING_PATIENCE", "30"))
CORRELATION_THRESHOLD = float(os.getenv("CORRELATION_THRESHOLD", "0.3"))

FUTURE_YEARS_DEFAULT = int(os.getenv("FUTURE_YEARS_DEFAULT", "5"))
FUTURE_YEARS_MIN = int(os.getenv("FUTURE_YEARS_MIN", "1"))
FUTURE_YEARS_MAX = int(os.getenv("FUTURE_YEARS_MAX", "20"))


MODEL_FILE_NAME = "model.keras"
SCALER_FILE_NAME = "scaler.joblib"
FEATURES_FILE_NAME = "features.json"
METRICS_FILE_NAME = "metrics.json"
TRAINING_CONFIG_FILE_NAME = "training_config.json"


def create_required_directories() -> None:
    folders = [
        STORAGE_DIR,
        LOG_DIR,
        DATASET_DIR,
        MODEL_DIR,
        SCALER_DIR,
        FEATURE_DIR,
        REPORT_DIR,
        TEMP_DIR,
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)


def is_allowed_file(filename: str) -> bool:
    if not filename:
        return False

    file_ext = Path(filename).suffix.lower()
    return file_ext in ALLOWED_EXTENSIONS


def get_storage_path() -> dict:
    return {
        "root": ROOT_DIR,
        "storage": STORAGE_DIR,
        "datasets": DATASET_DIR,
        "models": MODEL_DIR,
        "scalers": SCALER_DIR,
        "features": FEATURE_DIR,
        "reports": REPORT_DIR,
        "temp": TEMP_DIR,
        "logs": LOG_DIR,
    }