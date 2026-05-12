"""
Inisialisasi database aplikasi Prediksi Jumlah Pengangguran Sulawesi Utara.

File ini digunakan untuk:
- membuat tabel database,
- membuat admin default,
- mengecek koneksi database,
- menampilkan ringkasan isi database.

File ini bisa dijalankan langsung dari terminal:

    python -m src.database.init_db
"""

from sqlalchemy import func, select

from src.auth.auth_service import ensure_default_admin
from src.database.connection import (
    create_tables,
    db_session,
    drop_tables,
    test_database_connection,
)
from src.database.models import (
    Admin,
    AdminActivityLog,
    Dataset,
    DatasetRow,
    FuturePrediction,
    ModelArtifact,
    ModelEvaluation,
    ModelTraining,
    TestPrediction,
    UserPredictionDetail,
    UserPredictionJob,
)


def initialize_database() -> None:
    """
    Membuat tabel database dan admin default.

    Fungsi ini aman dijalankan berkali-kali.
    Jika tabel sudah ada, tabel tidak akan dibuat ulang.
    Jika admin default sudah ada, admin tidak akan dibuat ulang.
    """

    print("Memulai inisialisasi database...")

    test_database_connection()
    print("Koneksi database berhasil.")

    create_tables()
    print("Tabel database berhasil dibuat atau sudah tersedia.")

    admin = ensure_default_admin()
    print(f"Admin default tersedia: {admin['username']}")

    print("Inisialisasi database selesai.")


def count_table_rows(model_class) -> int:
    """
    Menghitung jumlah data pada sebuah tabel.

    Parameters
    ----------
    model_class
        Class model SQLAlchemy.

    Returns
    -------
    int
        Jumlah baris pada tabel.
    """

    with db_session() as session:
        statement = select(func.count()).select_from(model_class)
        total = session.execute(statement).scalar_one()

    return int(total)


def get_database_summary() -> dict:
    """
    Mengambil ringkasan jumlah data pada setiap tabel utama.

    Returns
    -------
    dict
        Dictionary berisi nama tabel dan jumlah datanya.
    """

    return {
        "admins": count_table_rows(Admin),
        "datasets": count_table_rows(Dataset),
        "dataset_rows": count_table_rows(DatasetRow),
        "model_trainings": count_table_rows(ModelTraining),
        "model_artifacts": count_table_rows(ModelArtifact),
        "model_evaluations": count_table_rows(ModelEvaluation),
        "test_predictions": count_table_rows(TestPrediction),
        "future_predictions": count_table_rows(FuturePrediction),
        "user_prediction_jobs": count_table_rows(UserPredictionJob),
        "user_prediction_details": count_table_rows(UserPredictionDetail),
        "admin_activity_logs": count_table_rows(AdminActivityLog),
    }


def print_database_summary() -> None:
    """
    Menampilkan ringkasan jumlah data database ke terminal.
    """

    summary = get_database_summary()

    print("\nRingkasan Database")
    print("-" * 40)

    for table_name, total_rows in summary.items():
        print(f"{table_name}: {total_rows}")

    print("-" * 40)


def reset_database_for_development(confirm: bool = False) -> None:
    """
    Menghapus dan membuat ulang seluruh tabel database.

    Fungsi ini hanya untuk development.
    Jangan gunakan fungsi ini di production.

    Parameters
    ----------
    confirm : bool
        Harus True agar database benar-benar direset.
    """

    if not confirm:
        raise ValueError(
            "Reset database dibatalkan. "
            "Gunakan confirm=True jika benar-benar ingin reset database."
        )

    print("Menghapus seluruh tabel database...")
    drop_tables(confirm=True)

    print("Membuat ulang database...")
    initialize_database()


if __name__ == "__main__":
    initialize_database()
    print_database_summary()