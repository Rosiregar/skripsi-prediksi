"""
Service pengelolaan dataset.

File ini bertanggung jawab untuk:
- menyimpan dataset hasil upload,
- menyimpan metadata dataset ke database,
- menyimpan isi dataset ke tabel dataset_rows,
- mengambil dataset aktif,
- mengambil dataset published,
- mengubah dataset menjadi aktif/published.

Dataset resmi admin disimpan dalam dua bentuk:
1. File Excel bersih di storage/datasets.
2. Data baris di tabel dataset_rows untuk ditampilkan ke user.

Pada production, folder storage dapat diarahkan ke persistent storage
melalui konfigurasi STORAGE_DIR di file .env.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
import re
import uuid

import numpy as np
import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.config.settings import (
    APP_ENV,
    DATASET_DIR,
    TARGET_COLUMN,
    YEAR_COLUMN,
    create_required_directories,
)
from src.database.connection import db_session
from src.database.models import AdminActivityLog, Dataset, DatasetRow
from src.utils.file_validator import (
    DatasetValidationResult,
    validate_and_read_dataset,
    validate_dataset,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_filename(filename: str) -> str:
    """
    Membersihkan nama file agar aman disimpan.

    Contoh:
        "Dataset Pengangguran Sulut.xlsx"
        menjadi
        "Dataset_Pengangguran_Sulut.xlsx"
    """

    filename = Path(filename).name
    filename = filename.strip()
    filename = re.sub(r"[^\w\-.]+", "_", filename)
    filename = re.sub(r"_+", "_", filename)

    if not filename:
        filename = "dataset.xlsx"

    return filename


def generate_stored_filename(original_filename: str) -> str:
    """
    Membuat nama file unik untuk disimpan di storage/datasets.

    File yang disimpan selalu menggunakan format .xlsx agar konsisten
    setelah dataset dibersihkan.
    """

    safe_name = clean_filename(original_filename)
    stem = Path(safe_name).stem

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]

    return f"{timestamp}_{unique_id}_{stem}.xlsx"


def to_python_value(value):
    """
    Mengubah nilai pandas/numpy agar aman disimpan dalam JSON database.
    """

    if pd.isna(value):
        return None

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def dataframe_row_to_json(
    row: pd.Series,
    year_column: str = YEAR_COLUMN,
) -> dict:
    """
    Mengubah satu baris dataframe menjadi dictionary JSON.

    Kolom Tahun tidak dimasukkan ke values_json karena sudah disimpan
    pada field tahun di tabel dataset_rows.
    """

    values = {}

    for column, value in row.items():
        if column == year_column:
            continue

        values[column] = to_python_value(value)

    return values


def dataset_to_dict(dataset: Dataset) -> dict:
    """
    Mengubah object Dataset menjadi dictionary.
    """

    return {
        "id": dataset.id,
        "dataset_name": dataset.dataset_name,
        "original_filename": dataset.original_filename,
        "stored_filename": dataset.stored_filename,
        "storage_path": dataset.storage_path,
        "uploaded_by": dataset.uploaded_by,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "year_column": dataset.year_column,
        "target_column": dataset.target_column,
        "start_year": dataset.start_year,
        "end_year": dataset.end_year,
        "is_active": dataset.is_active,
        "is_published": dataset.is_published,
        "uploaded_at": dataset.uploaded_at,
    }


def save_dataframe_to_storage(
    df: pd.DataFrame,
    stored_filename: str,
) -> Path:
    """
    Menyimpan dataframe bersih ke folder storage/datasets dalam format Excel.
    """

    create_required_directories()

    output_path = DATASET_DIR / stored_filename
    df.to_excel(output_path, index=False)

    return output_path


def log_admin_activity(
    session: Session,
    admin_id: Optional[int],
    activity_type: str,
    description: Optional[str] = None,
) -> None:
    """
    Mencatat aktivitas admin ke database.
    """

    activity_log = AdminActivityLog(
        admin_id=admin_id,
        activity_type=activity_type,
        description=description,
    )

    session.add(activity_log)


# ============================================================
# DATASET SAVE FUNCTIONS
# ============================================================

def deactivate_other_datasets(session: Session) -> None:
    """
    Menonaktifkan semua dataset lain.

    Hanya satu dataset yang dijadikan dataset aktif.
    """

    datasets = session.execute(select(Dataset)).scalars().all()

    for dataset in datasets:
        dataset.is_active = False


def unpublish_other_datasets(session: Session) -> None:
    """
    Mengubah semua dataset lain menjadi tidak published.

    Hanya satu dataset yang dijadikan dataset published utama.
    """

    datasets = session.execute(select(Dataset)).scalars().all()

    for dataset in datasets:
        dataset.is_published = False


def save_dataset_from_dataframe(
    df: pd.DataFrame,
    original_filename: str,
    dataset_name: Optional[str] = None,
    uploaded_by: Optional[int] = None,
    make_active: bool = True,
    publish: bool = False,
) -> dict:
    """
    Menyimpan dataframe dataset yang sudah valid ke storage dan database.

    Fungsi ini digunakan untuk:
    - upload dataset admin,
    - testing lokal,
    - import dataset dari sumber lain.
    """

    validation_result = validate_dataset(df)

    if not validation_result.is_valid:
        raise ValueError(
            "Dataset tidak valid: "
            + "; ".join(validation_result.errors)
        )

    cleaned_df = validation_result.dataframe

    if cleaned_df is None:
        raise ValueError("Dataset tidak valid atau kosong.")

    summary = validation_result.summary

    stored_filename = generate_stored_filename(original_filename)
    storage_path = save_dataframe_to_storage(cleaned_df, stored_filename)

    if not dataset_name:
        dataset_name = Path(original_filename).stem

    with db_session() as session:
        if make_active:
            deactivate_other_datasets(session)

        if publish:
            unpublish_other_datasets(session)

        dataset = Dataset(
            dataset_name=dataset_name,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=str(storage_path),
            uploaded_by=uploaded_by,
            row_count=summary["row_count"],
            column_count=summary["column_count"],
            year_column=YEAR_COLUMN,
            target_column=TARGET_COLUMN,
            start_year=summary["start_year"],
            end_year=summary["end_year"],
            is_active=make_active,
            is_published=publish,
        )

        session.add(dataset)
        session.flush()

        for _, row in cleaned_df.iterrows():
            dataset_row = DatasetRow(
                dataset_id=dataset.id,
                tahun=int(row[YEAR_COLUMN]),
                values_json=dataframe_row_to_json(row),
            )

            session.add(dataset_row)

        if uploaded_by is not None:
            log_admin_activity(
                session=session,
                admin_id=uploaded_by,
                activity_type="UPLOAD_DATASET",
                description=(
                    f"Dataset '{dataset_name}' berhasil diupload "
                    f"dengan {summary['row_count']} baris data."
                ),
            )

        session.flush()
        saved_dataset = dataset_to_dict(dataset)

    return {
        "dataset": saved_dataset,
        "summary": summary,
        "warnings": validation_result.warnings,
    }


def save_uploaded_dataset(
    file_obj,
    filename: Optional[str] = None,
    dataset_name: Optional[str] = None,
    uploaded_by: Optional[int] = None,
    make_active: bool = True,
    publish: bool = False,
) -> dict:
    """
    Membaca, memvalidasi, dan menyimpan dataset dari file upload.

    Fungsi ini dipakai pada halaman upload dataset admin.
    """

    if filename is None:
        filename = getattr(file_obj, "name", None)

    if not filename:
        raise ValueError("Nama file tidak ditemukan.")

    validation_result: DatasetValidationResult = validate_and_read_dataset(
        file_obj=file_obj,
        filename=filename,
    )

    if not validation_result.is_valid:
        raise ValueError(
            "Dataset tidak valid: "
            + "; ".join(validation_result.errors)
        )

    if validation_result.dataframe is None:
        raise ValueError("Dataset kosong atau gagal dibaca.")

    return save_dataset_from_dataframe(
        df=validation_result.dataframe,
        original_filename=filename,
        dataset_name=dataset_name,
        uploaded_by=uploaded_by,
        make_active=make_active,
        publish=publish,
    )


# ============================================================
# DATASET QUERY FUNCTIONS
# ============================================================

def list_datasets(limit: int = 50) -> list[dict]:
    """
    Mengambil daftar dataset terbaru.
    """

    with db_session() as session:
        statement = (
            select(Dataset)
            .order_by(desc(Dataset.uploaded_at))
            .limit(limit)
        )

        datasets = session.execute(statement).scalars().all()

        return [dataset_to_dict(dataset) for dataset in datasets]


def get_dataset_by_id(dataset_id: int) -> Optional[dict]:
    """
    Mengambil metadata dataset berdasarkan ID.
    """

    with db_session() as session:
        dataset = session.get(Dataset, dataset_id)

        if not dataset:
            return None

        return dataset_to_dict(dataset)


def get_active_dataset() -> Optional[dict]:
    """
    Mengambil dataset aktif.

    Dataset aktif adalah dataset utama yang dipakai admin untuk training.
    """

    with db_session() as session:
        statement = (
            select(Dataset)
            .where(Dataset.is_active.is_(True))
            .order_by(desc(Dataset.uploaded_at))
        )

        dataset = session.execute(statement).scalars().first()

        if not dataset:
            return None

        return dataset_to_dict(dataset)


def get_published_dataset() -> Optional[dict]:
    """
    Mengambil dataset published.

    Dataset published adalah dataset yang ditampilkan ke sisi user.
    """

    with db_session() as session:
        statement = (
            select(Dataset)
            .where(Dataset.is_published.is_(True))
            .order_by(desc(Dataset.uploaded_at))
        )

        dataset = session.execute(statement).scalars().first()

        if not dataset:
            return None

        return dataset_to_dict(dataset)


def get_dataset_rows_as_dataframe(dataset_id: int) -> pd.DataFrame:
    """
    Mengambil isi dataset dari tabel dataset_rows dan mengubahnya menjadi dataframe.
    """

    with db_session() as session:
        dataset = session.get(Dataset, dataset_id)

        if not dataset:
            raise ValueError("Dataset tidak ditemukan.")

        statement = (
            select(DatasetRow)
            .where(DatasetRow.dataset_id == dataset_id)
            .order_by(DatasetRow.tahun)
        )

        rows = session.execute(statement).scalars().all()

        data = []

        for row in rows:
            item = {YEAR_COLUMN: row.tahun}
            item.update(row.values_json)
            data.append(item)

    if not data:
        return pd.DataFrame()

    return pd.DataFrame(data)


def load_dataset_file_as_dataframe(dataset_id: int) -> pd.DataFrame:
    """
    Membaca file dataset dari storage berdasarkan ID dataset.
    """

    dataset = get_dataset_by_id(dataset_id)

    if not dataset:
        raise ValueError("Dataset tidak ditemukan.")

    storage_path = Path(dataset["storage_path"])

    if not storage_path.exists():
        raise FileNotFoundError(
            f"File dataset tidak ditemukan: {storage_path}"
        )

    return pd.read_excel(storage_path)


# ============================================================
# DATASET STATUS FUNCTIONS
# ============================================================

def set_active_dataset(
    dataset_id: int,
    admin_id: Optional[int] = None,
) -> dict:
    """
    Menjadikan dataset tertentu sebagai dataset aktif.
    """

    with db_session() as session:
        dataset = session.get(Dataset, dataset_id)

        if not dataset:
            raise ValueError("Dataset tidak ditemukan.")

        deactivate_other_datasets(session)

        dataset.is_active = True

        log_admin_activity(
            session=session,
            admin_id=admin_id,
            activity_type="SET_ACTIVE_DATASET",
            description=f"Dataset '{dataset.dataset_name}' dijadikan dataset aktif.",
        )

        session.flush()

        return dataset_to_dict(dataset)


def publish_dataset(
    dataset_id: int,
    admin_id: Optional[int] = None,
) -> dict:
    """
    Mempublish dataset agar tampil di sisi user.
    """

    with db_session() as session:
        dataset = session.get(Dataset, dataset_id)

        if not dataset:
            raise ValueError("Dataset tidak ditemukan.")

        unpublish_other_datasets(session)

        dataset.is_published = True
        dataset.is_active = True

        log_admin_activity(
            session=session,
            admin_id=admin_id,
            activity_type="PUBLISH_DATASET",
            description=f"Dataset '{dataset.dataset_name}' berhasil dipublish.",
        )

        session.flush()

        return dataset_to_dict(dataset)


def unpublish_dataset(
    dataset_id: int,
    admin_id: Optional[int] = None,
) -> dict:
    """
    Mengubah dataset menjadi tidak published.
    """

    with db_session() as session:
        dataset = session.get(Dataset, dataset_id)

        if not dataset:
            raise ValueError("Dataset tidak ditemukan.")

        dataset.is_published = False

        log_admin_activity(
            session=session,
            admin_id=admin_id,
            activity_type="UNPUBLISH_DATASET",
            description=f"Dataset '{dataset.dataset_name}' tidak lagi dipublish.",
        )

        session.flush()

        return dataset_to_dict(dataset)


def delete_dataset(
    dataset_id: int,
    admin_id: Optional[int] = None,
    confirm: bool = False,
) -> None:
    """
    Menghapus dataset dari database dan storage.

    Catatan:
    Dataset yang sudah dipakai training sebaiknya tidak dihapus di production.
    Pada mode production, fungsi ini membutuhkan confirm=True.
    """

    if APP_ENV == "production" and not confirm:
        raise RuntimeError(
            "delete_dataset() pada mode production membutuhkan confirm=True."
        )

    with db_session() as session:
        dataset = session.get(Dataset, dataset_id)

        if not dataset:
            raise ValueError("Dataset tidak ditemukan.")

        storage_path = Path(dataset.storage_path)
        dataset_name = dataset.dataset_name

        session.delete(dataset)

        log_admin_activity(
            session=session,
            admin_id=admin_id,
            activity_type="DELETE_DATASET",
            description=f"Dataset '{dataset_name}' dihapus.",
        )

    if storage_path.exists():
        storage_path.unlink()