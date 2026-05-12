from __future__ import annotations

import streamlit as st

from src.auth.session_manager import get_current_admin_id, require_admin_login
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
from src.services.dataset_service import (
    get_active_dataset,
    get_dataset_rows_as_dataframe,
)
from src.services.training_service import (
    get_future_predictions_dataframe,
    get_test_predictions_dataframe,
    get_training_evaluation,
    list_training_results,
    publish_training_result,
    train_active_dataset_model,
)
from src.utils.chart_builder import (
    build_combined_prediction_chart,
    build_future_prediction_chart,
    build_target_history_chart,
    build_test_prediction_chart,
)
from src.utils.formatting import format_datetime, format_status
from src.utils.ui_components import (
    render_admin_page_header,
    render_dataframe_download_button,
    render_empty_state,
    render_feature_badges,
    render_info_card,
    render_metric_cards,
    render_prediction_table,
    render_section_title,
    render_step_indicator,
    render_training_summary,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

def render_admin_training_page() -> None:
    """
    Render halaman Training Model Admin.
    """

    if not require_admin_login():
        return

    render_admin_page_header(
        title="Training Model LSTM",
        subtitle=(
            "Melatih model LSTM berdasarkan dataset aktif, melihat evaluasi, "
            "dan mempublish hasil prediksi ke halaman publik."
        ),
    )

    active_dataset = get_active_dataset()

    if not active_dataset:
        render_empty_dataset_message()
        return

    render_training_steps()
    render_active_dataset_info(active_dataset)

    tab_training, tab_history = st.tabs(
        [
            "Training Model",
            "Riwayat Training",
        ]
    )

    with tab_training:
        render_training_form()

    with tab_history:
        render_training_history()


def render_training_steps() -> None:
    """
    Menampilkan alur proses training model.
    """

    render_step_indicator(
        [
            ("Dataset Aktif", "Gunakan dataset yang sudah diaktifkan."),
            ("Konfigurasi", "Atur parameter training LSTM."),
            ("Training", "Latih model dan hitung evaluasi."),
            ("Publish", "Tampilkan hasil ke halaman publik."),
        ]
    )


def render_empty_dataset_message() -> None:
    """
    Tampilan jika belum ada dataset aktif.
    """

    render_empty_state(
        title="Belum Ada Dataset Aktif",
        text=(
            "Buka menu Kelola Dataset, upload dataset, lalu jadikan dataset "
            "tersebut sebagai dataset aktif sebelum melakukan training model."
        ),
    )

    with st.expander("Format Dataset yang Dibutuhkan"):
        st.markdown(
            """
            Dataset minimal harus memiliki kolom:

            ```text
            Tahun
            Total_Pengangguran
            ```

            Contoh struktur dataset:

            ```text
            Tahun | Total_Pengangguran | Jumlah_Penduduk | TPAK | PDRB
            2018  | 70000              | 2600000         | 62.1 | 12345
            2019  | 72000              | 2630000         | 62.4 | 12500
            2020  | 76000              | 2650000         | 61.8 | 12400
            ```
            """
        )


def render_active_dataset_info(dataset: dict) -> None:
    """
    Menampilkan informasi dataset aktif.
    """

    render_section_title(
        "Dataset Aktif",
        "Dataset ini digunakan sebagai dasar proses training model LSTM.",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_info_card(
            "Nama Dataset",
            str(dataset.get("dataset_name", "-")),
        )

    with col2:
        render_info_card(
            "Jumlah Baris",
            str(dataset.get("row_count", 0)),
        )

    with col3:
        render_info_card(
            "Tahun Awal",
            str(dataset.get("start_year", "-")),
        )

    with col4:
        render_info_card(
            "Tahun Akhir",
            str(dataset.get("end_year", "-")),
        )

    st.write("")

    col_file, col_upload = st.columns(2)

    with col_file:
        render_info_card(
            "File Dataset",
            str(dataset.get("original_filename", "-")),
        )

    with col_upload:
        render_info_card(
            "Tanggal Upload",
            format_datetime(dataset.get("uploaded_at")),
        )

    try:
        df = get_dataset_rows_as_dataframe(dataset["id"])

        with st.expander("Preview Dataset Aktif"):
            st.dataframe(
                df.head(50),
                use_container_width=True,
                height=300,
            )

            if len(df) > 50:
                st.caption(
                    f"Dataset memiliki {len(df)} baris. "
                    "Preview hanya menampilkan 50 baris pertama."
                )

            st.plotly_chart(
                build_target_history_chart(df),
                use_container_width=True,
                key=f"active_dataset_chart_{dataset['id']}",
            )

    except Exception as exc:
        st.error(f"Gagal membaca dataset aktif: {exc}")


def render_training_form() -> None:
    """
    Menampilkan form konfigurasi training model.
    """

    render_section_title(
        "Konfigurasi Training",
        "Nilai default mengikuti rancangan model LSTM pada penelitian.",
    )

    with st.expander("Konfigurasi Default Model", expanded=False):
        st.markdown(
            f"""
            ```text
            Target Column          : Total_Pengangguran
            Window Size            : {WINDOW_SIZE}
            Train Ratio            : {TRAIN_RATIO}
            LSTM Units             : {LSTM_UNITS}
            Dropout Rate           : {DROPOUT_RATE}
            Epochs                 : {EPOCHS}
            Batch Size             : {BATCH_SIZE}
            Validation Split       : {VALIDATION_SPLIT}
            EarlyStopping Patience : {EARLY_STOPPING_PATIENCE}
            Korelasi Fitur         : abs(corr) >= {CORRELATION_THRESHOLD}
            Prediksi Default       : {FUTURE_YEARS_DEFAULT} tahun ke depan
            ```
            """
        )

    with st.expander("Penjelasan Parameter Training"):
        st.markdown(
            """
            **Window Size** menentukan jumlah periode sebelumnya yang digunakan
            sebagai input model.

            **Train Ratio** menentukan proporsi data yang digunakan untuk
            proses training.

            **LSTM Units** menentukan jumlah unit pada layer LSTM.

            **Dropout Rate** digunakan untuk mengurangi risiko overfitting.

            **Epochs** menentukan jumlah maksimum iterasi training.

            **Batch Size** menentukan jumlah sampel yang diproses dalam satu
            langkah training.

            **Correlation Threshold** menentukan batas korelasi minimum untuk
            memilih fitur pendukung.
            """
        )

    col_left, col_right = st.columns(2)

    with col_left:
        future_years = st.number_input(
            "Jumlah Tahun Prediksi Masa Depan",
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

        batch_size = st.number_input(
            "Batch Size",
            min_value=1,
            max_value=64,
            value=BATCH_SIZE,
            step=1,
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

        lstm_units = st.number_input(
            "LSTM Units",
            min_value=4,
            max_value=256,
            value=LSTM_UNITS,
            step=4,
        )

        dropout_rate = st.slider(
            "Dropout Rate",
            min_value=0.0,
            max_value=0.8,
            value=float(DROPOUT_RATE),
            step=0.05,
        )

    publish_after_training = st.checkbox(
        "Langsung publish hasil training ke user",
        value=False,
        help="Jika dicentang, hasil training langsung tampil di halaman Hasil Prediksi.",
    )

    st.info(
        "Proses training TensorFlow dapat membutuhkan waktu beberapa menit. "
        "Jangan tutup halaman sampai proses selesai."
    )

    if st.button("Mulai Training Model LSTM", use_container_width=True):
        run_training_process(
            future_years=int(future_years),
            window_size=int(window_size),
            epochs=int(epochs),
            batch_size=int(batch_size),
            train_ratio=float(train_ratio),
            correlation_threshold=float(correlation_threshold),
            lstm_units=int(lstm_units),
            dropout_rate=float(dropout_rate),
            publish_after_training=publish_after_training,
        )


def run_training_process(
    future_years: int,
    window_size: int,
    epochs: int,
    batch_size: int,
    train_ratio: float,
    correlation_threshold: float,
    lstm_units: int,
    dropout_rate: float,
    publish_after_training: bool,
) -> None:
    """
    Menjalankan proses training model.
    """

    admin_id = get_current_admin_id()

    progress_text = st.empty()
    progress_bar = st.progress(0)

    try:
        progress_text.info("Menyiapkan dataset aktif...")
        progress_bar.progress(10)

        progress_text.info("Menjalankan preprocessing dan seleksi fitur...")
        progress_bar.progress(25)

        progress_text.info("Melatih model LSTM...")
        progress_bar.progress(45)

        result = train_active_dataset_model(
            admin_id=admin_id,
            future_years=future_years,
            publish_after_training=publish_after_training,
            window_size=window_size,
            train_ratio=train_ratio,
            correlation_threshold=correlation_threshold,
            lstm_units=lstm_units,
            dropout_rate=dropout_rate,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=VALIDATION_SPLIT,
            early_stopping_patience=EARLY_STOPPING_PATIENCE,
            verbose=0,
        )

        progress_text.info("Menyimpan model, scaler, evaluasi, dan hasil prediksi...")
        progress_bar.progress(90)

        progress_bar.progress(100)
        progress_text.success("Training model berhasil diselesaikan.")

        render_training_result(result)

    except Exception as exc:
        logger.exception("Training model gagal dijalankan.")
        progress_bar.empty()
        progress_text.error("Training model gagal.")
        st.error(f"Error: {exc}")


def render_training_result(result: dict) -> None:
    """
    Menampilkan hasil training model yang baru dijalankan.
    """

    st.write("")
    render_section_title(
        "Hasil Training",
        "Ringkasan hasil training model LSTM.",
    )

    training = result.get("training")
    evaluation = result.get("evaluation")
    metrics = result.get("metrics")
    selected_features = result.get("selected_features", [])
    model_columns = result.get("model_columns", [])
    test_predictions = result.get("test_predictions")
    future_predictions = result.get("future_predictions")

    if training:
        render_training_summary(training, evaluation)

    if metrics:
        st.write("")
        render_section_title(
            "Evaluasi Model",
            "Nilai evaluasi model berdasarkan data test historis.",
        )
        render_metric_cards(metrics)

    st.write("")
    render_section_title(
        "Fitur Terpilih",
        "Fitur dipilih berdasarkan korelasi terhadap Total_Pengangguran.",
    )

    render_feature_badges(selected_features)

    with st.expander("Kolom yang Digunakan Model"):
        st.write(model_columns)

    render_section_title(
        "Visualisasi dan Tabel Hasil Training",
        "Hasil training ditampilkan dalam grafik dan tabel prediksi.",
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
                test_predictions=test_predictions,
                future_predictions=future_predictions,
            ),
            use_container_width=True,
            key="training_result_combined_chart",
        )

    with tab_test:
        render_prediction_table(
            df=test_predictions,
            title="Aktual vs Prediksi Data Test",
        )

        st.plotly_chart(
            build_test_prediction_chart(test_predictions),
            use_container_width=True,
            key="training_result_test_chart",
        )

    with tab_future:
        render_prediction_table(
            df=future_predictions,
            title="Prediksi Masa Depan",
        )

        st.plotly_chart(
            build_future_prediction_chart(future_predictions),
            use_container_width=True,
            key="training_result_future_chart",
        )

    if training and not training.get("is_published"):
        st.info(
            "Hasil training ini belum dipublish. "
            "Anda dapat mempublish-nya melalui tab Riwayat Training."
        )


def render_training_history() -> None:
    """
    Menampilkan riwayat training model.
    """

    render_section_title(
        "Riwayat Training",
        "Daftar model LSTM yang pernah dilatih.",
    )

    trainings = list_training_results(limit=100)

    if not trainings:
        render_empty_state(
            title="Belum Ada Riwayat Training",
            text="Belum ada model LSTM yang pernah dilatih.",
        )
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
                "Batch": training.get("batch_size"),
                "Selesai": format_datetime(training.get("finished_at")),
            }
        )

    st.dataframe(
        table_data,
        use_container_width=True,
    )

    completed_trainings = [
        training
        for training in trainings
        if training.get("status") == "completed"
    ]

    if not completed_trainings:
        st.info("Belum ada training dengan status completed.")
        return

    options = {
        f"ID {training['id']} - {training['model_version']}": training["id"]
        for training in completed_trainings
    }

    selected_label = st.selectbox(
        "Pilih training",
        options=list(options.keys()),
    )

    selected_training_id = options[selected_label]

    render_selected_training_detail(selected_training_id)


def render_selected_training_detail(training_id: int) -> None:
    """
    Menampilkan detail training yang dipilih dari riwayat.
    """

    evaluation = get_training_evaluation(training_id)
    test_predictions = get_test_predictions_dataframe(training_id)
    future_predictions = get_future_predictions_dataframe(training_id=training_id)

    st.write("")
    render_section_title(
        "Detail Training Terpilih",
        "Evaluasi, visualisasi, tabel prediksi, dan aksi publish model.",
    )

    if evaluation:
        render_metric_cards(
            {
                "MAE": evaluation.get("mae"),
                "RMSE": evaluation.get("rmse"),
                "MAPE": evaluation.get("mape"),
            }
        )

    tab_chart, tab_test, tab_future, tab_action = st.tabs(
        [
            "Grafik",
            "Prediksi Test",
            "Prediksi Masa Depan",
            "Aksi",
        ]
    )

    with tab_chart:
        st.plotly_chart(
            build_combined_prediction_chart(
                test_predictions=test_predictions,
                future_predictions=future_predictions,
            ),
            use_container_width=True,
            key=f"history_combined_chart_{training_id}",
        )

    with tab_test:
        render_prediction_table(
            df=test_predictions,
            title="Aktual vs Prediksi Data Test",
        )

        st.plotly_chart(
            build_test_prediction_chart(test_predictions),
            use_container_width=True,
            key=f"history_test_chart_{training_id}",
        )

        render_dataframe_download_button(
            df=test_predictions,
            filename=f"training_{training_id}_test_predictions.csv",
            label="Download Prediksi Test CSV",
        )

    with tab_future:
        render_prediction_table(
            df=future_predictions,
            title="Prediksi Masa Depan",
        )

        st.plotly_chart(
            build_future_prediction_chart(future_predictions),
            use_container_width=True,
            key=f"history_future_chart_{training_id}",
        )

        render_dataframe_download_button(
            df=future_predictions,
            filename=f"training_{training_id}_future_predictions.csv",
            label="Download Prediksi Masa Depan CSV",
        )

    with tab_action:
        st.info(
            "Gunakan tombol berikut untuk mempublish model dan hasil prediksi "
            "ke halaman user."
        )

        if st.button(
            "Publish Training Ini",
            use_container_width=True,
            key=f"publish_training_{training_id}",
        ):
            try:
                publish_training_result(
                    training_id=training_id,
                    admin_id=get_current_admin_id(),
                )

                st.success("Hasil training berhasil dipublish ke user.")
                st.rerun()

            except Exception as exc:
                logger.exception("Gagal publish hasil training.")
                st.error(f"Gagal publish hasil training: {exc}")