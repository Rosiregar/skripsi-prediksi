"""
Utility validasi file dan dataset.

File ini bertanggung jawab untuk:
- mengecek ekstensi file dataset,
- mengecek ukuran file,
- membaca file Excel/CSV,
- memvalidasi kolom wajib,
- membersihkan nama kolom,
- mengubah kolom Tahun menjadi integer,
- memastikan semua fitur numerik,
- membuat ringkasan dataset.

Dataset yang valid minimal harus memiliki:
- kolom Tahun
- kolom Total_Pengangguran
- kolom fitur numerik lainnya
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from src.config.settings import (
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_SIZE_MB,
    TARGET_COLUMN,
    WINDOW_SIZE,
    YEAR_COLUMN,
)


@dataclass
class DatasetValidationResult:
    """
    Hasil validasi dataset.

    Attributes
    ----------
    is_valid : bool
        True jika dataset valid.

    dataframe : Optional[pd.DataFrame]
        Dataset yang sudah dibersihkan jika valid.

    errors : list[str]
        Daftar error validasi.

    warnings : list[str]
        Daftar peringatan validasi.

    summary : dict
        Ringkasan dataset.
    """

    is_valid: bool
    dataframe: Optional[pd.DataFrame]
    errors: list[str]
    warnings: list[str]
    summary: dict


# ============================================================
# FILE VALIDATION
# ============================================================

def get_file_extension(filename: str) -> str:
    """
    Mengambil ekstensi file.

    Contoh:
        dataset.xlsx -> .xlsx
        dataset.csv -> .csv
    """

    if not filename:
        return ""

    return Path(filename).suffix.lower()


def is_allowed_extension(filename: str) -> bool:
    """
    Mengecek apakah ekstensi file diizinkan.
    """

    extension = get_file_extension(filename)
    return extension in ALLOWED_EXTENSIONS


def get_file_size_mb(file_obj: Any) -> float:
    """
    Mengambil ukuran file dalam MB.

    Fungsi ini mendukung:
    - path file lokal,
    - file object biasa,
    - Streamlit UploadedFile.
    """

    size_bytes = 0

    if isinstance(file_obj, (str, Path)):
        file_path = Path(file_obj)
        if file_path.exists():
            size_bytes = file_path.stat().st_size

    elif hasattr(file_obj, "size"):
        size_bytes = int(file_obj.size)

    elif hasattr(file_obj, "getbuffer"):
        size_bytes = len(file_obj.getbuffer())

    elif hasattr(file_obj, "seek") and hasattr(file_obj, "tell"):
        current_position = file_obj.tell()
        file_obj.seek(0, 2)
        size_bytes = file_obj.tell()
        file_obj.seek(current_position)

    return size_bytes / (1024 * 1024)


def validate_file_size(file_obj: Any, max_size_mb: int = MAX_UPLOAD_SIZE_MB) -> bool:
    """
    Mengecek apakah ukuran file masih dalam batas maksimum.
    """

    file_size_mb = get_file_size_mb(file_obj)
    return file_size_mb <= max_size_mb


def read_dataset_file(file_obj: Any, filename: Optional[str] = None) -> pd.DataFrame:
    """
    Membaca file dataset Excel atau CSV.

    Parameters
    ----------
    file_obj : Any
        File path, file object, atau Streamlit UploadedFile.

    filename : Optional[str]
        Nama file. Dibutuhkan jika file_obj tidak memiliki atribut name.

    Returns
    -------
    pd.DataFrame
        Dataset yang sudah dibaca.
    """

    if filename is None:
        filename = getattr(file_obj, "name", None)

    if not filename and isinstance(file_obj, (str, Path)):
        filename = str(file_obj)

    if not filename:
        raise ValueError("Nama file tidak ditemukan.")

    extension = get_file_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Format file tidak didukung. "
            f"Gunakan salah satu dari: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    if extension == ".csv":
        return pd.read_csv(file_obj)

    if extension in [".xlsx", ".xls"]:
        return pd.read_excel(file_obj)

    raise ValueError("Format file tidak dikenali.")


# ============================================================
# DATASET CLEANING
# ============================================================

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Membersihkan nama kolom dengan menghapus spasi di awal dan akhir.

    Contoh:
        " Tahun " -> "Tahun"
    """

    cleaned_df = df.copy()
    cleaned_df.columns = [str(column).strip() for column in cleaned_df.columns]

    return cleaned_df


def convert_year_column_to_int(df: pd.DataFrame, year_column: str) -> pd.Series:
    """
    Mengubah kolom Tahun menjadi integer.

    Fungsi ini mendukung format:
    - 2018
    - "2018"
    - "2018-01-01"
    - datetime Excel
    """

    year_data = df[year_column]

    if pd.api.types.is_numeric_dtype(year_data):
        years = pd.to_numeric(year_data, errors="coerce").astype("Int64")
        return years

    year_as_string = year_data.astype(str).str.strip()
    is_four_digit_year = year_as_string.str.fullmatch(r"\d{4}").fillna(False)

    if is_four_digit_year.all():
        years = pd.to_numeric(year_as_string, errors="coerce").astype("Int64")
        return years

    parsed_dates = pd.to_datetime(year_data, errors="coerce")
    years = parsed_dates.dt.year.astype("Int64")

    return years


def standardize_dataset(
    df: pd.DataFrame,
    year_column: str = YEAR_COLUMN,
    target_column: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """
    Membersihkan dan menstandarkan dataset.

    Output dari fungsi ini:
    - nama kolom sudah dibersihkan,
    - kolom Tahun menjadi integer,
    - semua kolom selain Tahun menjadi numerik,
    - data diurutkan berdasarkan Tahun.
    """

    if df is None:
        raise ValueError("Dataset kosong.")

    if df.empty:
        raise ValueError("Dataset tidak memiliki data.")

    cleaned_df = clean_column_names(df)

    required_columns = [year_column, target_column]
    missing_columns = [
        column for column in required_columns
        if column not in cleaned_df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Kolom wajib tidak ditemukan: "
            + ", ".join(missing_columns)
        )

    cleaned_df[year_column] = convert_year_column_to_int(
        cleaned_df,
        year_column,
    )

    if cleaned_df[year_column].isna().any():
        raise ValueError(
            f"Kolom {year_column} memiliki nilai tahun yang tidak valid."
        )

    cleaned_df[year_column] = cleaned_df[year_column].astype(int)

    invalid_numeric_columns = []

    for column in cleaned_df.columns:
        if column == year_column:
            continue

        cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors="coerce")

        if cleaned_df[column].isna().any():
            invalid_numeric_columns.append(column)

    if invalid_numeric_columns:
        raise ValueError(
            "Kolom berikut harus berisi angka dan tidak boleh kosong: "
            + ", ".join(invalid_numeric_columns)
        )

    cleaned_df = cleaned_df.sort_values(by=year_column).reset_index(drop=True)

    return cleaned_df


# ============================================================
# DATASET SUMMARY
# ============================================================

def get_dataset_summary(
    df: pd.DataFrame,
    year_column: str = YEAR_COLUMN,
    target_column: str = TARGET_COLUMN,
) -> dict:
    """
    Membuat ringkasan dataset.
    """

    summary = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "year_column": year_column,
        "target_column": target_column,
        "start_year": None,
        "end_year": None,
        "missing_values": {},
        "duplicated_years": 0,
        "numeric_columns": [],
    }

    if year_column in df.columns and len(df) > 0:
        summary["start_year"] = int(df[year_column].min())
        summary["end_year"] = int(df[year_column].max())
        summary["duplicated_years"] = int(df[year_column].duplicated().sum())

    summary["missing_values"] = {
        column: int(total)
        for column, total in df.isna().sum().to_dict().items()
    }

    summary["numeric_columns"] = [
        column for column in df.columns
        if column != year_column and pd.api.types.is_numeric_dtype(df[column])
    ]

    return summary


# ============================================================
# DATASET VALIDATION
# ============================================================

def validate_dataset(
    df: pd.DataFrame,
    year_column: str = YEAR_COLUMN,
    target_column: str = TARGET_COLUMN,
    window_size: int = WINDOW_SIZE,
) -> DatasetValidationResult:
    """
    Melakukan validasi lengkap dataset.

    Dataset valid jika:
    - tidak kosong,
    - memiliki kolom Tahun,
    - memiliki kolom Total_Pengangguran,
    - semua fitur selain Tahun numerik,
    - jumlah data cukup untuk LSTM,
    - tidak ada tahun duplikat,
    - nilai target lebih dari 0.
    """

    errors = []
    warnings = []
    cleaned_df = None
    summary = {}

    try:
        cleaned_df = standardize_dataset(
            df=df,
            year_column=year_column,
            target_column=target_column,
        )

        summary = get_dataset_summary(
            df=cleaned_df,
            year_column=year_column,
            target_column=target_column,
        )

    except Exception as exc:
        errors.append(str(exc))

        return DatasetValidationResult(
            is_valid=False,
            dataframe=None,
            errors=errors,
            warnings=warnings,
            summary=summary,
        )

    minimum_rows = window_size + 3

    if len(cleaned_df) < minimum_rows:
        errors.append(
            f"Jumlah data terlalu sedikit. "
            f"Minimal diperlukan {minimum_rows} baris data "
            f"untuk window_size={window_size}."
        )

    if cleaned_df[year_column].duplicated().any():
        duplicated_years = (
            cleaned_df.loc[
                cleaned_df[year_column].duplicated(),
                year_column,
            ]
            .astype(str)
            .tolist()
        )

        errors.append(
            "Terdapat tahun duplikat pada dataset: "
            + ", ".join(duplicated_years)
        )

    if (cleaned_df[target_column] <= 0).any():
        errors.append(
            f"Kolom {target_column} harus bernilai lebih dari 0. "
            "Nilai 0 atau negatif akan mengganggu perhitungan MAPE."
        )

    feature_columns = [
        column for column in cleaned_df.columns
        if column not in [year_column, target_column]
    ]

    if len(feature_columns) == 0:
        warnings.append(
            "Dataset tidak memiliki fitur tambahan selain target. "
            "Model masih bisa dibuat, tetapi prediksi hanya berbasis target."
        )

    year_values = cleaned_df[year_column].tolist()

    if len(year_values) > 1:
        expected_years = list(range(min(year_values), max(year_values) + 1))
        missing_years = sorted(set(expected_years) - set(year_values))

        if missing_years:
            warnings.append(
                "Terdapat tahun yang tidak ada dalam dataset: "
                + ", ".join(str(year) for year in missing_years)
            )

    if len(cleaned_df) < 10:
        warnings.append(
            "Jumlah data kurang dari 10 baris. "
            "Training LSTM mungkin kurang stabil karena data historis terbatas."
        )

    is_valid = len(errors) == 0

    return DatasetValidationResult(
        is_valid=is_valid,
        dataframe=cleaned_df if is_valid else None,
        errors=errors,
        warnings=warnings,
        summary=summary,
    )


def validate_and_read_dataset(
    file_obj: Any,
    filename: Optional[str] = None,
) -> DatasetValidationResult:
    """
    Membaca dan memvalidasi dataset dari file upload.

    Fungsi ini akan sering dipakai pada halaman upload dataset admin dan user.
    """

    errors = []
    warnings = []

    if filename is None:
        filename = getattr(file_obj, "name", None)

    if not filename and isinstance(file_obj, (str, Path)):
        filename = str(file_obj)

    if not filename:
        errors.append("Nama file tidak ditemukan.")

        return DatasetValidationResult(
            is_valid=False,
            dataframe=None,
            errors=errors,
            warnings=warnings,
            summary={},
        )

    if not is_allowed_extension(filename):
        errors.append(
            f"Format file tidak didukung. "
            f"Gunakan salah satu dari: {', '.join(ALLOWED_EXTENSIONS)}"
        )

        return DatasetValidationResult(
            is_valid=False,
            dataframe=None,
            errors=errors,
            warnings=warnings,
            summary={},
        )

    if not validate_file_size(file_obj):
        errors.append(
            f"Ukuran file melebihi batas maksimum {MAX_UPLOAD_SIZE_MB} MB."
        )

        return DatasetValidationResult(
            is_valid=False,
            dataframe=None,
            errors=errors,
            warnings=warnings,
            summary={},
        )

    try:
        df = read_dataset_file(file_obj=file_obj, filename=filename)
    except Exception as exc:
        errors.append(f"Gagal membaca file dataset: {exc}")

        return DatasetValidationResult(
            is_valid=False,
            dataframe=None,
            errors=errors,
            warnings=warnings,
            summary={},
        )

    return validate_dataset(df)