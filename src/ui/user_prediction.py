from __future__ import annotations

import streamlit as st

from src.config.settings import (
    BATCH_SIZE,
    CORRELATION_THRESHOLD,
    DROPOUT_RATE,
    EARLY_STOPPING_PATIENCE,
    EPOCHS,
    FUTURE_YEARS_DEFAULT,
    FUTURE_YEARS_MAX,
    FUTURE_YEARS_MIN,
    LSTM_UNITS,
    TRAIN_RATIO,
    VALIDATION_SPLIT,
    WINDOW_SIZE,
)
from src.ml.lstm_service import train_lstm_pipeline
from src.utils.chart_builder import (
    build_combined_prediction_chart,
    build_future_prediction_chart,
    build_target_history_chart,
    build_test_prediction_chart,
)
from src.utils.file_validator import validate_and_read_dataset
from src.utils.ui_components import (
    render_dataframe,
    render_dataframe_download_button,
    render_dataset_summary,
    render_errors,
    render_evaluation_explanation,
    render_feature_badges,
    render_metric_cards,
    render_page_header,
    render_prediction_table,
    render_section_title,
    render_step_indicator,
    render_warnings,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

def render_user_prediction_page() -> None:
    """
    Render halaman Prediksi User.
    """

    render_page_header(
        title="Prediksi User",
        subtitle=(
            "Pengguna dapat mengunggah dataset sendiri untuk menjalankan "
            "prediksi jumlah pengangguran menggunakan model LSTM."
        ),
        icon="",
        badge="Publik",
    )

    render_step_indicator(
        [
            ("Upload Dataset", "Masukkan file Excel atau CSV."),
            ("Preview Data", "Cek ringkasan, tabel, dan grafik."),
            ("Konfigurasi", "Atur parameter prediksi."),
            ("Hasil Prediksi", "Lihat evaluasi, grafik, dan tabel."),
        ]
    )

    render_prediction_guidance()
    render_upload_area()


def render_prediction_guidance() -> None:
    """
    Menampilkan panduan singkat dalam expander agar halaman tidak terlalu penuh.
    """

    with st.expander("Panduan Prediksi User"):
        st.markdown(
            """
            Dataset minimal harus memiliki kolom **Tahun** dan
            **Total_Pengangguran**. Kolom tambahan dapat digunakan sebagai
            fitur pendukung jika berupa data numerik dan memenuhi nilai
            korelasi minimum.

            Parameter seperti **Window Size**, **Train Ratio**, **Epochs**,
            **Batch Size**, dan **Correlation Threshold** dapat disesuaikan
            untuk kebutuhan pengujian.
            """
        )


def render_upload_area() -> None:
    """
    Menampilkan area upload dataset user.
    """

    render_section_title(
        "Upload Dataset",
        "Dataset yang diupload akan divalidasi dan diproses menggunakan model LSTM.",
    )

    uploaded_file = st.file_uploader(
        "Upload dataset Excel/CSV",
        type=["xlsx", "xls", "csv"],
        help="Format file yang didukung: .xlsx, .xls, dan .csv",
    )

    if uploaded_file is None:
        st.info("Upload dataset terlebih dahulu untuk menjalankan prediksi.")
        return

    validation_result = validate_and_read_dataset(uploaded_file)

    show_validation_result(validation_result)

    if not validation_result.is_valid or validation_result.dataframe is None:
        return

    df = validation_result.dataframe

    show_dataset_preview(df)
    show_prediction_config(df)


def show_validation_result(validation_result) -> None:
    """
    Menampilkan hasil validasi dataset.
    """

    render_section_title(
        "Validasi Dataset",
        "Sistem memeriksa format kolom, tipe data, dan kelengkapan dataset.",
    )

    if validation_result.is_valid:
        st.success("Dataset valid dan siap diproses.")
    else:
        st.error("Dataset belum valid.")
        render_errors(validation_result.errors)

    render_warnings(validation_result.warnings)

    if validation_result.summary:
        render_section_title(
            "Ringkasan Dataset",
            "Informasi dasar dataset yang berhasil dibaca oleh sistem.",
        )
        render_dataset_summary(validation_result.summary)


def show_dataset_preview(df) -> None:
    """
    Menampilkan preview dataset dalam bentuk tabel dan grafik.
    """

    render_section_title(
        "Preview Dataset",
        "Tinjau isi dataset sebelum menjalankan proses prediksi.",
    )

    tab_table, tab_chart = st.tabs(["Tabel", "Grafik"])

    with tab_table:
        render_dataframe(
            df=df.head(50),
            empty_message="Dataset tidak tersedia.",
            height=320,
        )

        if len(df) > 50:
            st.caption(
                f"Dataset memiliki {len(df)} baris. "
                "Preview hanya menampilkan 50 baris pertama."
            )

    with tab_chart:
        st.plotly_chart(
            build_target_history_chart(df),
            use_container_width=True,
            key="user_prediction_target_chart",
        )


def show_prediction_config(df) -> None:
    """
    Menampilkan konfigurasi prediksi user.
    """

    render_section_title(
        "Konfigurasi Prediksi",
        "Atur parameter model LSTM sebelum menjalankan prediksi.",
    )

    with st.expander("Penjelasan Parameter Prediksi"):
        st.markdown(
            """
            **Jumlah Tahun Prediksi** menentukan jumlah periode mendatang yang
            ingin diprediksi.

            **Window Size** menentukan jumlah periode sebelumnya yang digunakan
            model untuk membentuk pola input.

            **Train Ratio** menentukan proporsi data yang digunakan sebagai data
            training.

            **Correlation Threshold** menentukan batas minimum korelasi untuk
            memilih fitur pendukung.

            **Epochs** menentukan jumlah maksimum iterasi training, sedangkan
            **Batch Size** menentukan jumlah sampel yang diproses dalam satu
            langkah training.
            """
        )

    col_left, col_right = st.columns(2)

    with col_left:
        future_years = st.number_input(
            "Jumlah Tahun Prediksi",
            min_value=FUTURE_YEARS_MIN,
            max_value=FUTURE_YEARS_MAX,
            value=FUTURE_YEARS_DEFAULT,
            step=1,
        )

        window_size = st.number_input(
            "Window Size",
            min_value=2,
            max_value=20,
            value=WINDOW_SIZE,
            step=1,
        )

        epochs = st.number_input(
            "Epochs",
            min_value=10,
            max_value=1000,
            value=EPOCHS,
            step=10,
        )

    with col_right:
        train_ratio = st.slider(
            "Train Ratio",
            min_value=0.5,
            max_value=0.9,
            value=float(TRAIN_RATIO),
            step=0.05,
        )

        correlation_threshold = st.slider(
            "Correlation Threshold",
            min_value=0.0,
            max_value=1.0,
            value=float(CORRELATION_THRESHOLD),
            step=0.05,
        )

        batch_size = st.number_input(
            "Batch Size",
            min_value=1,
            max_value=64,
            value=BATCH_SIZE,
            step=1,
        )

    if st.button("Jalankan Prediksi", use_container_width=True):
        run_user_prediction(
            df=df,
            future_years=int(future_years),
            window_size=int(window_size),
            epochs=int(epochs),
            train_ratio=float(train_ratio),
            correlation_threshold=float(correlation_threshold),
            batch_size=int(batch_size),
        )


def run_user_prediction(
    df,
    future_years: int,
    window_size: int,
    epochs: int,
    train_ratio: float,
    correlation_threshold: float,
    batch_size: int,
) -> None:
    """
    Menjalankan proses prediksi user.
    """

    progress_text = st.empty()
    progress_bar = st.progress(0)

    try:
        progress_text.info("Memproses dataset...")
        progress_bar.progress(20)

        progress_text.info("Melatih model LSTM...")
        progress_bar.progress(50)

        result = train_lstm_pipeline(
            df=df,
            future_years=future_years,
            window_size=window_size,
            train_ratio=train_ratio,
            correlation_threshold=correlation_threshold,
            lstm_units=LSTM_UNITS,
            dropout_rate=DROPOUT_RATE,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=VALIDATION_SPLIT,
            patience=EARLY_STOPPING_PATIENCE,
            verbose=0,
        )

        progress_text.info("Menyiapkan hasil prediksi...")
        progress_bar.progress(85)

        progress_bar.progress(100)
        progress_text.success("Prediksi berhasil dijalankan.")

        show_prediction_result(result)

    except Exception as exc:
        logger.exception("Prediksi user gagal dijalankan.")
        progress_bar.empty()
        progress_text.error("Prediksi gagal dijalankan.")
        st.error(f"Error: {exc}")

def show_prediction_result(result) -> None:
    """
    Menampilkan hasil prediksi user.
    """

    render_section_title(
        "Hasil Prediksi",
        "Ringkasan hasil prediksi berdasarkan dataset yang diupload user.",
    )

    render_metric_cards(result.metrics)

    st.write("")

    render_section_title(
        "Fitur Terpilih",
        "Fitur dipilih berdasarkan korelasi terhadap Total_Pengangguran.",
    )

    render_feature_badges(result.selected_features)

    with st.expander("Kolom yang Digunakan Model"):
        st.write(result.model_columns)

    render_section_title(
        "Visualisasi dan Tabel Prediksi",
        "Hasil prediksi ditampilkan dalam bentuk grafik, tabel, dan file CSV.",
    )

    tab_chart, tab_test, tab_future = st.tabs(
        [
            "Grafik Gabungan",
            "Prediksi Test",
            "Prediksi Masa Depan",
        ]
    )

    with tab_chart:
        st.plotly_chart(
            build_combined_prediction_chart(
                test_predictions=result.test_predictions,
                future_predictions=result.future_predictions,
            ),
            use_container_width=True,
            key="user_prediction_combined_chart",
        )

    with tab_test:
        render_prediction_table(
            df=result.test_predictions,
            title="Aktual vs Prediksi Data Test",
        )

        st.plotly_chart(
            build_test_prediction_chart(result.test_predictions),
            use_container_width=True,
            key="user_prediction_test_chart",
        )

        render_dataframe_download_button(
            df=result.test_predictions,
            filename="prediksi_user_test.csv",
            label="Download Prediksi Test",
        )

    with tab_future:
        render_prediction_table(
            df=result.future_predictions,
            title="Prediksi Masa Depan",
        )

        st.plotly_chart(
            build_future_prediction_chart(result.future_predictions),
            use_container_width=True,
            key="user_prediction_future_chart",
        )

        render_dataframe_download_button(
            df=result.future_predictions,
            filename="prediksi_user_masa_depan.csv",
            label="Download Prediksi Masa Depan",
        )

    render_evaluation_explanation()