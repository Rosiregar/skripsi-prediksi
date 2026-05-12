from __future__ import annotations

from io import BytesIO

import streamlit as st

from src.auth.session_manager import get_current_admin_id, require_admin_login
from src.services.dataset_service import (
    get_dataset_rows_as_dataframe,
    list_datasets,
    publish_dataset,
    save_uploaded_dataset,
    set_active_dataset,
)
from src.utils.chart_builder import build_target_history_chart
from src.utils.file_validator import validate_and_read_dataset
from src.utils.formatting import format_datetime
from src.utils.ui_components import (
    render_admin_page_header,
    render_dataframe,
    render_dataset_summary,
    render_empty_state,
    render_errors,
    render_info_card,
    render_page_header,
    render_section_title,
    render_step_indicator,
    render_warnings,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

@st.cache_data(show_spinner=False)
def load_and_validate_uploaded_file(file_bytes: bytes, filename: str):
    file_buffer = BytesIO(file_bytes)
    file_buffer.name = filename

    return validate_and_read_dataset(
        file_obj=file_buffer,
        filename=filename,
    )


def render_admin_dataset_page() -> None:
    """
    Render halaman Kelola Dataset Admin.
    """

    if not require_admin_login():
        return

    render_admin_page_header(
        title="Kelola Dataset",
        subtitle=(
            "Upload, validasi, aktifkan, dan publish dataset yang digunakan "
            "dalam proses training model LSTM."
        ),
    )

    render_dataset_steps()

    tab_upload, tab_list = st.tabs(["Upload Dataset", "Daftar Dataset"])

    with tab_upload:
        render_upload_dataset_tab()

    with tab_list:
        render_dataset_list_tab()


def render_dataset_steps() -> None:
    """
    Menampilkan alur pengelolaan dataset.
    """

    render_step_indicator(
        [
            ("Upload", "Masukkan file Excel atau CSV."),
            ("Validasi", "Periksa format dan isi dataset."),
            ("Aktifkan", "Pilih dataset untuk training."),
            ("Publish", "Tampilkan dataset ke user."),
        ]
    )


def render_upload_dataset_tab() -> None:
    """
    Menampilkan tab upload dataset.
    """

    render_section_title(
        "Upload Dataset",
        "Dataset minimal harus memiliki kolom Tahun dan Total_Pengangguran.",
    )

    render_dataset_format_info()

    uploaded_file = st.file_uploader(
        "Pilih file dataset",
        type=["xlsx", "xls", "csv"],
        help="Format file yang didukung: Excel dan CSV.",
    )

    dataset_name = st.text_input(
        "Nama Dataset",
        placeholder="Contoh: Dataset Pengangguran Sulawesi Utara",
    )

    col_active, col_publish = st.columns(2)

    with col_active:
        make_active = st.checkbox(
            "Jadikan dataset aktif",
            value=True,
            help="Dataset aktif akan dipakai untuk training model.",
        )

    with col_publish:
        publish = st.checkbox(
            "Publish dataset ke user",
            value=True,
            help="Dataset published akan tampil di halaman Dataset user.",
        )

    if uploaded_file is None:
        st.info("Silakan upload dataset terlebih dahulu.")
        return

    file_bytes = uploaded_file.getvalue()

    with st.spinner("Membaca dan memvalidasi dataset..."):
        validation_result = load_and_validate_uploaded_file(
            file_bytes=file_bytes,
            filename=uploaded_file.name,
        )

    render_validation_result(validation_result)

    if not validation_result.is_valid or validation_result.dataframe is None:
        return

    render_preview_dataset(validation_result.dataframe)

    st.write("")

    if st.button("Simpan Dataset", use_container_width=True):
        save_dataset_action(
            uploaded_file=uploaded_file,
            dataset_name=dataset_name,
            make_active=make_active,
            publish=publish,
        )


def render_dataset_format_info() -> None:
    """
    Menampilkan format dataset dalam expander agar halaman tidak terlalu penuh.
    """

    with st.expander("Panduan Format Dataset"):
        st.markdown(
            """
            Dataset minimal harus memiliki kolom berikut:

            ```text
            Tahun
            Total_Pengangguran
            ```

            Contoh:

            ```text
            Tahun | Total_Pengangguran | Jumlah_Penduduk | TPAK | PDRB
            2018  | 70000              | 2600000         | 62.1 | 12345
            2019  | 72000              | 2630000         | 62.4 | 12500
            2020  | 76000              | 2650000         | 61.8 | 12400
            ```

            Catatan:
            - Kolom `Tahun` boleh berupa angka tahun atau tanggal.
            - Kolom selain `Tahun` harus berisi angka.
            - Kolom `Total_Pengangguran` tidak boleh bernilai 0 atau negatif.
            """
        )


def render_validation_result(validation_result) -> None:
    """
    Menampilkan hasil validasi dataset.
    """

    render_section_title(
        "Validasi Dataset",
        "Sistem memeriksa format, kolom wajib, dan isi dataset.",
    )

    if validation_result.is_valid:
        st.success("Dataset valid dan siap disimpan.")
    else:
        st.error("Dataset belum valid.")
        render_errors(validation_result.errors)

    render_warnings(validation_result.warnings)

    if validation_result.summary:
        render_section_title(
            "Ringkasan Dataset",
            "Informasi dasar dataset yang berhasil dibaca.",
        )
        render_dataset_summary(validation_result.summary)


def render_preview_dataset(df) -> None:
    """
    Menampilkan preview dataset sebelum disimpan.
    """

    render_section_title(
        "Preview Dataset",
        "Untuk menjaga performa, tabel preview hanya menampilkan sebagian data.",
    )

    preview_df = df.head(50)

    render_dataframe(
        df=preview_df,
        empty_message="Preview dataset tidak tersedia.",
        height=320,
    )

    if len(df) > 50:
        st.caption(
            f"Dataset memiliki {len(df)} baris. "
            "Preview hanya menampilkan 50 baris pertama."
        )

    with st.expander("Lihat Grafik Total Pengangguran"):
        st.plotly_chart(
            build_target_history_chart(df),
            use_container_width=True,
            key="admin_upload_preview_target_chart",
        )


def save_dataset_action(
    uploaded_file,
    dataset_name: str,
    make_active: bool,
    publish: bool,
) -> None:
    """
    Menyimpan dataset yang sudah divalidasi.
    """

    admin_id = get_current_admin_id()

    try:
        with st.spinner("Menyimpan dataset ke sistem..."):
            result = save_uploaded_dataset(
                file_obj=uploaded_file,
                filename=uploaded_file.name,
                dataset_name=dataset_name.strip() or None,
                uploaded_by=admin_id,
                make_active=make_active,
                publish=publish,
            )

        dataset = result["dataset"]

        st.success(f"Dataset '{dataset['dataset_name']}' berhasil disimpan.")

        if make_active:
            st.info("Dataset ini sudah dijadikan dataset aktif.")

        if publish:
            st.info("Dataset ini sudah dipublish ke halaman user.")

        render_warnings(result.get("warnings", []))

        st.cache_data.clear()

    except Exception as exc:
        logger.exception("Gagal menyimpan dataset.")
        st.error(f"Gagal menyimpan dataset: {exc}")


def render_dataset_list_tab() -> None:
    """
    Menampilkan tab daftar dataset.
    """

    render_section_title(
        "Daftar Dataset",
        "Dataset yang sudah pernah diupload oleh admin.",
    )

    datasets = list_datasets(limit=100)

    if not datasets:
        render_empty_state(
            title="Belum Ada Dataset",
            text="Belum ada dataset yang diupload oleh admin.",
        )
        return

    table_data = []

    for dataset in datasets:
        table_data.append(
            {
                "ID": dataset.get("id"),
                "Nama Dataset": dataset.get("dataset_name"),
                "File": dataset.get("original_filename"),
                "Baris": dataset.get("row_count"),
                "Kolom": dataset.get("column_count"),
                "Periode": (
                    f"{dataset.get('start_year', '-')}"
                    f"-{dataset.get('end_year', '-')}"
                ),
                "Aktif": "Ya" if dataset.get("is_active") else "Tidak",
                "Published": "Ya" if dataset.get("is_published") else "Tidak",
                "Upload": format_datetime(dataset.get("uploaded_at")),
            }
        )

    st.dataframe(
        table_data,
        use_container_width=True,
    )

    dataset_options = {
        f"ID {dataset['id']} - {dataset['dataset_name']}": dataset["id"]
        for dataset in datasets
    }

    selected_label = st.selectbox(
        "Pilih dataset",
        options=list(dataset_options.keys()),
    )

    selected_dataset_id = dataset_options[selected_label]

    render_selected_dataset_summary(datasets, selected_dataset_id)
    render_dataset_action_area(selected_dataset_id)


def render_selected_dataset_summary(
    datasets: list[dict],
    selected_dataset_id: int,
) -> None:
    """
    Menampilkan ringkasan dataset yang dipilih.
    """

    selected_dataset = next(
        (
            dataset
            for dataset in datasets
            if dataset.get("id") == selected_dataset_id
        ),
        None,
    )

    if not selected_dataset:
        return

    st.write("")
    render_section_title(
        "Dataset Terpilih",
        "Informasi singkat dataset yang dipilih.",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_info_card(
            "Nama Dataset",
            str(selected_dataset.get("dataset_name", "-")),
        )

    with col2:
        render_info_card(
            "Aktif",
            "Ya" if selected_dataset.get("is_active") else "Tidak",
        )

    with col3:
        render_info_card(
            "Published",
            "Ya" if selected_dataset.get("is_published") else "Tidak",
        )

    with col4:
        render_info_card(
            "Periode",
            (
                f"{selected_dataset.get('start_year', '-')}"
                f"-{selected_dataset.get('end_year', '-')}"
            ),
        )


def render_dataset_action_area(dataset_id: int) -> None:
    """
    Menampilkan tombol aksi dataset.
    """

    st.write("")
    render_section_title(
        "Aksi Dataset",
        "Gunakan aksi berikut untuk mengelola dataset terpilih.",
    )

    col_active, col_publish, col_preview = st.columns(3)

    with col_active:
        if st.button("Jadikan Aktif", use_container_width=True):
            activate_dataset_action(dataset_id)

    with col_publish:
        if st.button("Publish ke User", use_container_width=True):
            publish_dataset_action(dataset_id)

    with col_preview:
        show_preview = st.button("Lihat Preview", use_container_width=True)

    if show_preview:
        render_dataset_preview_by_id(dataset_id)


def activate_dataset_action(dataset_id: int) -> None:
    """
    Mengaktifkan dataset.
    """

    try:
        dataset = set_active_dataset(
            dataset_id=dataset_id,
            admin_id=get_current_admin_id(),
        )

        st.success(f"Dataset '{dataset['dataset_name']}' berhasil dijadikan aktif.")
        st.rerun()

    except Exception as exc:
        logger.exception("Gagal mengaktifkan dataset.")
        st.error(f"Gagal mengaktifkan dataset: {exc}")


def publish_dataset_action(dataset_id: int) -> None:
    """
    Publish dataset ke halaman user.
    """

    try:
        dataset = publish_dataset(
            dataset_id=dataset_id,
            admin_id=get_current_admin_id(),
        )

        st.success(f"Dataset '{dataset['dataset_name']}' berhasil dipublish.")
        st.rerun()

    except Exception as exc:
        logger.exception("Gagal publish dataset.")
        st.error(f"Gagal publish dataset: {exc}")


def render_dataset_preview_by_id(dataset_id: int) -> None:
    """
    Menampilkan preview dataset berdasarkan ID.
    """

    try:
        with st.spinner("Memuat preview dataset..."):
            df = get_dataset_rows_as_dataframe(dataset_id)

        render_section_title(
            "Preview Dataset Terpilih",
            "Preview tabel dan grafik dari dataset yang dipilih.",
        )

        preview_df = df.head(50)

        render_dataframe(
            df=preview_df,
            empty_message="Isi dataset tidak tersedia.",
            height=360,
        )

        if len(df) > 50:
            st.caption(
                f"Dataset memiliki {len(df)} baris. "
                "Preview hanya menampilkan 50 baris pertama."
            )

        with st.expander("Lihat Grafik Total Pengangguran"):
            st.plotly_chart(
                build_target_history_chart(df),
                use_container_width=True,
                key=f"admin_dataset_preview_chart_{dataset_id}",
            )

    except Exception as exc:
        logger.exception("Gagal menampilkan preview dataset.")
        st.error(f"Gagal menampilkan preview dataset: {exc}")