"""
Utility formatting untuk aplikasi Streamlit.

File ini bertanggung jawab untuk:
- format angka jumlah pengangguran,
- format MAE, RMSE, MAPE,
- format tahun,
- format status training,
- format nama kolom agar lebih ramah dibaca di UI.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import pandas as pd


# ============================================================
# NUMBER FORMATTERS
# ============================================================

def format_number(value: Any, decimal_places: int = 0) -> str:
    """
    Format angka dengan pemisah ribuan.

    Contoh:
        1234567 -> 1,234,567
    """

    if value is None:
        return "-"

    try:
        value_float = float(value)

        if pd.isna(value_float):
            return "-"

        return f"{value_float:,.{decimal_places}f}"
    except Exception:
        return str(value)


def format_people(value: Any) -> str:
    """
    Format angka jumlah orang/jiwa.

    Contoh:
        123456 -> 123,456 jiwa
    """

    if value is None:
        return "-"

    return f"{format_number(value, 0)} jiwa"


def format_percentage(value: Any, decimal_places: int = 2) -> str:
    """
    Format angka persen.

    Contoh:
        12.3456 -> 12.35%
    """

    if value is None:
        return "-"

    try:
        value_float = float(value)

        if pd.isna(value_float):
            return "-"

        return f"{value_float:.{decimal_places}f}%"
    except Exception:
        return str(value)


def format_metric_value(metric_name: str, value: Any) -> str:
    """
    Format nilai metrik berdasarkan nama metrik.

    MAE dan RMSE ditampilkan sebagai jiwa.
    MAPE ditampilkan sebagai persen.
    """

    metric_name_upper = metric_name.upper()

    if metric_name_upper in ["MAE", "RMSE"]:
        return format_people(value)

    if metric_name_upper == "MAPE":
        return format_percentage(value)

    return format_number(value)


# ============================================================
# DATE FORMATTERS
# ============================================================

def format_datetime(value: Any) -> str:
    """
    Format datetime agar ramah dibaca.

    Output:
        07 Mei 2026 14:30
    """

    if value is None:
        return "-"

    month_names = {
        1: "Januari",
        2: "Februari",
        3: "Maret",
        4: "April",
        5: "Mei",
        6: "Juni",
        7: "Juli",
        8: "Agustus",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Desember",
    }

    try:
        if isinstance(value, str):
            value = pd.to_datetime(value)

        if isinstance(value, pd.Timestamp):
            value = value.to_pydatetime()

        if isinstance(value, datetime):
            month_name = month_names.get(value.month, str(value.month))
            return (
                f"{value.day:02d} {month_name} {value.year} "
                f"{value.hour:02d}:{value.minute:02d}"
            )

        return str(value)
    except Exception:
        return str(value)


def format_year(value: Any) -> str:
    """
    Format tahun.
    """

    if value is None:
        return "-"

    try:
        return str(int(value))
    except Exception:
        return str(value)


# ============================================================
# TEXT FORMATTERS
# ============================================================

def prettify_column_name(column_name: str) -> str:
    """
    Mengubah nama kolom agar lebih mudah dibaca.

    Contoh:
        Total_Pengangguran -> Total Pengangguran
    """

    if not column_name:
        return ""

    return str(column_name).replace("_", " ").strip().title()


def prettify_status(status: Optional[str]) -> str:
    """
    Mengubah status internal menjadi teks ramah user.
    """

    if not status:
        return "-"

    mapping = {
        "created": "Dibuat",
        "running": "Sedang Diproses",
        "completed": "Selesai",
        "failed": "Gagal",
        "published": "Dipublish",
        "archived": "Diarsipkan",
    }

    return mapping.get(status.lower(), prettify_column_name(status))


def get_status_icon(status: Optional[str]) -> str:
    """
    Mengambil ikon berdasarkan status.
    """

    if not status:
        return "⚪"

    mapping = {
        "created": "⚪",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
        "published": "🟢",
        "archived": "📦",
    }

    return mapping.get(status.lower(), "⚪")


def format_status(status: Optional[str]) -> str:
    """
    Format status lengkap dengan ikon.
    """

    return f"{get_status_icon(status)} {prettify_status(status)}"


# ============================================================
# DATAFRAME FORMATTERS
# ============================================================

def format_prediction_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format dataframe prediksi agar siap ditampilkan di Streamlit.

    Kolom yang dikenali:
    - Tahun
    - Aktual
    - Prediksi
    """

    if df is None or df.empty:
        return pd.DataFrame()

    formatted_df = df.copy()

    if "Tahun" in formatted_df.columns:
        formatted_df["Tahun"] = formatted_df["Tahun"].apply(format_year)

    if "Aktual" in formatted_df.columns:
        formatted_df["Aktual"] = formatted_df["Aktual"].apply(format_people)

    if "Prediksi" in formatted_df.columns:
        formatted_df["Prediksi"] = formatted_df["Prediksi"].apply(format_people)

    return formatted_df


def format_metrics_dict(metrics: Optional[dict]) -> dict:
    """
    Format dictionary metrics.

    Input:
        {"MAE": 123, "RMSE": 456, "MAPE": 7.89}

    Output:
        {"MAE": "123 jiwa", "RMSE": "456 jiwa", "MAPE": "7.89%"}
    """

    if not metrics:
        return {}

    return {
        key: format_metric_value(key, value)
        for key, value in metrics.items()
    }


# ============================================================
# VALIDATION DISPLAY HELPERS
# ============================================================

def build_error_message(errors: list[str]) -> str:
    """
    Mengubah list error menjadi teks.
    """

    if not errors:
        return ""

    return "\n".join(f"- {error}" for error in errors)


def build_warning_message(warnings: list[str]) -> str:
    """
    Mengubah list warning menjadi teks.
    """

    if not warnings:
        return ""

    return "\n".join(f"- {warning}" for warning in warnings)