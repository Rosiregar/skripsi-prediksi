from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


from src.auth.auth_service import ensure_default_admin
from src.config.settings import (
    DATABASE_URL,
    ROOT_DIR,
    STORAGE_DIR,
    DATASET_DIR,
    MODEL_DIR,
    SCALER_DIR,
    FEATURE_DIR,
    REPORT_DIR,
    TEMP_DIR,
    LOG_DIR,
    create_required_directories,
)
from src.database.connection import create_tables, test_database_connection


def check_folder(path: Path) -> None:
    if path.exists():
        print(f"[OK] Folder ada: {path}")
    else:
        print(f"[ERROR] Folder tidak ada: {path}")


def main() -> None:
    print("Mengecek proyek Pengangguran LSTM")
    print("-" * 50)

    print(f"Project dir : {PROJECT_DIR}")
    print(f"Root config : {ROOT_DIR}")
    print(f"Database    : {DATABASE_URL}")
    print("-" * 50)

    create_required_directories()

    folders = [
        STORAGE_DIR,
        DATASET_DIR,
        MODEL_DIR,
        SCALER_DIR,
        FEATURE_DIR,
        REPORT_DIR,
        TEMP_DIR,
        LOG_DIR,
    ]

    for folder in folders:
        check_folder(folder)

    print("-" * 50)

    test_database_connection()
    print("[OK] Koneksi database aman")

    create_tables()
    print("[OK] Tabel database aman")

    admin = ensure_default_admin()
    print(f"[OK] Admin default tersedia: {admin['username']}")

    print("-" * 50)

    from src.ui.admin_login import render_admin_login_page
    from src.ui.admin_dashboard import render_admin_dashboard_page
    from src.ui.admin_dataset import render_admin_dataset_page
    from src.ui.user_dataset import render_user_dataset_page
    from src.ui.user_results import render_user_results_page

    print("[OK] Import halaman ringan aman")

    from src.ml.lstm_service import train_lstm_pipeline

    print("[OK] Import LSTM service aman")

    print("-" * 50)
    print("Project check selesai. Semua bagian utama aman.")


if __name__ == "__main__":
    main()