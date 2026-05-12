"""
Halaman Dataset User.

File ini bertanggung jawab untuk:
- menampilkan dataset yang dipublish admin,
- menampilkan ringkasan dataset,
- menampilkan tabel dataset,
- menampilkan grafik historis Total_Pengangguran,
- menampilkan grafik seluruh variabel,
- menyediakan tombol download dataset.

Catatan:
- File ini hanya mengubah tampilan.
- Fungsi dataset service tidak diubah.
"""

from __future__ import annotations

import streamlit as st

from src.services.dataset_service import (
    get_dataset_rows_as_dataframe,
    get_published_dataset,
)
from src.utils.chart_builder import (
    build_all_variables_chart,
    build_target_history_chart,
)
from src.utils.ui_components import (
    render_dataframe,
    render_dataframe_download_button,
    render_dataset_summary,
    render_empty_state,
    render_info_card,
    render_page_header,
    render_section_title,
)


def render_user_dataset_page() -> None:
    """
    Render halaman dataset untuk user.
    """

    render_page_header(
        title="Dataset",
        subtitle=(
            "Dataset resmi yang dipublish oleh admin dan digunakan "
            "sebagai dasar analisis serta prediksi jumlah pengangguran."
        ),
        icon="",
        badge="Publik",
    )

    render_dataset_guidance()

    published_dataset = get_published_dataset()

    if not published_dataset:
        render_empty_dataset_state()
        return

    render_dataset_information(published_dataset)

    df = get_dataset_rows_as_dataframe(published_dataset["id"])

    if df.empty:
        st.warning("Dataset ditemukan, tetapi isi dataset masih kosong.")
        return

    render_dataset_summary_section(published_dataset, df)
    render_dataset_chart_section(df)
    render_dataset_table_section(df)


def render_dataset_guidance() -> None:
    """
    Menampilkan panduan dataset dalam expander agar halaman tetap bersih.
    """

    with st.expander("Penjelasan Dataset"):
        st.markdown(
            """
            Dataset pada halaman ini merupakan dataset yang telah dipublish
            oleh admin. Dataset ini digunakan sebagai dasar analisis dan
            proses prediksi jumlah pengangguran.

            Dataset minimal memiliki kolom **Tahun** dan
            **Total_Pengangguran**. Kolom tambahan seperti jumlah penduduk,
            TPAK, PDRB, inflasi, atau indikator numerik lainnya dapat digunakan
            sebagai fitur pendukung dalam proses pemodelan.
            """
        )

    with st.expander("Struktur Minimal Dataset"):
        st.markdown(
            """
            Dataset minimal harus memiliki kolom:

            ```text
            Tahun
            Total_Pengangguran
            ```

            Contoh struktur dataset:

            ```text
            Tahun | Total_Pengangguran | Jumlah_Penduduk | TPAK | PDRB | Inflasi
            2018  | 70000              | 2600000         | 62.1 | 12345| 2.8
            2019  | 72000              | 2630000         | 62.4 | 12500| 3.1
            ```
            """
        )


def render_empty_dataset_state() -> None:
    """
    Tampilan jika belum ada dataset yang dipublish.
    """

    render_empty_state(
        title="Belum Ada Dataset yang Dipublish",
        text=(
            "Belum ada dataset yang dipublish oleh admin. "
            "Silakan login sebagai admin, upload dataset, lalu publish dataset."
        ),
    )

    with st.expander("Alur agar dataset tampil di halaman ini"):
        st.markdown(
            """
            Agar dataset tampil di halaman publik, admin perlu melakukan:

            ```text
            Login Admin
            ↓
            Upload Dataset
            ↓
            Validasi Dataset
            ↓
            Aktifkan Dataset
            ↓
            Publish Dataset
            ```
            """
        )


def render_dataset_information(dataset: dict) -> None:
    """
    Menampilkan informasi metadata dataset.
    """

    render_section_title(
        "Informasi Dataset",
        "Metadata dataset yang sedang dipublish.",
    )

    columns = st.columns(4)

    with columns[0]:
        render_info_card(
            "Nama Dataset",
            str(dataset.get("dataset_name", "-")),
        )

    with columns[1]:
        render_info_card(
            "Jumlah Baris",
            str(dataset.get("row_count", 0)),
        )

    with columns[2]:
        render_info_card(
            "Tahun Awal",
            str(dataset.get("start_year", "-")),
        )

    with columns[3]:
        render_info_card(
            "Tahun Akhir",
            str(dataset.get("end_year", "-")),
        )

    st.write("")

    col_file, col_status = st.columns(2)

    with col_file:
        render_info_card(
            "File Asli",
            str(dataset.get("original_filename", "-")),
        )

    with col_status:
        render_info_card(
            "Status",
            "Dataset Dipublish",
        )


def render_dataset_summary_section(dataset: dict, df) -> None:
    """
    Menampilkan ringkasan dataset.
    """

    summary = {
        "row_count": dataset.get("row_count", len(df)),
        "column_count": dataset.get("column_count", len(df.columns)),
        "start_year": dataset.get("start_year"),
        "end_year": dataset.get("end_year"),
    }

    render_section_title(
        "Ringkasan Dataset",
        "Informasi jumlah data, jumlah kolom, dan rentang tahun.",
    )

    render_dataset_summary(summary)


def render_dataset_chart_section(df) -> None:
    """
    Menampilkan grafik dataset.
    """

    render_section_title(
        "Visualisasi Dataset",
        "Grafik historis jumlah pengangguran dan variabel pendukung.",
    )

    tab_target, tab_all_variables = st.tabs(
        [
            "Total Pengangguran",
            "Semua Variabel",
        ]
    )

    with tab_target:
        st.plotly_chart(
            build_target_history_chart(df),
            use_container_width=True,
            key="published_dataset_target_chart",
        )

    with tab_all_variables:
        st.plotly_chart(
            build_all_variables_chart(df),
            use_container_width=True,
            key="published_dataset_all_variables_chart",
        )


def render_dataset_table_section(df) -> None:
    """
    Menampilkan tabel dataset dan tombol download.
    """

    render_section_title(
        "Tabel Dataset",
        "Data historis yang digunakan sebagai dasar prediksi.",
    )

    render_dataframe(
        df=df,
        empty_message="Dataset belum tersedia.",
        height=420,
    )

    render_dataframe_download_button(
        df=df,
        filename="dataset_pengangguran_sulawesi_utara.csv",
        label="Download Dataset CSV",
    )