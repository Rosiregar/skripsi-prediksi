"""
Halaman Hasil Prediksi User.

File ini bertanggung jawab untuk:
- menampilkan hasil prediksi resmi yang dipublish admin,
- menampilkan informasi model aktif,
- menampilkan evaluasi MAE, RMSE, MAPE,
- menampilkan grafik aktual vs prediksi,
- menampilkan grafik prediksi masa depan,
- menampilkan tabel hasil prediksi.

Catatan:
- assumption_note sudah dihapus total.
- File ini hanya mengubah tampilan halaman, bukan logika model.
"""

from __future__ import annotations

import streamlit as st

from src.services.training_service import get_published_prediction_summary
from src.utils.chart_builder import (
    build_combined_prediction_chart,
    build_future_prediction_chart,
    build_test_prediction_chart,
)
from src.utils.formatting import format_datetime
from src.utils.ui_components import (
    render_dataframe_download_button,
    render_empty_state,
    render_evaluation_explanation,
    render_info_card,
    render_metric_cards,
    render_page_header,
    render_prediction_table,
    render_section_title,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

def render_user_results_page() -> None:
    """
    Render halaman hasil prediksi resmi untuk user.
    """

    render_page_header(
        title="Hasil Prediksi",
        subtitle=(
            "Hasil prediksi jumlah pengangguran berdasarkan model LSTM "
            "yang sudah dipublish oleh admin."
        ),
        icon="",
        badge="Publik",
    )

    try:
        prediction_summary = get_published_prediction_summary()
    except Exception as exc:
        logger.exception("Gagal mengambil hasil prediksi yang dipublish.")
        st.error(f"Gagal memuat hasil prediksi: {exc}")
        return

    if not prediction_summary:
        render_empty_prediction_state()
        return

    training = prediction_summary["training"]
    evaluation = prediction_summary["evaluation"]
    test_predictions = prediction_summary["test_predictions"]
    future_predictions = prediction_summary["future_predictions"]

    render_model_information(training)
    render_evaluation_section(evaluation)
    render_prediction_chart_section(test_predictions, future_predictions)
    render_prediction_table_section(test_predictions, future_predictions)
    render_evaluation_explanation()


def render_empty_prediction_state() -> None:
    """
    Tampilan jika belum ada hasil prediksi yang dipublish.
    """

    render_empty_state(
        title="Belum Ada Hasil Prediksi",
        text=(
            "Belum ada hasil prediksi yang dipublish oleh admin. "
            "Silakan login sebagai admin, upload dataset, training model, "
            "lalu publish hasil prediksi."
        ),
    )

    with st.expander("Alur agar hasil prediksi tampil di halaman ini"):
        st.markdown(
            """
            Agar hasil prediksi tampil di halaman user, admin perlu melakukan:

            ```text
            Login Admin
            ↓
            Upload Dataset
            ↓
            Aktifkan Dataset
            ↓
            Training Model LSTM
            ↓
            Lihat Evaluasi
            ↓
            Publish Hasil Prediksi
            ```
            """
        )


def render_model_information(training: dict) -> None:
    """
    Menampilkan informasi model aktif.
    """

    render_section_title(
        "Informasi Model Aktif",
        "Model LSTM yang sedang dipublish dan digunakan sebagai hasil resmi.",
    )

    columns = st.columns(4)

    with columns[0]:
        render_info_card(
            "Algoritma",
            str(training.get("algorithm", "LSTM")),
        )

    with columns[1]:
        render_info_card(
            "Window Size",
            str(training.get("window_size", "-")),
        )

    with columns[2]:
        render_info_card(
            "Epochs",
            str(training.get("epochs", "-")),
        )

    with columns[3]:
        render_info_card(
            "Batch Size",
            str(training.get("batch_size", "-")),
        )

    st.write("")

    col_version, col_date = st.columns(2)

    with col_version:
        render_info_card(
            "Versi Model",
            str(training.get("model_version", "-")),
        )

    with col_date:
        render_info_card(
            "Tanggal Training",
            format_datetime(training.get("finished_at")),
        )


def render_evaluation_section(evaluation: dict | None) -> None:
    """
    Menampilkan evaluasi model.
    """

    render_section_title(
        "Evaluasi Model",
        "Evaluasi dihitung berdasarkan data test historis.",
    )

    if not evaluation:
        st.warning("Data evaluasi model belum tersedia.")
        return

    metrics = {
        "MAE": evaluation.get("mae"),
        "RMSE": evaluation.get("rmse"),
        "MAPE": evaluation.get("mape"),
    }

    render_metric_cards(metrics)

    test_start_year = evaluation.get("test_start_year")
    test_end_year = evaluation.get("test_end_year")

    if test_start_year and test_end_year:
        st.caption(
            f"Periode data test: {test_start_year} sampai {test_end_year}"
        )


def render_prediction_chart_section(test_predictions, future_predictions) -> None:
    """
    Menampilkan grafik hasil prediksi.
    """

    render_section_title(
        "Visualisasi Hasil Prediksi",
        "Grafik aktual, prediksi data test, dan prediksi masa depan.",
    )

    tab_combined, tab_test, tab_future = st.tabs(
        [
            "Gabungan",
            "Aktual vs Prediksi Test",
            "Prediksi Masa Depan",
        ]
    )

    with tab_combined:
        st.plotly_chart(
            build_combined_prediction_chart(
                test_predictions=test_predictions,
                future_predictions=future_predictions,
            ),
            use_container_width=True,
            key="published_combined_prediction_chart",
        )

    with tab_test:
        st.plotly_chart(
            build_test_prediction_chart(test_predictions),
            use_container_width=True,
            key="published_test_prediction_chart",
        )

    with tab_future:
        st.plotly_chart(
            build_future_prediction_chart(future_predictions),
            use_container_width=True,
            key="published_future_prediction_chart",
        )


def render_prediction_table_section(test_predictions, future_predictions) -> None:
    """
    Menampilkan tabel hasil prediksi.
    Kolom teknis seperti training_id, is_published, dan published_at
    disembunyikan agar tampilan user lebih bersih.
    """

    render_section_title(
        "Tabel Hasil Prediksi",
        "Data aktual vs prediksi test dan prediksi masa depan.",
    )

    clean_test_predictions = test_predictions.copy()
    clean_future_predictions = future_predictions.copy()

    hidden_columns = [
        "training_id",
        "is_published",
        "published_at",
        "created_at",
        "updated_at",
    ]

    clean_test_predictions = clean_test_predictions.drop(
        columns=[col for col in hidden_columns if col in clean_test_predictions.columns],
        errors="ignore",
    )

    clean_future_predictions = clean_future_predictions.drop(
        columns=[col for col in hidden_columns if col in clean_future_predictions.columns],
        errors="ignore",
    )

    tab_test_table, tab_future_table = st.tabs(
        [
            "Prediksi Data Test",
            "Prediksi Masa Depan",
        ]
    )

    with tab_test_table:
        render_prediction_table(
            df=clean_test_predictions,
            title="Tabel Aktual vs Prediksi Data Test",
        )

        render_dataframe_download_button(
            df=clean_test_predictions,
            filename="hasil_prediksi_test.csv",
            label="Download Hasil Prediksi Test CSV",
        )

    with tab_future_table:
        render_prediction_table(
            df=clean_future_predictions,
            title="Tabel Prediksi Masa Depan",
        )

        render_dataframe_download_button(
            df=clean_future_predictions,
            filename="hasil_prediksi_masa_depan.csv",
            label="Download Prediksi Masa Depan CSV",
        )