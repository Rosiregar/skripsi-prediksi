from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from src.utils.formatting import (
    format_datetime,
    format_metric_value,
    format_prediction_dataframe,
    format_status,
)


# ============================================================
# PAGE HEADER
# ============================================================

def render_page_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: str = "",
    badge: str = "Halaman",
) -> None:
    """
    Header halaman publik tanpa badge kecil.
    """

    icon_text = f"{icon} " if icon else ""

    st.markdown(
        f"""
        <div class="page-head">
            <h1>{icon_text}{title}</h1>
            <p>{subtitle or ""}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_admin_page_header(
    title: str,
    subtitle: Optional[str] = None,
) -> None:
    """
    Header halaman admin tanpa badge kecil.
    """

    st.markdown(
        f"""
        <div class="page-head admin">
            <h1>{title}</h1>
            <p>{subtitle or ""}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(
    title: str,
    subtitle: Optional[str] = None,
) -> None:
    """
    Judul section.
    Dibuat sederhana agar tidak memunculkan HTML mentah.
    """

    st.markdown(f"### {title}")

    if subtitle:
        st.caption(subtitle)


# ============================================================
# CARD
# ============================================================

def render_info_card(title: str, text: str) -> None:
    """
    Card informasi.
    """

    st.markdown(
        f"""
        <div class="card">
            <h3>{title}</h3>
            <p>{text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_card(title: str, text: str) -> None:
    """
    Alias untuk card informasi.
    """

    render_info_card(title, text)


def render_detail_panel(
    title: str,
    body: str,
    label: str = "",
) -> None:
    """
    Panel detail.
    """

    paragraphs = "".join(
        f"<p>{paragraph.strip()}</p>"
        for paragraph in body.split("\n")
        if paragraph.strip()
    )

    label_html = ""

    if label:
        label_html = f'<div class="hero-label">{label}</div>'

    st.markdown(
        f"""
        <div class="hero">
            {label_html}
            <h1>{title}</h1>
            {paragraphs}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, text: str) -> None:
    """
    Empty state sederhana.
    """

    st.info(f"**{title}**\n\n{text}")


# ============================================================
# METRIC
# ============================================================

def render_metric_cards(metrics: dict) -> None:
    """
    Menampilkan MAE, RMSE, dan MAPE.

    Sengaja memakai st.metric agar aman dan tidak memunculkan HTML mentah.
    """

    if not metrics:
        st.info("Metrik evaluasi belum tersedia.")
        return

    metric_order = ["MAE", "RMSE", "MAPE"]
    columns = st.columns(3)

    for index, metric_name in enumerate(metric_order):
        value = metrics.get(metric_name)

        with columns[index]:
            st.metric(
                label=metric_name,
                value=format_metric_value(metric_name, value),
            )


def render_dataset_summary(summary: dict) -> None:
    """
    Ringkasan dataset.
    """

    if not summary:
        st.info("Ringkasan dataset belum tersedia.")
        return

    columns = st.columns(4)

    with columns[0]:
        st.metric("Jumlah Baris", summary.get("row_count", 0))

    with columns[1]:
        st.metric("Jumlah Kolom", summary.get("column_count", 0))

    with columns[2]:
        st.metric("Tahun Awal", summary.get("start_year", "-"))

    with columns[3]:
        st.metric("Tahun Akhir", summary.get("end_year", "-"))


def render_training_summary(
    training: dict,
    evaluation: Optional[dict] = None,
) -> None:
    """
    Ringkasan hasil training.
    """

    if not training:
        st.info("Data training belum tersedia.")
        return

    columns = st.columns(4)

    with columns[0]:
        st.metric("Status", format_status(training.get("status")))

    with columns[1]:
        st.metric("Window Size", training.get("window_size", "-"))

    with columns[2]:
        st.metric("Epochs", training.get("epochs", "-"))

    with columns[3]:
        is_published = training.get("is_published", False)
        st.metric("Publish", "Ya" if is_published else "Tidak")

    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        render_info_card(
            "Versi Model",
            str(training.get("model_version", "-")),
        )

    with col2:
        render_info_card(
            "Mulai Training",
            format_datetime(training.get("started_at")),
        )

    with col3:
        render_info_card(
            "Selesai Training",
            format_datetime(training.get("finished_at")),
        )

    if evaluation:
        st.write("")
        render_section_title(
            "Evaluasi Model",
            "Nilai evaluasi model berdasarkan data test historis.",
        )

        render_metric_cards(
            {
                "MAE": evaluation.get("mae"),
                "RMSE": evaluation.get("rmse"),
                "MAPE": evaluation.get("mape"),
            }
        )


# ============================================================
# BADGE
# ============================================================

def render_status_badge(label: str, variant: str = "info") -> None:
    """
    Badge status.
    """

    st.markdown(
        f"""
        <span class="status-badge {variant}">
            {label}
        </span>
        """,
        unsafe_allow_html=True,
    )


def render_feature_badges(features: list[str]) -> None:
    """
    Fitur terpilih dalam bentuk badge.
    """

    if not features:
        st.warning("Tidak ada fitur tambahan yang memenuhi nilai korelasi minimum.")
        return

    badges = "".join(
        f'<span class="feature-badge">{feature}</span>'
        for feature in features
    )

    st.markdown(
        f"""
        <div class="feature-badge-wrap">
            {badges}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_selected_features(features: list[str]) -> None:
    """
    Menampilkan fitur terpilih.
    """

    render_section_title(
        "Fitur Terpilih",
        "Fitur dipilih berdasarkan korelasi terhadap Total_Pengangguran.",
    )

    render_feature_badges(features)


# ============================================================
# STEP INDICATOR
# ============================================================

def render_step_indicator(steps: list[tuple[str, str]]) -> None:
    """
    Step indicator untuk alur halaman.
    """

    cards = ""

    for index, step in enumerate(steps, start=1):
        title = step[0]
        description = step[1] if len(step) > 1 else ""

        cards += f"""
        <div class="step-card">
            <div class="step-number">{index}</div>
            <div class="step-title">{title}</div>
            <div class="step-desc">{description}</div>
        </div>
        """

    st.markdown(
        f"""
        <div class="step-wrap">
            {cards}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DATAFRAME
# ============================================================

def render_dataframe(
    df: pd.DataFrame,
    title: Optional[str] = None,
    empty_message: str = "Data belum tersedia.",
    height: Optional[int] = None,
) -> None:
    """
    Menampilkan dataframe.
    """

    if title:
        render_section_title(title)

    if df is None or df.empty:
        st.info(empty_message)
        return

    if height is None:
        st.dataframe(
            df,
            use_container_width=True,
        )
    else:
        st.dataframe(
            df,
            use_container_width=True,
            height=height,
        )


def render_prediction_table(
    df: pd.DataFrame,
    title: str = "Tabel Hasil Prediksi",
) -> None:
    """
    Menampilkan tabel prediksi.
    """

    if df is None or df.empty:
        st.info("Data prediksi belum tersedia.")
        return

    formatted_df = format_prediction_dataframe(df)

    render_dataframe(
        formatted_df,
        title=title,
        empty_message="Data prediksi belum tersedia.",
    )


def render_table_card(
    title: str,
    subtitle: str,
    df: pd.DataFrame,
    empty_message: str = "Data belum tersedia.",
    height: Optional[int] = None,
) -> None:
    """
    Menampilkan tabel dengan judul section.
    """

    render_section_title(title, subtitle)

    render_dataframe(
        df=df,
        empty_message=empty_message,
        height=height,
    )


# ============================================================
# CHART
# ============================================================

def render_chart_title(title: str, subtitle: str = "") -> None:
    """
    Judul area grafik.
    """

    render_info_card(title, subtitle)


# ============================================================
# EVALUATION EXPLANATION
# ============================================================

def render_evaluation_explanation() -> None:
    """
    Penjelasan MAE, RMSE, dan MAPE.
    """

    with st.expander("Penjelasan MAE, RMSE, dan MAPE"):
        st.markdown(
            """
            **MAE (Mean Absolute Error)** menunjukkan rata-rata selisih absolut
            antara nilai aktual dan nilai prediksi.

            **RMSE (Root Mean Squared Error)** menunjukkan akar dari rata-rata
            kuadrat error. Nilai RMSE lebih sensitif terhadap error besar.

            **MAPE (Mean Absolute Percentage Error)** menunjukkan rata-rata
            persentase kesalahan prediksi terhadap nilai aktual.

            Semakin kecil nilai MAE, RMSE, dan MAPE, semakin baik performa model.
            """
        )


# ============================================================
# ALERT HELPERS
# ============================================================

def render_errors(errors: list[str]) -> None:
    """
    Menampilkan daftar error.
    """

    if not errors:
        return

    for error in errors:
        st.error(error)


def render_warnings(warnings: list[str]) -> None:
    """
    Menampilkan daftar warning.
    """

    if not warnings:
        return

    for warning in warnings:
        st.warning(warning)


def render_success_message(message: str) -> None:
    st.success(message)


def render_info_message(message: str) -> None:
    st.info(message)


# ============================================================
# DOWNLOAD
# ============================================================

def render_dataframe_download_button(
    df: pd.DataFrame,
    filename: str,
    label: str = "Download CSV",
) -> None:
    """
    Download dataframe sebagai CSV.
    """

    if df is None or df.empty:
        return

    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# FOOTER
# ============================================================

def render_footer() -> None:
    """
    Footer aplikasi.
    """

    st.markdown(
        """
        <div class="footer-note">
            Aplikasi Prediksi Jumlah Pengangguran di Sulawesi Utara
            menggunakan algoritma Long Short-Term Memory (LSTM).
        </div>
        """,
        unsafe_allow_html=True,
    )