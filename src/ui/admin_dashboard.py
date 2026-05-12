"""
Dashboard Admin.

File ini bertanggung jawab untuk:
- melindungi halaman admin dengan login,
- menampilkan status dataset aktif,
- menampilkan status dataset published,
- menampilkan model training terakhir,
- menampilkan model yang sedang dipublish,
- menampilkan evaluasi model,
- menyediakan navigasi awal untuk admin.

Catatan:
Fitur upload dataset dan training model akan dibuat pada file terpisah berikutnya.
"""

from __future__ import annotations

import streamlit as st

from src.auth.session_manager import (
    get_current_admin_name,
    require_admin_login,
)
from src.services.dataset_service import (
    get_active_dataset,
    get_published_dataset,
    list_datasets,
)
from src.services.training_service import (
    get_published_prediction_summary,
    get_published_training,
    list_training_results,
)
from src.utils.formatting import format_datetime, format_status
from src.utils.ui_components import (
    render_metric_cards,
    render_page_header,
    render_section_title,
    render_training_summary,
)


def render_admin_dashboard_page() -> None:
    """
    Render halaman dashboard admin.
    """

    if not require_admin_login():
        return

    admin_name = get_current_admin_name()

    render_page_header(
        title="Dashboard Admin",
        subtitle=(
            f"Selamat datang, {admin_name}. "
            "Kelola dataset, model LSTM, evaluasi, dan hasil prediksi dari halaman ini."
        ),
        icon="",
    )

    render_admin_quick_status()
    render_dataset_status_section()
    render_model_status_section()
    render_recent_training_section()
    render_admin_next_steps()


# ============================================================
# QUICK STATUS
# ============================================================

def render_admin_quick_status() -> None:
    """
    Menampilkan ringkasan cepat status sistem.
    """

    datasets = list_datasets(limit=100)
    trainings = list_training_results(limit=100)
    published_training = get_published_training()
    prediction_summary = get_published_prediction_summary()

    columns = st.columns(4)

    with columns[0]:
        st.metric("Total Dataset", len(datasets))

    with columns[1]:
        st.metric("Total Training", len(trainings))

    with columns[2]:
        st.metric("Model Published", "Ada" if published_training else "Belum Ada")

    with columns[3]:
        has_prediction = prediction_summary is not None
        st.metric("Prediksi Published", "Ada" if has_prediction else "Belum Ada")


# ============================================================
# DATASET STATUS
# ============================================================

def render_dataset_status_section() -> None:
    """
    Menampilkan status dataset aktif dan dataset published.
    """

    st.write("")
    render_section_title(
        "Status Dataset",
        "Dataset aktif digunakan untuk training, sedangkan dataset published ditampilkan ke sisi user.",
    )

    active_dataset = get_active_dataset()
    published_dataset = get_published_dataset()

    col_active, col_published = st.columns(2)

    with col_active:
        st.markdown("#### Dataset Aktif")

        if active_dataset:
            render_dataset_card(active_dataset)
        else:
            st.warning("Belum ada dataset aktif.")

    with col_published:
        st.markdown("#### Dataset Published")

        if published_dataset:
            render_dataset_card(published_dataset)
        else:
            st.warning("Belum ada dataset yang dipublish ke user.")


def render_dataset_card(dataset: dict) -> None:
    """
    Menampilkan informasi singkat dataset.
    """

    st.write(f"**{dataset.get('dataset_name', '-')}**")
    st.caption(f"File: {dataset.get('original_filename', '-')}")
    st.caption(f"Upload: {format_datetime(dataset.get('uploaded_at'))}")

    columns = st.columns(3)

    with columns[0]:
        st.metric("Baris", dataset.get("row_count", 0))

    with columns[1]:
        st.metric("Kolom", dataset.get("column_count", 0))

    with columns[2]:
        tahun_awal = dataset.get("start_year", "-")
        tahun_akhir = dataset.get("end_year", "-")
        st.metric("Periode", f"{tahun_awal}-{tahun_akhir}")


# ============================================================
# MODEL STATUS
# ============================================================

def render_model_status_section() -> None:
    """
    Menampilkan status model yang sedang dipublish.
    """

    st.write("")
    render_section_title(
        "Status Model Published",
        "Model yang sedang aktif ditampilkan ke user sebagai hasil prediksi resmi.",
    )

    prediction_summary = get_published_prediction_summary()

    if not prediction_summary:
        st.warning("Belum ada model atau hasil prediksi yang dipublish.")
        return

    training = prediction_summary.get("training")
    evaluation = prediction_summary.get("evaluation")

    if not training:
        st.warning("Data training published tidak ditemukan.")
        return

    render_training_summary(training, evaluation)

    if evaluation:
        st.write("")
        render_section_title("Metrik Evaluasi Published")
        render_metric_cards(
            {
                "MAE": evaluation.get("mae"),
                "RMSE": evaluation.get("rmse"),
                "MAPE": evaluation.get("mape"),
            }
        )


# ============================================================
# RECENT TRAINING
# ============================================================

def render_recent_training_section() -> None:
    """
    Menampilkan riwayat training terbaru.
    """

    st.write("")
    render_section_title(
        "Riwayat Training Terbaru",
        "Daftar proses training model LSTM yang pernah dijalankan.",
    )

    trainings = list_training_results(limit=10)

    if not trainings:
        st.info("Belum ada riwayat training model.")
        return

    table_data = []

    for training in trainings:
        table_data.append(
            {
                "ID": training.get("id"),
                "Versi Model": training.get("model_version"),
                "Status": format_status(training.get("status")),
                "Published": "Ya" if training.get("is_published") else "Tidak",
                "Window": training.get("window_size"),
                "Epochs": training.get("epochs"),
                "Selesai": format_datetime(training.get("finished_at")),
            }
        )

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# NEXT STEPS
# ============================================================

def render_admin_next_steps() -> None:
    """
    Menampilkan arahan fitur berikutnya untuk admin.
    """

    st.write("")
    render_section_title("Menu Admin Berikutnya")

    st.info(
        "Pada langkah berikutnya kita akan membuat halaman Upload Dataset Admin. "
        "Setelah itu kita lanjutkan ke halaman Training Model LSTM."
    )

    with st.expander("Alur kerja admin yang akan dibangun"):
        st.markdown(
            """
            ```txt
            1. Upload Dataset
            2. Validasi Dataset
            3. Publish Dataset
            4. Training Model LSTM
            5. Lihat Evaluasi MAE, RMSE, MAPE
            6. Lihat Hasil Prediksi Masa Depan
            7. Publish Hasil Prediksi ke User
            ```
            """
        )